from pico2d import get_canvas_width, get_canvas_height

import asset_loader


class Background:
    def __init__(self):
        self.image = asset_loader.image('background.png')

    def update(self):
        pass

    def draw(self):
        self.image.draw(get_canvas_width() / 2, get_canvas_height() / 2)
