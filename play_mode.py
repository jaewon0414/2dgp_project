from pico2d import *

import camera
import game_framework
import game_world
import stages
from background import Background
from heater import Heater
from hud import Hud
from snowman import Snowman
from spirit import FlameSpirit, Fireball
from effects import Puff

current_stage = stages.STAGE_1

snowman = None
goal = None
hud = None
stage_clear = False
show_bb = False  # F2 로 충돌 상자를 보여 준다. (개발용)


def handle_events():
    global show_bb
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_F1:
            Hud.toggle()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_F2:
            show_bb = not show_bb
        elif event.type == SDL_KEYDOWN and event.key == SDLK_r:
            restart()
            return
        else:
            snowman.handle_event(event)


def add_heater(x, kind):
    heater = Heater(x, kind)
    game_world.add_object(heater, game_world.OBJECT)
    game_world.add_object(heater.zone, game_world.GROUND)
    game_world.add_collision_pair('snowman:heat', None, heater.zone)
    game_world.add_collision_pair('snowball:heater', None, heater)
    return heater


def init():
    global snowman, goal, hud, stage_clear
    stage = current_stage
    stage_clear = False
    camera.reset(stage['width'], stage['start_x'])

    game_world.add_object(Background(), game_world.BACKGROUND)

    for x in stage['heaters']:
        add_heater(x, 'small')
    goal = add_heater(stage['goal_x'], 'goal') if stage.get('goal_x') else None

    snowman = Snowman(stage['start_x'])
    game_world.add_object(snowman, game_world.OBJECT)
    game_world.add_collision_pair('snowman:heat', snowman, None)
    game_world.add_collision_pair('snowman:snowfield', snowman, None)
    game_world.add_collision_pair('snowman:fireball', snowman, None)

    for x in stage['spirits']:
        spirit = FlameSpirit(x, snowman)
        game_world.add_object(spirit, game_world.OBJECT)
        game_world.add_collision_pair('snowball:spirit', None, spirit)

    hud = Hud(snowman, stage['name'])
    game_world.add_object(hud, game_world.UI)


def finish():
    global snowman, goal, hud
    game_world.clear()
    snowman = None
    goal = None
    hud = None


def restart():
    finish()
    init()


def pause():
    pass


def resume():
    pass


def clear_stage():
    """큰 난로가 꺼지면 열에서 태어난 정령과 불덩이도 김이 되어 사라진다."""
    global stage_clear
    stage_clear = True
    hud.stage_clear = True
    for o in game_world.world[game_world.OBJECT][:]:
        if isinstance(o, (FlameSpirit, Fireball)):
            game_world.remove_object(o)
            game_world.add_object(Puff(o.x, o.y, count=6, size=44), game_world.OBJECT)


def update():
    game_world.update()
    game_world.handle_collisions()
    camera.follow(snowman.x, snowman.face, game_framework.frame_time)
    if goal is not None and not goal.is_on() and not stage_clear:
        clear_stage()
    if snowman.melt_finished():
        restart()


def draw_bounding_boxes():
    for layer in game_world.world:
        for o in layer:
            if hasattr(o, 'get_bb'):
                left, bottom, right, top = o.get_bb()
                draw_rectangle(camera.sx(left), bottom, camera.sx(right), top)


def render():
    clear_canvas()
    game_world.render()
    if show_bb:
        draw_bounding_boxes()
    update_canvas()
