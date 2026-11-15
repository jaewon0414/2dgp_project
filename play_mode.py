from pico2d import *

import game_framework
import game_world
from background import Background
from heater import Heater
from hud import Hud
from snowman import Snowman

snowman = None


def handle_events():
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_F1:
            Hud.toggle()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_r:
            restart()
            return
        else:
            snowman.handle_event(event)


def init():
    global snowman

    game_world.add_object(Background(), game_world.BACKGROUND)

    # 2단계 확인용 장면: 왼쪽에서 출발해 오른쪽 난로를 끄고 눈밭에서 회복한다.
    heater = Heater(1000)
    game_world.add_object(heater, game_world.OBJECT)
    game_world.add_object(heater.zone, game_world.GROUND)

    snowman = Snowman(200)
    game_world.add_object(snowman, game_world.OBJECT)

    game_world.add_object(Hud(snowman), game_world.UI)

    game_world.add_collision_pair('snowman:heat', snowman, heater.zone)
    game_world.add_collision_pair('snowman:snowfield', snowman, None)
    game_world.add_collision_pair('snowball:heater', None, heater)


def finish():
    global snowman
    game_world.clear()
    snowman = None


def restart():
    finish()
    init()


def pause():
    pass


def resume():
    pass


def update():
    game_world.update()
    game_world.handle_collisions()
    if snowman.melt_finished():
        restart()


def render():
    clear_canvas()
    game_world.render()
    update_canvas()
