from pico2d import open_canvas, close_canvas
from sdl2 import SDL_SetHint, SDL_HINT_RENDER_SCALE_QUALITY

import game_framework
import play_mode as start_mode

CANVAS_WIDTH, CANVAS_HEIGHT = 1280, 720

open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
# 파츠를 줄여 그릴 때 계단 현상이 생기지 않게, 이미지를 읽기 전에 선형 보간으로 바꾼다.
SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, b'linear')
game_framework.run(start_mode)
close_canvas()
