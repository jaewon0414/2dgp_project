import math
import random

import asset_loader
import game_framework
import game_world
from rules import GROUND_Y, HEATER_HP, HEAT_RANGE, HEAT_HEIGHT
from snowfield import SnowField

BODY_HALF_WIDTH = 58  # 눈덩이가 맞는 난로 몸통의 반 너비
BODY_HEIGHT = 130  # 땅에서 난로 입구까지의 높이
FLAMES = ((-14, 11.0, 0.8), (12, 13.0, 0.75), (0, 9.0, 1.0))  # 불꽃마다 (가로 위치, 흔들리는 빠르기, 크기)


class Heater:
    def __init__(self, x):
        self.x = x
        self.hp = HEATER_HP
        self.time = random.uniform(0.0, 10.0)  # 난로마다 불꽃이 다르게 흔들리게 한다.
        self.shake = 0.0  # 눈덩이에 맞으면 1 이 되고 점점 줄어든다.
        self.on_image = asset_loader.image('heater_on.png')
        self.off_image = asset_loader.image('heater_off.png')
        self.flame = asset_loader.image('flame.png')
        self.zone = HeatZone(self)

    def is_on(self):
        return self.hp > 0

    def update(self):
        dt = game_framework.frame_time
        self.time += dt
        self.shake = max(0.0, self.shake - dt * 4)

    def draw(self):
        dx = math.sin(self.time * 70) * 5 * self.shake
        if self.is_on():
            # 남은 횟수가 줄면 불꽃도 작아진다. 불꽃 셋을 엇갈려 흔들어 일렁이게 한다.
            power = 0.45 + 0.55 * self.hp / HEATER_HP
            for i, (offset, speed, size) in enumerate(FLAMES):
                wobble = math.sin(self.time * speed + i * 2)
                w = self.flame.w * size * power * (1 - 0.05 * wobble)
                h = self.flame.h * size * power * (1 + 0.1 * wobble)
                self.flame.composite_draw(wobble * 0.08, '', self.x + dx + offset * power,
                                          GROUND_Y + BODY_HEIGHT - 12 + h / 2, w, h)
        image = self.on_image if self.is_on() else self.off_image
        image.draw(self.x + dx, GROUND_Y - 4 + image.h / 2)

    def get_bb(self):
        return self.x - BODY_HALF_WIDTH, GROUND_Y, self.x + BODY_HALF_WIDTH, GROUND_Y + BODY_HEIGHT

    def handle_collision(self, group, other):
        if group == 'snowball:heater' and self.is_on():
            self.hp -= 1
            self.shake = 1.0
            if self.hp == 0:
                self.turn_off()

    def turn_off(self):
        # 열이 사라지고, 그 자리가 얼어붙어 눈밭이 된다.
        game_world.remove_object(self.zone)
        field = SnowField(self.x)
        game_world.add_object(field, game_world.GROUND)
        game_world.add_collision_pair('snowman:snowfield', None, field)


class HeatZone:
    """난로 주변의 열 구역. 이 안에 있는 눈사람은 계속 녹는다."""

    def __init__(self, heater):
        self.heater = heater
        self.time = 0.0
        self.image = asset_loader.image('heat.png')

    def update(self):
        self.time += game_framework.frame_time

    def draw(self):
        # 화면 맨 아래부터 그려서 땅까지 붉게 물들인다. 위쪽은 이미지 자체가 옅어지며 사라진다.
        self.image.opacify(0.8 + 0.2 * math.sin(self.time * 4))
        height = GROUND_Y + HEAT_HEIGHT
        self.image.draw(self.heater.x, height / 2, HEAT_RANGE * 2, height)

    def get_bb(self):
        return self.heater.x - HEAT_RANGE, GROUND_Y - 20, self.heater.x + HEAT_RANGE, GROUND_Y + HEAT_HEIGHT

    def handle_collision(self, group, other):
        pass
