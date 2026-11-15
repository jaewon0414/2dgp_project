import math
import random

import asset_loader
import camera
import game_framework
import game_world
from effects import Puff
from rules import GROUND_Y, HEATER_KINDS
from snowfield import SnowField, FrozenGround

BODY_HALF_WIDTH = 58  # 눈덩이가 맞는 난로 몸통의 반 너비(크기 1 기준)
BODY_HEIGHT = 130  # 땅에서 난로 입구까지의 높이(크기 1 기준)
FLAMES = ((-14, 11.0, 0.8), (12, 13.0, 0.75), (0, 9.0, 1.0))  # 불꽃마다 (가로 위치, 흔들리는 빠르기, 크기)


class Heater:
    def __init__(self, x, kind='small'):
        self.x = x
        self.kind = kind
        spec = HEATER_KINDS[kind]
        self.max_hp = spec['hp']
        self.hp = spec['hp']
        self.scale = spec['scale']
        self.heat_range = spec['heat_range']
        self.heat_height = spec['heat_height']
        self.field_snow = spec['field_snow']
        self.field_width = spec['field_width']

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
        k = self.scale
        x = camera.sx(self.x) + math.sin(self.time * 70) * 5 * self.shake
        if self.is_on():
            # 남은 횟수가 줄면 불꽃도 작아진다. 불꽃 셋을 엇갈려 흔들어 일렁이게 한다.
            power = (0.45 + 0.55 * self.hp / self.max_hp) * k
            for i, (offset, speed, size) in enumerate(FLAMES):
                wobble = math.sin(self.time * speed + i * 2)
                w = self.flame.w * size * power * (1 - 0.05 * wobble)
                h = self.flame.h * size * power * (1 + 0.1 * wobble)
                self.flame.composite_draw(wobble * 0.08, '', x + offset * power,
                                          GROUND_Y + (BODY_HEIGHT - 12) * k + h / 2, w, h)
        image = self.on_image if self.is_on() else self.off_image
        image.draw(x, GROUND_Y + (image.h / 2 - 4) * k, image.w * k, image.h * k)

    def get_bb(self):
        half = BODY_HALF_WIDTH * self.scale
        return self.x - half, GROUND_Y, self.x + half, GROUND_Y + BODY_HEIGHT * self.scale

    def handle_collision(self, group, other):
        if group == 'snowball:heater' and self.is_on():
            self.hp -= 1
            self.shake = 1.0
            if self.hp == 0:
                self.turn_off()

    def turn_off(self):
        # 열이 사라지고, 김이 피어오르고, 그 자리가 얼어붙어 눈밭이 된다.
        # 꺼진 난로는 배경일 뿐이라 눈덩이가 그냥 지나가게 충돌 목록에서 뺀다.
        # (그대로 두면 난로 뒤의 정령에게 던진 눈덩이가 꺼진 난로에 막힌다.)
        game_world.remove_collision_object(self)
        game_world.remove_object(self.zone)
        game_world.add_object(Puff(self.x, GROUND_Y + BODY_HEIGHT * self.scale, count=10, size=70 * self.scale),
                              game_world.OBJECT)
        game_world.add_object(FrozenGround(self.x, self.heat_range * 2), game_world.GROUND)
        field = SnowField(self.x, self.field_snow, self.field_width)
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
        h = self.heater
        self.image.opacify(0.8 + 0.2 * math.sin(self.time * 4))
        height = GROUND_Y + h.heat_height
        self.image.draw(camera.sx(h.x), height / 2, h.heat_range * 2, height)
        self.image.opacify(1.0)

    def get_bb(self):
        h = self.heater
        return h.x - h.heat_range, GROUND_Y - 20, h.x + h.heat_range, GROUND_Y + h.heat_height

    def handle_collision(self, group, other):
        pass
