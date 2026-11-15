"""잠깐 보였다 사라지는 효과들."""
import random

import asset_loader
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
        self.image.draw(self.x, self.y, self.image.w * self.scale, self.image.h * self.scale)


class Splash:
    """눈덩이가 부딪힌 자리에서 눈 부스러기가 튄다."""
    LIFE = 0.45
    PIECE_GRAVITY = 1400

    def __init__(self, x, y, count=7):
        # 조각마다 [x, y, 가로 속도, 세로 속도, 반지름]
        self.pieces = [[x, y, random.uniform(-200, 200), random.uniform(60, 300), random.uniform(3, 7)]
                       for _ in range(count)]
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
                self.image.draw(x, y, size, size)
