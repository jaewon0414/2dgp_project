"""가로로 긴 스테이지에서 화면에 보이는 부분.

객체는 스테이지 좌표(x)를 가지고, 그릴 때만 camera.sx(x) 로 화면 좌표로 바꾼다. 세로로는 움직이지 않는다.
"""
from pico2d import get_canvas_width, clamp

LOOK_AHEAD = 140  # 눈사람이 바라보는 쪽을 조금 더 보여 준다.
FOLLOW_SPEED = 4.0  # 화면이 눈사람을 따라가는 빠르기. 클수록 바로 붙는다.

left = 0.0  # 화면 왼쪽 끝의 스테이지 좌표
stage_width = 1280


def max_left():
    return max(0.0, stage_width - get_canvas_width())


def reset(width, x):
    global left, stage_width
    stage_width = width
    left = clamp(0.0, x - get_canvas_width() / 2, max_left())


def follow(x, face, dt):
    global left
    target = clamp(0.0, x - get_canvas_width() / 2 + face * LOOK_AHEAD, max_left())
    left += (target - left) * min(1.0, dt * FOLLOW_SPEED)


def sx(x):
    return x - left


def on_screen(x, margin=0):
    return -margin <= x - left <= get_canvas_width() + margin
