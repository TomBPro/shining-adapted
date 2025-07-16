import pygame
import time
import threading
import queue
import sys

pygame.mixer.init()

class SoundEvent:
    def __init__(self, timestamp, path, volume, panoramique, character_id=None):
        self.timestamp = timestamp
        self.path = path
        self.volume = volume
        self.panoramique = panoramique
        self.character_id = character_id

class AudioPlayer(threading.Thread):
    # Thread dédié à la lecture des sons, gérant la musique d'ambiance, les effets sonores par personnage
    # et un système de fondu (ducking) pour l'ambiance
    def __init__(self, audio_queue):
        super().__init__()
        self.audio_queue = audio_queue
        self.running = True
        self.daemon = True
        
        self.ambient_channel = pygame.mixer.Channel(0) # Canal dédié à la musique de fond.
        
        # Canaux dédiés aux bruits de pas de chaque personnage pour éviter les coupures entre eux.
        self.character_footstep_channels = {
            'son': pygame.mixer.Channel(1),
            'father': pygame.mixer.Channel(2),
        }
        # Définit le nombre total de canaux Pygame pour inclure les canaux dédiés et un pool général
        pygame.mixer.set_num_channels(5) 
        # Pool de canaux pour les effets sonores généraux (victoire, fin de partie), utilisant le "voice stealing"
        self.general_fx_channels = [pygame.mixer.Channel(i) for i in range(3, pygame.mixer.get_num_channels())]
        self.next_general_fx_channel_index = 0

        self.original_ambient_volume = 0.0
        self.duck_level = 0.7 # Niveau de réduction du volume de l'ambiance pendant le ducking
        
        self._last_fx_played_time = 0.0
        self._fx_hold_time = 0.25 # Durée pendant laquelle l'ambiance reste atténuée après un FX
        self._fade_duration = 0.2 # Durée du fondu d'entrée/sortie du ducking

    def start_ambient(self, path, volume):
        try:
            ambient_sound = pygame.mixer.Sound(path)
            self.original_ambient_volume = volume
            self.ambient_channel.set_volume(self.original_ambient_volume)
            self.ambient_channel.play(ambient_sound, loops=-1)
        except pygame.error:
            pass

    def stop_ambient(self):
        self.ambient_channel.stop()

    def is_ambient_playing(self):
        return self.ambient_channel.get_busy()

    def run(self):
        self.sequence_start_time_ns = time.perf_counter_ns()
        last_volume_update_time = time.perf_counter()

        while self.running:
            current_real_time = time.perf_counter()
            delta_time = current_real_time - last_volume_update_time
            last_volume_update_time = current_real_time

            # Détermine si un effet sonore est actif pour déclencher le ducking de l'ambiance.
            fx_channel_busy = False
            for channel in self.character_footstep_channels.values():
                if channel.get_busy():
                    fx_channel_busy = True
                    break
            if not fx_channel_busy:
                for channel in self.general_fx_channels:
                    if channel.get_busy():
                        fx_channel_busy = True
                        break

            # Ajuste le volume de la musique d'ambiance en fonction de l'activité des effets sonores
            target_ambient_volume = self.original_ambient_volume
            if fx_channel_busy or (current_real_time - self._last_fx_played_time < self._fx_hold_time):
                target_ambient_volume = self.original_ambient_volume * self.duck_level
            
            # Applique un fondu progressif au volume de l'ambiance
            current_ambient_volume = self.ambient_channel.get_volume()
            if abs(current_ambient_volume - target_ambient_volume) > 0.005:
                if self._fade_duration > 0:
                    volume_change_rate = (target_ambient_volume - current_ambient_volume) / self._fade_duration
                    new_volume = current_ambient_volume + volume_change_rate * delta_time
                    new_volume = max(min(new_volume, self.original_ambient_volume), self.original_ambient_volume * self.duck_level)
                    self.ambient_channel.set_volume(new_volume)
            else:
                self.ambient_channel.set_volume(target_ambient_volume)

            try:
                # Récupère un événement sonore de la file d'attente
                sound_event = self.audio_queue.get(timeout=0.001) 
                
                self._last_fx_played_time = current_real_time

                # Synchronise le temps de lecture du son avec le temps de jeu
                absolute_target_time_ns = self.sequence_start_time_ns + sound_event.timestamp * 1_000_000_000
                delta_time_ns_for_sleep = absolute_target_time_ns - time.perf_counter_ns()
                time_to_wait_s = max(0, delta_time_ns_for_sleep / 1_000_000_000)
                
                if time_to_wait_s > 0:
                    time.sleep(time_to_wait_s)

                try:
                    if isinstance(sound_event.path, pygame.mixer.Sound):
                        sound = sound_event.path
                    else:
                        sound = pygame.mixer.Sound(sound_event.path)
                except pygame.error:
                    continue
                
                sound.set_volume(sound_event.volume)
                
                # Selection auto canal
                channel_to_play = None
                if sound_event.character_id and sound_event.character_id in self.character_footstep_channels:
                    channel_to_play = self.character_footstep_channels[sound_event.character_id]
                elif self.general_fx_channels:
                    channel_to_play = self.general_fx_channels[self.next_general_fx_channel_index]
                    self.next_general_fx_channel_index = (self.next_general_fx_channel_index + 1) % len(self.general_fx_channels)

                if channel_to_play:
                    channel = channel_to_play.play(sound) 
                    if channel:
                        # Applique l'effet panoramique pour la spatialisation du son
                        left_pan_vol = 1.0 - sound_event.panoramique
                        right_pan_vol = sound_event.panoramique
                        channel.set_volume(left_pan_vol * sound_event.volume, right_pan_vol * sound_event.volume)

            except queue.Empty:
                pass
            except Exception as e:
                self.running = False
        sys.exit()
