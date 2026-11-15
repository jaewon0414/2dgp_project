"""여러 층으로 된 배경. 먼 층일수록 천천히 스크롤되어 깊이가 느껴진다."""
from pico2d import get_canvas_width, get_canvas_height

import asset_loader
import camera

# (이미지, 스크롤 비율, 화면에서 이미지 아래쪽 높이). 비율 1 은 땅과 같은 속도다.
LAYERS = (
    ('bg_far.png', 0.15, 92),
    ('bg_village.png', 0.35, 90),
    ('bg_near.png', 0.6, 60),
    ('bg_ground.png', 1.0, 0),
)


class Background:
    def __init__(self):
        self.sky = asset_loader.image('bg_sky.png')  # 하늘과 땅. 움직이지 않는다.
        self.layers = [(asset_loader.image(name), rate, bottom) for name, rate, bottom in LAYERS]

    def update(self):
        pass

    def draw(self):
        self.sky.draw(get_canvas_width() / 2, get_canvas_height() / 2)
        for image, rate, bottom in self.layers:
            # 층 그림은 가로로 이어지게 만들어 두었으므로, 화면이 찰 때까지 옆으로 붙여 그린다.
            x = -(camera.left * rate % image.w)
            while x < get_canvas_width():
                image.draw(x + image.w / 2, bottom + image.h / 2)
                x += image.w
