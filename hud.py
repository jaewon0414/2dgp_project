"""화면 위에 겹쳐 보이는 글자.

왼쪽 위의 개발용 정보(눈의 양, 크기, 상태, 위치)는 F1 로 끄고 켠다. 정식 눈 게이지는 5단계에서 만든다.
"""
from pico2d import get_canvas_width, get_canvas_height

import asset_loader
import camera
import game_framework
from rules import SIZE_TABLE

TEXT_COLOR = (38, 44, 72)
BANNER_TIME = 2.5  # 시작할 때 스테이지 이름을 보여 주는 시간


class Hud:
    visible = True  # 다시 시작해도 켜고 끈 상태가 유지되도록 클래스에 둔다.

    def __init__(self, snowman, stage_name=''):
        self.snowman = snowman
        self.stage_name = stage_name
        self.stage_clear = False
        self.time = 0.0
        self.font = asset_loader.font('ENCR10B.TTF', 18)
        self.big_font = asset_loader.font('ENCR10B.TTF', 56)

    @classmethod
    def toggle(cls):
        cls.visible = not cls.visible

    def update(self):
        self.time += game_framework.frame_time

    def center_text(self, text, y, font=None, char_width=34):
        # ENCR10B 는 글자 폭이 일정해서 글자 수로 가운데를 맞출 수 있다.
        (font or self.big_font).draw(get_canvas_width() / 2 - len(text) * char_width / 2, y, text, TEXT_COLOR)

    def draw(self):
        s = self.snowman
        mid = get_canvas_height() / 2 + 120
        if s.state == 'MELT':
            self.center_text('MELTED...', mid)
        elif self.stage_clear:
            self.center_text('STAGE CLEAR!', mid)
            self.center_text('PRESS R TO PLAY AGAIN', mid - 56, self.font, 11)
        elif self.time < BANNER_TIME and self.stage_name:
            self.center_text(self.stage_name, mid)

        if not self.visible:
            return
        level = s.size_level()
        top = get_canvas_height() - 24
        self.font.draw(16, top, f'SNOW {round(s.snow):3d}   SIZE {level:<6}   STATE {s.state}', TEXT_COLOR)
        self.font.draw(16, top - 24, f'SPEED {s.speed():.0f} px/s   JUMP {SIZE_TABLE[level]["jump_m"]:.1f} m'
                                     f'   X {round(s.x)} / {camera.stage_width}', TEXT_COLOR)
        self.font.draw(16, top - 48, '<- -> MOVE   UP JUMP   DOWN+MOVE ROLL   SPACE THROW', TEXT_COLOR)
        self.font.draw(16, top - 72, 'DEV: 1/2/3 SIZE   -/= SNOW   R RESET   F1 HIDE   F2 BOXES', TEXT_COLOR)
