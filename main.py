import random
import sys
import os

import pygame
from pygame.locals import *

from shapely.geometry import Point
from shapely.geometry.polygon import Polygon


class MouseButtons:
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3
    WHEEL_UP = 4
    WHEEL_DOWN = 5


# settings
window_size = (1400, 800)
window_width, window_height = window_size
window_title = "Ars Amatoria - Alkohol"
framerate = 60
font_name = "Comic Sans MS"

# initialisation
os.environ["SDL_VIDEO_CENTERED"] = '1'
pygame.font.init()
pygame.init()
screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption(window_title)
clock = pygame.time.Clock()
title_font = pygame.font.SysFont(font_name, 22)
text_font = pygame.font.SysFont(font_name, 18)

# images
images_background = [pygame.image.load('sprites/background.{}.png'.format(x)).convert_alpha() for x in range(0, 11)]
images_1 = [pygame.image.load('sprites/persons1.{}.png'.format(x)).convert_alpha() for x in range(0, 11)]
images_2 = [pygame.image.load('sprites/persons2.{}.png'.format(x)).convert_alpha() for x in range(0, 11)]
images_3 = [pygame.image.load('sprites/persons3.{}.png'.format(x)).convert_alpha() for x in range(0, 11)]
images_door = [pygame.image.load('sprites/door.{}.png'.format(x)).convert_alpha() for x in range(0, 11)]

image_dialog = pygame.image.load('sprites/dialogbox.png').convert_alpha()


# dialogs
class Dialog:
    def __init__(self, title, text):
        self.title = title
        self.text = text

    def blit(self, screen):
        t1 = title_font.render(self.title, True, pygame.Color('white'))
        t2 = title_font.render(self.text, True, pygame.Color('white'))
        screen.blit(image_dialog, ((window_width / 2 - image_dialog.get_width() / 2), window_height - 200))
        screen.blit(t1, ((window_width / 2 - image_dialog.get_width() / 2) + 20, window_height - 200 + 20))
        screen.blit(t2, ((window_width / 2 - image_dialog.get_width() / 2) + 20, window_height - 200 + 45))


def show_dialog(title, text):
    pending_dialogs.append(Dialog(title, text))


def show_level_dialog():
    pending_dialogs.clear()
    choice = random.choice(dialogs[wine_level])
    c = True
    for itm in choice:
        if c:
            pending_dialogs.append(Dialog("Selbst", itm))
        else:
            pending_dialogs.append(Dialog("Person", itm))
        c = not c


# helpers
def get_outline(image, width=3, c=(255, 255, 255), threshold=127):
    mask = pygame.mask.from_surface(image, threshold)
    outline_image = pygame.Surface(image.get_size()).convert_alpha()
    outline_image.fill((0, 0, 0, 0))
    pygame.draw.lines(outline_image, c, True, mask.outline(), width)
    return outline_image


# intractable objects
class PolyClickable:
    def __init__(self, callback, poly, c=(0, 0, 0, 0)):
        self.callback = callback
        self.poly = poly
        self.c = pygame.color.Color(*c)

    def update(self, *args):
        for e in args[0]:
            if e.type == MOUSEBUTTONDOWN:
                point = Point(e.pos[0], e.pos[1])
                polygon = Polygon(self.poly)
                if polygon.contains(point):
                    self.callback()

    def blit(self, surface):
        pass


class Person(pygame.sprite.Sprite):
    def __init__(self, images, pos, **kwargs):
        pygame.sprite.Sprite.__init__(self)
        self.images = images
        self.rect = self.images[0].get_rect()
        self.mask = pygame.mask.from_surface(self.images[0], 50)
        self.pos = pos

        self.pressed_keys = []
        self.hover = False

        self.kwargs = kwargs

    def mouse_click_left(self):
        if 'mouse_click_left' in self.kwargs:
            self.kwargs['mouse_click_left']()

    def mouse_click_right(self):
        if 'mouse_click_right' in self.kwargs:
            self.kwargs['mouse_click_right']()

    def mouse_click_off(self):
        if 'mouse_click_off' in self.kwargs:
            self.kwargs['mouse_click_off']()

    def mouse_enter(self):
        self.hover = True
        if 'mouse_enter' in self.kwargs:
            self.kwargs['mouse_enter']()

    def mouse_leave(self):
        self.hover = False
        if 'mouse_leave' in self.kwargs:
            self.kwargs['mouse_leave']()

    def key_down(self, key):
        if 'key_down' in self.kwargs:
            self.kwargs['key_down'](key)

    def key_up(self, key):
        if 'key_up' in self.kwargs:
            self.kwargs['key_up'](key)

    def update(self, *args):
        for e in args[0]:
            if e.type == KEYDOWN:
                self.pressed_keys.append(e.key)
                self.key_down(e.key)
            elif e.type == KEYUP:
                self.pressed_keys.remove(e.key)
                self.key_up(e.key)

            elif e.type == MOUSEBUTTONDOWN:
                e_x = e.pos[0] - self.pos[0]
                e_y = e.pos[1] - self.pos[1]
                try:
                    if self.mask.get_at((e_x, e_y)):
                        if e.button == MouseButtons.LEFT:
                            self.mouse_click_left()
                        elif e.button == MouseButtons.RIGHT:
                            self.mouse_click_right()
                    else:
                        self.mouse_click_off()
                except IndexError:
                    self.mouse_click_off()

            if e.type == MOUSEMOTION:
                e_x = e.pos[0] - self.pos[0]
                e_y = e.pos[1] - self.pos[1]
                try:
                    if self.mask.get_at((e_x, e_y)):
                        self.mouse_enter()
                    else:
                        self.mouse_leave()
                except IndexError:
                    self.mouse_leave()

    def blit(self, surface):
        surface.blit(self.images[wine_level], self.pos)
        if self.hover:
            out = get_outline(self.images[0])
            out_rect = out.get_rect(center=[self.images[0].get_rect().center[0] + self.pos[0], self.images[0].get_rect().center[1] + self.pos[1]])
            surface.blit(out, out_rect)


# game state
wine_level = 0
ended = False
increasing = 0
pending_dialogs = []


# game state helpers
def increase_wine_level():
    global wine_level, increasing
    increasing += 1 * framerate
    wine_level += 1


# game objects
game_elements = [
    Person(images_1, [0, 0], mouse_click_left=lambda: show_level_dialog()),
    Person(images_2, [0, 0], mouse_click_left=lambda: show_level_dialog()),
    Person(images_3, [0, 0], mouse_click_left=lambda: show_level_dialog()),
    Person(images_door, [0, 0], mouse_click_left=lambda: increase_wine_level())
]

dialogs = {
    0:  [
        ["...", "..."],
        ["...", "..."],
        ["Eh...", "..."],
        ["Uhm...", "..."]
    ],
    1:  [
        ["...", "..."],
        ["...", "..."],
        ["...", "..."],
        ["Uhm...", "..?"]
    ],
    2:  [
        ["Hey", "Wer bist du?", "Mein Name ist Julius C & A, Ich kam sah und kaufte!", "Achso..."],
        ["...", "..."],
        ["...", "..."],
        ["Uhm...", "..?"]
    ],
    3:  [["..3.", "..."], ["...", "..."], ["...", "..."], ["Uhm...", "..?"]],
    4:  [["..4.", "..."], ["...", "..."], ["...", "..."], ["Uhm...", "..?"]],
    5:  [["..5.", "..."], ["...", "..."], ["...", "..."], ["Uhm...", "..?"]],
    6:  [["..6.", "..."], ["...", "..."], ["...", "..."], ["Uhm...", "..?"]],
    7:  [["..7.", "..."], ["...", "..."], ["...", "..."], ["Uhm...", "..?"]],
    8:  [["..8.", "..."], ["...", "..."], ["...", "..."], ["Uhm...", "..?"]],
    9:  [["..9.", "..."], ["...", "..."], ["...", "..."], ["Uhm...", "..?"]],
    10: [["..0.", "..."], ["...", "..."], ["...", "..."], ["Uhm...", "..?"]],
}

# main loop
while True:
    # events
    events = pygame.event.get()
    for event in events:
        # quit
        if event.type == QUIT:
            sys.exit(0)
        if event.type == MOUSEBUTTONDOWN:
            if pending_dialogs.__len__() > 0:
                pending_dialogs.remove(pending_dialogs[0])
                events.remove(event)

    if not ended:
        if increasing:
            screen.fill((0, 0, 0, 1))
            font = pygame.font.SysFont("Comic Sans MS", 72)
            text = font.render("Wenig später...", True, (255, 255, 255, 255))
            text_rect = text.get_rect(center=(window_width / 2, window_height / 2))
            screen.blit(text, text_rect)
            increasing -= 1
        else:
            # background
            try:
                screen.blit(images_background[wine_level], [0, 0])
                # game elements
                for el in game_elements:
                    el.update(events)
                    el.blit(screen)

                if pending_dialogs.__len__() > 0:
                    pending_dialogs[0].blit(screen)

                # debug
                fps = text_font.render("DEBUG: " + str(int(clock.get_fps())) + "|" + str(wine_level), True, pygame.Color('white'))
                screen.blit(fps, (50, 50))
            except IndexError:
                ended = True
    else:
        game_over = title_font.render("GAME OVER", True, pygame.Color('white'))
        drunk = title_font.render("Du hast zu viel getrunken und bist gestorben.", True, pygame.Color('white'))
        screen.fill((0, 0, 0, 1))
        screen.blit(game_over, (50, 50))
        screen.blit(drunk, (50, 75))

    # show
    pygame.display.flip()
    clock.tick(framerate)
