"""잠깐 보였다 사라지는 효과들."""
import random

import asset_loader
import camera
import game_framework
import game_world
from rules import GROUND_Y, GRAVITY_PPS2


class Drip:
    """열을 받은 눈사람에게서 떨어지는 물방울."""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vy = random.uniform(-30.0, 30.0)
        self.scale = random.uniform(0.7, 1.1)
        self.image = asset_loader.image('drop.png')

    def update(self):
        dt = game_framework.frame_time
        self.vy -= GRAVITY_PPS2 * 0.6 * dt
        self.y += self.vy * dt
        if self.y <= GROUND_Y + 4:
            game_world.remove_object(self)

    def draw(self):
        self.image.draw(camera.sx(self.x), self.y, self.image.w * self.scale, self.image.h * self.scale)


class Splash:
    """눈덩이가 부딪힌 자리에서 눈 부스러기가 튄다."""
    LIFE = 0.45
    PIECE_GRAVITY = 1400

    def __init__(self, x, y, count=7, power=1.0):
        # 조각마다 [x, y, 가로 속도, 세로 속도, 반지름]
        self.pieces = [[x, y, random.uniform(-200, 200) * power, random.uniform(60, 300) * power,
                        random.uniform(3, 7) * power ** 0.5] for _ in range(count)]
        self.time = 0.0
        self.image = asset_loader.image('snowball.png')

    def update(self):
        dt = game_framework.frame_time
        self.time += dt
        for piece in self.pieces:
            piece[0] += piece[2] * dt
            piece[3] -= self.PIECE_GRAVITY * dt
            piece[1] += piece[3] * dt
        if self.time >= self.LIFE:
            game_world.remove_object(self)

    def draw(self):
        shrink = 1.0 - self.time / self.LIFE
        for x, y, _, _, radius in self.pieces:
            if y > GROUND_Y - 6:
                size = radius * 2 * shrink
                self.image.draw(camera.sx(x), y, size, size)


class Puff:
    """하얀 김이 피어오르며 사라진다. 불이 꺼질 때 쓴다."""
    LIFE = 0.7

    def __init__(self, x, y, count=6, size=44, spread=30):
        # 덩어리마다 [x, y, 가로 속도, 세로 속도, 크기]
        self.blobs = [[x + random.uniform(-spread, spread), y + random.uniform(-spread, spread) * 0.5,
                       random.uniform(-40, 40), random.uniform(40, 110), size * random.uniform(0.6, 1.0)]
                      for _ in range(count)]
        self.time = 0.0
        self.image = asset_loader.image('steam.png')

    def update(self):
        dt = game_framework.frame_time
        self.time += dt
        for blob in self.blobs:
            blob[0] += blob[2] * dt
            blob[1] += blob[3] * dt
        if self.time >= self.LIFE:
            game_world.remove_object(self)

    def draw(self):
        t = self.time / self.LIFE
        # 같은 그림을 여러 객체가 같이 쓰므로, 그리기 직전에 투명도를 정한다.
        self.image.opacify(1.0 - t)
        for x, y, _, _, size in self.blobs:
            s = size * (0.6 + 0.8 * t)
            self.image.draw(camera.sx(x), y, s, s)
        self.image.opacify(1.0)
