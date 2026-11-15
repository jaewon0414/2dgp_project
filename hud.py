"""개발용 정보 표시. 눈의 양, 크기 단계, 상태, 속도를 보여 주고 F1 로 끄고 켠다.

정식 눈 게이지는 5단계에서 따로 만든다.
"""
from pico2d import get_canvas_width, get_canvas_height

import asset_loader
from rules import SIZE_TABLE

TEXT_COLOR = (38, 44, 72)


class Hud:
    visible = True  # 다시 시작해도 켜고 끈 상태가 유지되도록 클래스에 둔다.

    def __init__(self, snowman):
        self.snowman = snowman
        self.font = asset_loader.font('ENCR10B.TTF', 18)
        self.big_font = asset_loader.font('ENCR10B.TTF', 56)

    @classmethod
    def toggle(cls):
        cls.visible = not cls.visible

    def update(self):
        pass

    def draw(self):
        s = self.snowman
        if s.state == 'MELT':
            self.big_font.draw(get_canvas_width() / 2 - 150, get_canvas_height() / 2 + 60, 'MELTED...', TEXT_COLOR)
        if not self.visible:
            return
        level = s.size_level()
        top = get_canvas_height() - 24
        self.font.draw(16, top, f'SNOW {round(s.snow):3d}   SIZE {level:<6}   STATE {s.state}', TEXT_COLOR)
        self.font.draw(16, top - 24, f'SPEED {s.speed():.0f} px/s   JUMP {SIZE_TABLE[level]["jump_m"]:.1f} m',
                       TEXT_COLOR)
        self.font.draw(16, top - 48, '<- -> MOVE   UP JUMP   DOWN+MOVE ROLL   SPACE THROW', TEXT_COLOR)
        self.font.draw(16, top - 72, 'DEV: 1/2/3 SIZE   -/= SNOW   R RESET   F1 HIDE', TEXT_COLOR)
