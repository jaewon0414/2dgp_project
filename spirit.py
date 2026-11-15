"""불꽃 정령과 불덩이.

정령은 상태 머신으로 움직인다.
  WANDER: 제자리 근처를 떠다닌다. 눈사람이 가까이 오면 CHASE.
  CHASE: 눈사람과 일정한 거리를 유지한다. 멀면 다가가고 가까우면 물러난다. 쏠 준비가 되면 AIM.
  AIM: 멈춰서 부풀어 오르며 쏠 것을 알려 준 뒤, 눈사람을 향해 불덩이를 쏘고 CHASE 로 돌아간다.
눈사람이 너무 멀어지거나 녹으면 WANDER 로 돌아간다.
"""
import math
import random

from pico2d import clamp
from transitions import Machine

import asset_loader
import camera
import game_framework
import game_world
from effects import Puff
from rules import (GROUND_Y, SPIRIT_HP, SPIRIT_SPEED, SPIRIT_HOVER_HEIGHT, SPIRIT_NOTICE_RANGE,
                   SPIRIT_GIVE_UP_RANGE, SPIRIT_KEEP_MIN, SPIRIT_KEEP_MAX, SPIRIT_LEASH,
                   SPIRIT_AIM_TIME, SPIRIT_FIRE_COOLDOWN, FIREBALL_SPEED)

DRAW_SCALE = 0.8
WANDER_WIDTH = 120  # 떠다닐 때 제자리에서 좌우로 움직이는 거리
HURT_TIME = 0.3
HEIGHT_FOLLOW_SPEED = 2.0  # 싸울 때 눈사람 손 높이로 내려오거나 올라가는 빠르기
BELOW_HAND = 30  # 싸울 때 눈사람 손보다 이만큼 낮게 뜬다. 던진 눈덩이가 지나가는 높이다.


class Wander:
    def enter(self, spirit):
        pass

    def do(self, spirit):
        target = spirit.home_x + math.sin(spirit.time * 0.6) * WANDER_WIDTH
        spirit.move_toward(target, SPIRIT_SPEED * 0.5)
        if spirit.distance_to_player() < SPIRIT_NOTICE_RANGE and spirit.player.state != 'MELT':
            spirit.notice()


class Chase:
    def enter(self, spirit):
        pass

    def do(self, spirit):
        player = spirit.player
        gap = player.x - spirit.x
        distance = abs(gap)
        spirit.face = 1 if gap > 0 else -1
        if distance > SPIRIT_GIVE_UP_RANGE or player.state == 'MELT':
            spirit.give_up()
            return

        # 너무 가까우면 물러나고, 너무 멀면 다가간다. 그 사이에서는 멈춰서 기다린다.
        if distance > SPIRIT_KEEP_MAX:
            spirit.move_toward(player.x, SPIRIT_SPEED)
        elif distance < SPIRIT_KEEP_MIN:
            spirit.move_toward(spirit.x - spirit.face * 100, SPIRIT_SPEED)

        # 화면 밖에서는 쏘지 않는다. 보이지 않는 곳에서 날아오는 공격은 피할 수 없기 때문이다.
        in_range = SPIRIT_KEEP_MIN * 0.8 <= distance <= SPIRIT_KEEP_MAX * 1.2
        if spirit.cooldown <= 0 and in_range and camera.on_screen(spirit.x, -40):
            spirit.aim()


class Aim:
    def enter(self, spirit):
        spirit.aim_time = 0.0

    def do(self, spirit):
        spirit.aim_time += game_framework.frame_time
        spirit.face = 1 if spirit.player.x > spirit.x else -1
        if spirit.player.state == 'MELT':
            spirit.give_up()
        elif spirit.aim_time >= SPIRIT_AIM_TIME:
            spirit.fire()
            spirit.cooldown = SPIRIT_FIRE_COOLDOWN
            spirit.fired()


class FlameSpirit:
    def __init__(self, x, player):
        self.home_x = x
        self.x = x
        self.player = player
        self.face = -1
        self.hp = SPIRIT_HP
        self.time = random.uniform(0.0, 10.0)
        self.cooldown = SPIRIT_FIRE_COOLDOWN * 0.5  # 처음 마주쳤을 때 바로 쏘지 않게 조금 기다린다.
        self.aim_time = 0.0
        self.hurt = 0.0
        self.height = GROUND_Y + SPIRIT_HOVER_HEIGHT  # 흔들림을 빼고 떠 있는 높이
        self.image = asset_loader.image('spirit.png')

        self.states = {'WANDER': Wander(), 'CHASE': Chase(), 'AIM': Aim()}
        self.machine = Machine(
            model=self,
            states=['WANDER', 'CHASE', 'AIM'],
            transitions=[
                {'trigger': 'notice', 'source': 'WANDER', 'dest': 'CHASE'},
                {'trigger': 'aim', 'source': 'CHASE', 'dest': 'AIM'},
                {'trigger': 'fired', 'source': 'AIM', 'dest': 'CHASE'},
                {'trigger': 'give_up', 'source': ['CHASE', 'AIM'], 'dest': 'WANDER'},
            ],
            initial='WANDER',
            auto_transitions=False,
        )

    def on_enter_WANDER(self):
        self.states['WANDER'].enter(self)

    def on_enter_CHASE(self):
        self.states['CHASE'].enter(self)

    def on_enter_AIM(self):
        self.states['AIM'].enter(self)

    @property
    def y(self):
        # 위아래로 둥실둥실 떠 있다.
        return self.height + math.sin(self.time * 2.4) * 12

    def target_height(self):
        """떠다닐 때는 정해진 높이에, 싸울 때는 눈사람 손보다 조금 낮은 높이에 뜬다.

        눈사람은 크기마다 손 높이가 달라서 눈덩이가 지나가는 높이도 다르다. 정령이 그 높이로 내려와야
        어느 크기에서든 맞힐 수 있다. 몸통 반지름의 2.6 배가 손 높이와 거의 같다.
        """
        if self.state == 'WANDER':
            return GROUND_Y + SPIRIT_HOVER_HEIGHT
        return self.player.y + self.player.body_radius() * 2.6 - BELOW_HAND

    def distance_to_player(self):
        return abs(self.player.x - self.x)

    def move_toward(self, target_x, speed):
        step = min(abs(target_x - self.x), speed * game_framework.frame_time)
        self.x += step if target_x > self.x else -step
        self.x = clamp(self.home_x - SPIRIT_LEASH, self.x, self.home_x + SPIRIT_LEASH)

    def fire(self):
        # 쏘는 순간의 눈사람 몸통 가운데를 겨눈다. 그 뒤로는 방향을 바꾸지 않아서 피할 수 있다.
        start_x, start_y = self.x + self.face * 30, self.y
        target_y = self.player.y + self.player.body_radius()
        dx, dy = self.player.x - start_x, target_y - start_y
        length = math.hypot(dx, dy) or 1.0
        ball = Fireball(start_x, start_y, dx / length * FIREBALL_SPEED, dy / length * FIREBALL_SPEED)
        game_world.add_object(ball, game_world.OBJECT)
        game_world.add_collision_pair('snowman:fireball', None, ball)
        game_world.add_collision_pair('snowball:fireball', None, ball)

    def update(self):
        dt = game_framework.frame_time
        self.time += dt
        self.cooldown = max(0.0, self.cooldown - dt)
        self.hurt = max(0.0, self.hurt - dt)
        self.states[self.state].do(self)
        self.height += (self.target_height() - self.height) * min(1.0, dt * HEIGHT_FOLLOW_SPEED)

    def draw(self):
        if self.hurt > 0 and int(self.hurt * 20) % 2 == 0:
            return  # 맞으면 깜빡인다.
        sx = math.sin(self.time * 11) * 0.05
        sy = math.sin(self.time * 13 + 1) * 0.07
        swell, shake = 1.0, 0.0
        if self.state == 'AIM':
            # 쏘기 직전에 부풀고 떨면서 알려 준다.
            t = self.aim_time / SPIRIT_AIM_TIME
            swell = 1 + 0.3 * t
            shake = math.sin(self.time * 60) * 4 * t
        w = self.image.w * DRAW_SCALE * swell * (1 + sx)
        h = self.image.h * DRAW_SCALE * swell * (1 + sy)
        flip = '' if self.face == 1 else 'h'
        self.image.composite_draw(math.sin(self.time * 3) * 0.06, flip, camera.sx(self.x) + shake, self.y, w, h)

    def get_bb(self):
        return self.x - 30, self.y - 42, self.x + 30, self.y + 26

    def handle_collision(self, group, other):
        if group == 'snowball:spirit':
            self.hp -= 1
            self.hurt = HURT_TIME
            if self.hp <= 0:
                self.die()

    def die(self):
        game_world.remove_object(self)
        game_world.add_object(Puff(self.x, self.y, count=8, size=50), game_world.OBJECT)


class Fireball:
    def __init__(self, x, y, vx, vy):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.rot = 0.0
        self.image = asset_loader.image('fireball.png')

    def update(self):
        dt = game_framework.frame_time
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rot += 9 * dt
        if self.y <= GROUND_Y:
            self.fizzle()
        elif not camera.on_screen(self.x, 200):
            game_world.remove_object(self)

    def fizzle(self):
        game_world.remove_object(self)
        game_world.add_object(Puff(self.x, self.y, count=3, size=28), game_world.OBJECT)

    def draw(self):
        self.image.composite_draw(self.rot, '', camera.sx(self.x), self.y, 36, 36)

    def get_bb(self):
        return self.x - 12, self.y - 12, self.x + 12, self.y + 12

    def handle_collision(self, group, other):
        if group == 'snowman:fireball':
            game_world.remove_object(self)
        elif group == 'snowball:fireball':
            self.fizzle()
