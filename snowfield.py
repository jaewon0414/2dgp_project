import asset_loader
import game_framework
import game_world
from rules import GROUND_Y, SNOWFIELD_SNOW, SNOWFIELD_WIDTH


class SnowField:
    """난로를 끈 자리에 생기는 눈밭. 위에서 구르면 눈을 나눠 주고, 다 주면 사라진다."""

    def __init__(self, x):
        self.x = x
        self.snow = SNOWFIELD_SNOW
        self.appear = 0.0  # 생길 때 0 에서 1 로 커진다.
        self.image = asset_loader.image('snowfield.png')

    def ratio(self):
        return self.snow / SNOWFIELD_SNOW

    def width(self):
        # 눈을 가져갈수록 좁아져서 얼마나 남았는지 눈으로 보인다.
        return SNOWFIELD_WIDTH * (0.4 + 0.6 * self.ratio()) * self.appear

    def give(self, amount):
        """눈을 amount 만큼 달라고 하면, 남은 만큼만 주고 준 양을 돌려준다."""
        taken = min(amount, self.snow)
        self.snow -= taken
        if self.snow <= 0:
            game_world.remove_object(self)
        return taken

    def update(self):
        self.appear = min(1.0, self.appear + game_framework.frame_time * 3)

    def draw(self):
        w = self.width()
        h = self.image.h * (0.55 + 0.45 * self.ratio()) * self.appear
        self.image.draw(self.x, GROUND_Y - 8 + h / 2, w, h)

    def get_bb(self):
        half = self.width() / 2
        return self.x - half, GROUND_Y - 10, self.x + half, GROUND_Y + 20

    def handle_collision(self, group, other):
        pass
