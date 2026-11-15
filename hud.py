"""개발용 정보 표시. 눈의 양, 크기 단계, 상태, 속도를 보여 주고 F1 로 끄고 켠다.

정식 눈 게이지는 5단계에서 따로 만든다.
"""
from pico2d import get_canvas_height

import asset_loader
from snowman import SIZE_TABLE

TEXT_COLOR = (38, 44, 72)


class Hud:
    def __init__(self, snowman):
        self.snowman = snowman
        self.font = asset_loader.font('ENCR10B.TTF', 18)
        self.visible = True

    def toggle(self):
        self.visible = not self.visible

    def update(self):
        pass

    def draw(self):
        if not self.visible:
            return
        s = self.snowman
        level = s.size_level()
        top = get_canvas_height() - 24
        self.font.draw(16, top, f'SNOW {round(s.snow):3d}   SIZE {level:<6}   STATE {s.state}', TEXT_COLOR)
        self.font.draw(16, top - 24, f'SPEED {s.speed():.0f} px/s   JUMP {SIZE_TABLE[level]["jump_m"]:.1f} m',
                       TEXT_COLOR)
        self.font.draw(16, top - 48, '<- -> MOVE   UP JUMP   DOWN+MOVE ROLL   1/2/3 SIZE   -/= SNOW   F1 HIDE',
                       TEXT_COLOR)
