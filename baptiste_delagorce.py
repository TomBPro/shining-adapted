#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  7 10:45:42 2025

@author: smartaudiotools
"""

import pyxel
import numpy
import random
import time
import queue
import sys
import pygame
from audio_manager import SoundEvent, AudioPlayer

# Taille de tampon augmentée pour une meilleure stabilité audio
pygame.mixer.pre_init(44100, -16, 2, 4096)
pygame.mixer.init()

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
SPEED = 2

TILE_SIZE = 8
PATH_SIZE = TILE_SIZE * 2
LABYRINTH_WIDTH = SCREEN_WIDTH // PATH_SIZE
LABYRINTH_HEIGHT = SCREEN_HEIGHT // PATH_SIZE

if LABYRINTH_WIDTH % 4 != 3:
    LABYRINTH_WIDTH = LABYRINTH_WIDTH // 4 * 4 - 1
if LABYRINTH_HEIGHT % 4 != 3:
    LABYRINTH_HEIGHT = LABYRINTH_HEIGHT // 4 * 4 - 1

LABYRINTH_START_POSITION = (0, LABYRINTH_HEIGHT // 2)
LABYRINTH_END_POSITION = (LABYRINTH_WIDTH - 1, LABYRINTH_HEIGHT // 2)

RESOURCE_PATH = "labyrinth_resource.pyxres"

LABYRINTH_TO_MAP_SCALE = 2
MAP_WIDTH = LABYRINTH_WIDTH * LABYRINTH_TO_MAP_SCALE
MAP_HEIGHT = LABYRINTH_HEIGHT * LABYRINTH_TO_MAP_SCALE

LABYRINTH_TO_SCREEN_SCALE = 16

HORIZONTAL = 1
VERTICAL = 2
LEFT = 1
RIGHT = 2
UP = 3
DOWN = 4

class Character:
    def __init__(
        self,
        position,
        key_right,
        key_left,
        key_up,
        key_down,
        labyrinth,
        character_id,
        app_instance,
        direction=DOWN,
        image_index=1,
        transparent_color=0,
    ):
        self.x = position[0] * LABYRINTH_TO_SCREEN_SCALE
        self.y = position[1] * LABYRINTH_TO_SCREEN_SCALE
        self.direction = direction

        self.traces = []
        self.moving = False
        self.frame = 0
        self.exited = False

        self.key_right = key_right
        self.key_left = key_left
        self.key_up = key_up
        self.key_down = key_down
        self.labyrinth = labyrinth
        self.image = pyxel.images[image_index]
        self.transparent_color = transparent_color
        self.character_id = character_id 
        self.app_instance = app_instance 

        self.last_sound_position = (self.x // PATH_SIZE, self.y // PATH_SIZE)
        self.footstep_index = 0

    def update(self):
        if self.exited:
            return

        x = self.x
        y = self.y
        labyrinth_array = self.labyrinth.labyrinth_array
        labyrinth_map = self.labyrinth.map
        direction = None

        current_grid_x = x // PATH_SIZE
        current_grid_y = y // PATH_SIZE

        if (current_grid_x, current_grid_y) == LABYRINTH_END_POSITION:
            self.exited = True
            return

        if pyxel.btn(self.key_right):
            new_x = x + SPEED
            if current_grid_x == LABYRINTH_WIDTH - 1:
                new_x = min(new_x, (LABYRINTH_WIDTH - 1) * PATH_SIZE)
            else:
                next_col_idx = current_grid_x + 1
                if (labyrinth_array[next_col_idx, current_grid_y] or 
                    labyrinth_array[next_col_idx, (y + PATH_SIZE - 1) // PATH_SIZE]):
                    new_x = current_grid_x * PATH_SIZE
            if new_x != x:
                if new_x // PATH_SIZE != current_grid_x:
                    self.traces.append([current_grid_x, current_grid_y, HORIZONTAL])
                labyrinth_map.pset(x // TILE_SIZE + 1, y // TILE_SIZE + 1, (8, 1))
                labyrinth_map.pset(x // TILE_SIZE + 1, y // TILE_SIZE, (9, 1))
                x = new_x
                direction = RIGHT

        elif pyxel.btn(self.key_left):
            new_x = x - SPEED
            if new_x < 0:
                new_x = 0
            else:
                next_col_idx = new_x // PATH_SIZE
                if (labyrinth_array[next_col_idx, current_grid_y] or 
                    labyrinth_array[next_col_idx, (y + PATH_SIZE - 1) // PATH_SIZE]):
                    new_x = (next_col_idx + 1) * PATH_SIZE
            if new_x != x:
                if new_x // PATH_SIZE != current_grid_x:
                    self.traces.append([current_grid_x, current_grid_y, HORIZONTAL])
                labyrinth_map.pset(new_x // TILE_SIZE + 1, y // TILE_SIZE + 1, (8, 1))
                labyrinth_map.pset(new_x // TILE_SIZE + 1, y // TILE_SIZE, (9, 1))
                x = new_x
                direction = LEFT

        if pyxel.btn(self.key_down):
            new_y = y + SPEED
            if current_grid_y == LABYRINTH_HEIGHT - 1:
                new_y = min(new_y, (LABYRINTH_HEIGHT - 1) * PATH_SIZE)
            else:
                next_row_idx = current_grid_y + 1
                if (labyrinth_array[current_grid_x, next_row_idx] or 
                    labyrinth_array[(x + PATH_SIZE - 1) // PATH_SIZE, next_row_idx]):
                    new_y = current_grid_y * PATH_SIZE
            if y != new_y:
                if new_y // PATH_SIZE != current_grid_y:
                    self.traces.append([current_grid_x, current_grid_y, VERTICAL])
                labyrinth_map.pset(x // TILE_SIZE + 1, y // TILE_SIZE + 1, (9, 0))
                labyrinth_map.pset(x // TILE_SIZE, y // TILE_SIZE + 1, (8, 0))
                y = new_y
                direction = DOWN

        elif pyxel.btn(self.key_up):
            new_y = y - SPEED
            if new_y < 0:
                new_y = 0
            else:
                next_row_idx = new_y // PATH_SIZE
                if (labyrinth_array[current_grid_x, next_row_idx] or 
                    labyrinth_array[(x + PATH_SIZE - 1) // PATH_SIZE, next_row_idx]):
                    new_y = (next_row_idx + 1) * PATH_SIZE
            if y != new_y:
                if new_y // PATH_SIZE != current_grid_y:
                    self.traces.append([current_grid_x, current_grid_y, VERTICAL])
                labyrinth_map.pset(x // TILE_SIZE + 1, new_y // TILE_SIZE + 1, (9, 0))
                labyrinth_map.pset(x // TILE_SIZE, new_y // TILE_SIZE + 1, (8, 0))
                y = new_y
                direction = UP

        self.x = x
        self.y = y

        if direction is None:
            self.moving = False
        else:
            self.moving = True
            self.direction = direction
            
            current_grid_pos = (self.x // PATH_SIZE, self.y // PATH_SIZE)
            if current_grid_pos != self.last_sound_position:
                self.play_footstep_sound()
                self.last_sound_position = current_grid_pos

    def play_footstep_sound(self):
        current_game_time = (time.perf_counter_ns() - self.app_instance.game_start_time_ns) / 1_000_000_000
        
        footstep_sound_object = self.app_instance.preloaded_footsteps[self.footstep_index % len(self.app_instance.preloaded_footsteps)]
        
        panoramique = self.x / SCREEN_WIDTH
        
        sound_event = SoundEvent(current_game_time, footstep_sound_object, 0.08, panoramique, character_id=self.character_id) 
        self.app_instance.audio_queue.put(sound_event)
        self.footstep_index += 1

    def draw(self):
        if self.exited:
            return

        if self.moving:
            self.frame = (self.frame + 1) % 4
        else:
            self.frame = 1

        if self.direction == UP:
            pyxel.blt(
                self.x + self.labyrinth.offset_x,
                self.y - 2 + self.labyrinth.offset_y,
                self.image,
                16 * self.frame,
                0,
                16,
                16,
                self.transparent_color,
            )
        elif self.direction == DOWN:
            pyxel.blt(
                self.x + self.labyrinth.offset_x,
                self.y - 2 + self.labyrinth.offset_y,
                self.image,
                16 * self.frame,
                16,
                16,
                16,
                self.transparent_color,
            )
        elif self.direction == RIGHT:
            pyxel.blt(
                self.x + self.labyrinth.offset_x,
                self.y - 2 + self.labyrinth.offset_y,
                self.image,
                16 * self.frame,
                32,
                16,
                16,
                self.transparent_color,
            )
        elif self.direction == LEFT:
            pyxel.blt(
                self.x + self.labyrinth.offset_x,
                self.y - 2 + self.labyrinth.offset_y,
                self.image,
                16 * self.frame,
                48,
                16,
                16,
                self.transparent_color,
            )
        else:
            pyxel.blt(
                self.x + self.labyrinth.offset_x,
                self.y - 2 + self.labyrinth.offset_y,
                self.image,
                16 * self.frame,
                16,
                16,
                16,
                self.transparent_color,
            )


class Labyrinth:
    def __init__(self, width, height):
        self.offset_x = (SCREEN_WIDTH - LABYRINTH_WIDTH * PATH_SIZE) // 2
        self.offset_y = (SCREEN_HEIGHT - LABYRINTH_HEIGHT * PATH_SIZE) // 2
        self.generate_array(width, height)
        self.draw_map()

    def generate_array(self, width, height):
        self.labyrinth_array = labyrinth_array = numpy.ones((width, height), dtype=bool)

        labyrinth_array[LABYRINTH_START_POSITION[0], LABYRINTH_START_POSITION[1]] = (
            False
        )

        def carve(x, y):
            labyrinth_array[x, y] = False
            dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                jump_x, jump_y = x + dx * 2, y + dy * 2

                if (
                    0 < jump_x < LABYRINTH_WIDTH - 1
                    and 0 < jump_y < LABYRINTH_HEIGHT - 1
                    and labyrinth_array[jump_x][jump_y]
                ):
                    labyrinth_array[x + dx, y + dy] = False
                    carve(jump_x, jump_y)

        carve(LABYRINTH_START_POSITION[0] + 1, LABYRINTH_START_POSITION[1])
        labyrinth_array[LABYRINTH_END_POSITION[0], LABYRINTH_END_POSITION[1]] = False

    def draw_map(self):
        self.map = pyxel.Tilemap(MAP_WIDTH, MAP_HEIGHT, pyxel.images[0])
        labyrinth_array = self.labyrinth_array
        for x in range(MAP_WIDTH):
            for y in range(MAP_HEIGHT):
                labyrinth_x = x // 2
                labyrinth_y = y // 2

                if labyrinth_array[labyrinth_x, labyrinth_y]:

                    up_y = (y - 1) // 2
                    down_y = (y + 1) // 2
                    left_x = (x - 1) // 2
                    right_x = (x + 1) // 2

                    if up_y >= 0:
                        labyrinth_up = bool(labyrinth_array[labyrinth_x, up_y])
                    else:
                        labyrinth_up = False
                    if down_y < LABYRINTH_HEIGHT:
                        labyrinth_down = bool(labyrinth_array[labyrinth_x, down_y])
                    else:
                        labyrinth_down = False

                    if left_x >= 0:
                        labyrinth_left = bool(labyrinth_array[left_x, labyrinth_y])
                    else:
                        labyrinth_left = False

                    if right_x < LABYRINTH_WIDTH:
                        labyrinth_right = bool(labyrinth_array[right_x, labyrinth_y])
                    else:
                        labyrinth_right = False

                    match labyrinth_up, labyrinth_left, labyrinth_down, labyrinth_right:

                        case (False, False, False, False):
                            pass
                            self.map.pset(x, y, (3, 0))

                        case (False, False, False, True):
                            self.map.pset(x, y, (3, 0))

                        case (False, False, True, False):
                            self.map.pset(x, y, (3, 0))

                        case (False, False, True, True):
                            self.map.pset(x, y, (2, 0))

                        case (False, True, False, False):
                            self.map.pset(x, y, (3, 0))

                        case (False, True, False, True):
                            self.map.pset(x, y, (2, 0))

                        case (False, True, True, False):
                            self.map.pset(x, y, (3, 0))

                        case (False, True, True, True):
                            self.map.pset(x, y, (5, 0))

                        case (True, False, False, False):
                            self.map.pset(x, y, (3, 0))

                        case (True, False, True, False):
                            self.map.pset(x, y, (3, 0))

                        case (True, False, False, True):
                            self.map.pset(x, y, (2, 1))

                        case (True, False, True, True):
                            self.map.pset(x, y, (4, 0))

                        case (True, True, False, False):
                            self.map.pset(x, y, (3, 1))

                        case (True, True, False, True):
                            self.map.pset(x, y, (4, 1))

                        case (True, True, True, False):
                            self.map.pset(x, y, (5, 1))

                        case (True, True, True, True):
                            if not labyrinth_array[left_x, up_y]:
                                self.map.pset(x, y, (6, 0))
                            elif not labyrinth_array[right_x, up_y]:
                                self.map.pset(x, y, (7, 0))
                            elif not labyrinth_array[left_x, down_y]:
                                self.map.pset(x, y, (6, 1))
                            elif not labyrinth_array[right_x, down_y]:
                                self.map.pset(x, y, (7, 1))
                        case _:
                            pass

    def draw(self):
        pyxel.bltm(
            self.offset_x,
            self.offset_y,
            self.map,
            0,
            0,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )

class App:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Shining", fps=30)
        pyxel.load(RESOURCE_PATH)
        
        self.audio_queue = queue.Queue()
        self.audio_player = AudioPlayer(self.audio_queue)
        self.audio_player.start()
        
        self.game_start_time_ns = time.perf_counter_ns()
        self.game_running = True
        self.game_won = False
        self.game_over_timeout = 120 

        self.footsteps = [
            "sounds/snow_step_1.wav", 
            "sounds/snow_step_2.wav", 
            "sounds/snow_step_3.wav",
            "sounds/snow_step_4.wav",
            "sounds/snow_step_5.wav",
            "sounds/snow_step_6.wav",
            "sounds/snow_step_7.wav"
        ]
        
        # Précharge tous les sons de pas au démarrage du jeu pour éviter la latence.
        self.preloaded_footsteps = []
        for path in self.footsteps:
            try:
                self.preloaded_footsteps.append(pygame.mixer.Sound(path))
            except pygame.error:
                print(f"Erreur lors du chargement du son de pas : {path}")
                self.preloaded_footsteps.append(None)

        self.victory_sound_path = "sounds/victory_by_xtrgamr.wav"
        self.game_over_sound_path = "sounds/game_over_by_Leszek_Szary.wav"
        self.ambient_sound_path = "sounds/Wendy Carlos - Main Title (The Shining).flac"
        
        self.audio_player.start_ambient(self.ambient_sound_path, 0.3)
        
        self.labyrinth = Labyrinth(LABYRINTH_WIDTH, LABYRINTH_HEIGHT)
        self.son = Character(
            LABYRINTH_START_POSITION,
            key_right=pyxel.KEY_RIGHT,
            key_left=pyxel.KEY_LEFT,
            key_up=pyxel.KEY_UP,
            key_down=pyxel.KEY_DOWN,
            labyrinth=self.labyrinth,
            character_id="son",
            app_instance=self,
            image_index=1,
        )
        self.father = Character(
            LABYRINTH_START_POSITION,
            key_right=pyxel.KEY_D, 
            key_left=pyxel.KEY_Q,  
            key_up=pyxel.KEY_Z,    
            key_down=pyxel.KEY_S,  
            labyrinth=self.labyrinth,
            character_id="father",
            app_instance=self,
            image_index=2,
            transparent_color=2,
        )
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_L):
            self.game_running = False 
            self.audio_player.stop_ambient()
            pyxel.quit()
            return

        if not self.game_running:
            if self.audio_player.is_ambient_playing():
                self.audio_player.stop_ambient()
            return 
        
        self.son.update()
        self.father.update()

        current_game_time = (time.perf_counter_ns() - self.game_start_time_ns) / 1_000_000_000
        self.remaining_time = max(0, int(self.game_over_timeout - current_game_time))

        if self.son.exited and self.father.exited and not self.game_won:
            sound_event = SoundEvent(current_game_time, self.victory_sound_path, 1.0, 0.5)
            self.audio_queue.put(sound_event)
            self.game_won = True
            self.game_running = False 

        if current_game_time > self.game_over_timeout and not self.son.exited and not self.father.exited and not self.game_won:
            sound_event = SoundEvent(current_game_time, self.game_over_sound_path, 1.0, 0.5)
            self.audio_queue.put(sound_event)
            self.game_running = False
            self.audio_player.stop_ambient()

    def draw(self):
        pyxel.cls(7)
        self.labyrinth.draw()
        self.son.draw()
        self.father.draw()

        pyxel.text(5, 5, f"Time: {self.remaining_time}s", 0)

        if not self.game_running and not self.game_won:
            message = "GAME OVER!"
            text_color = pyxel.COLOR_RED
        elif self.game_won:
            message = "VICTORY!"
            text_color = pyxel.COLOR_GREEN
        else:
            message = None

        if message:
            text_width = len(message) * 4
            text_height = 6
            padding = 8
            
            rect_width = text_width + padding * 2
            rect_height = text_height + padding * 2
            
            rect_x = (SCREEN_WIDTH - rect_width) // 2
            rect_y = (SCREEN_HEIGHT - rect_height) // 2
            
            text_x = rect_x + padding
            text_y = rect_y + padding

            pyxel.rect(rect_x, rect_y, rect_width, rect_height, pyxel.COLOR_BLACK)
            pyxel.text(text_x, text_y, message, text_color)

if __name__ == "__main__":
    game_app = App()
