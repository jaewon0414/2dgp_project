"""assets 폴더의 이미지와 글꼴을 읽는다.

어느 폴더에서 실행해도 찾을 수 있도록 이 파일의 위치를 기준으로 경로를 만든다.
"""
import os

from pico2d import load_image, load_font

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')

_images = {}


def image(name):
    # 같은 그림은 한 번만 읽는다. 나중에 눈덩이처럼 여러 개 생기는 객체가 매번 파일을 읽지 않게 한다.
    if name not in _images:
        _images[name] = load_image(os.path.join(ASSET_DIR, name))
    return _images[name]


def font(name, size):
    return load_font(os.path.join(ASSET_DIR, name), size)
