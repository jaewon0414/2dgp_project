from pico2d import *

import game_framework
import game_world
from background import Background
from hud import Hud
from snowman import Snowman

snowman = None
hud = None


def handle_events():
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_F1:
            hud.toggle()
        else:
            snowman.handle_event(event)


def init():
    global snowman, hud

    game_world.add_object(Background(), game_world.BACKGROUND)

    snowman = Snowman()
    game_world.add_object(snowman, game_world.OBJECT)

    hud = Hud(snowman)
    game_world.add_object(hud, game_world.UI)


def finish():
    global snowman, hud
    game_world.clear()
    snowman = None
    hud = None


def pause():
    pass


def resume():
    pass


def update():
    game_world.update()


def render():
    clear_canvas()
    game_world.render()
    update_canvas()
