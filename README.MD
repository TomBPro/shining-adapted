# Shining

## Installation of requirements.txt

```sh
python3 -m venv projet_venv
python3 -m pip install -r requirements.txt
projet_venv\Scripts\activate
```

## Objectifs

- Sons differents pour chaque action et pour chaque joueur
- Son de victoire avec le personnage (quelconque) lorsqu'il sort du labyrinthe
- Son quand le pere atteint le fils

LE premier bruit de pas se fait au self.update() puis les autres à un intervalle plus court selon la distance parcourue
Il ya une coupure entre l'affichage du mouvement du personnage et le son de pas.

Mouvement: Thread principal (Graphique)
Son : Thread secondaire (Audio)

Les 2 communiquent entre eux mais sont séparés.
le self.update() envoie un queue au thread audio pour lui dire de jouer un son.
On fait des append dans la queue audio pour que le thread audio puisse jouer les sons.

Liste chainée + queue car thread safe
Principe de FIFO (First In First Out) pour la queue

Approche 1 : Plus on va vite, plus les pas vont s'enchainer rapidement. (timestamp)
Approche 2 : tuple + timestamp, son à jouer, volume, panoramique

1. Dans un nouveau fichier, créer une queue avec un timestamp panoramique
2. Puis, faire un mécanisme pour jouer les sons les uns après les autres en respectant le timestamp.

> (timestamp, "son à jouer", volume, panoramique)

Bibliothèque possible à utiliser : pygame

> pygame.mixer.init()
> sound = pygame.mixer.Sound("son.wav")
> sound.play()

BONUS: Son de game over si dépasse un temps limite.
