import asset_loader
import camera
import game_framework
import game_world
from effects import Splash, Puff
from rules import GROUND_Y, THROW_SPEED_X, THROW_SPEED_Y, SNOWBALL_GRAVITY, SNOWBALL_RADIUS

IMAGE_BALL_RADIUS = 19  # snowball.png 안에 그려진 눈덩이의 반지름


class Snowball:
    def __init__(self, x, y, face, scale):
        self.x, self.y = x, y
        self.vx, self.vy = face * THROW_SPEED_X, THROW_SPEED_Y
        self.radius = SNOWBALL_RADIUS * scale
        self.rot = 0.0
        self.image = asset_loader.image('snowball.png')

    def update(self):
        dt = game_framework.frame_time
        self.x += self.vx * dt
        old_vy = self.vy
        self.vy -= SNOWBALL_GRAVITY * dt
        self.y += (old_vy + self.vy) / 2 * dt
        self.rot -= self.vx / self.radius * 0.3 * dt  # 날아가며 빙글빙글 돈다.

        if self.y - self.radius <= GROUND_Y:
            self.burst()
        elif not camera.on_screen(self.x, 100):
            game_world.remove_object(self)

    def burst(self):
        game_world.remove_object(self)
        game_world.add_object(Splash(self.x, max(self.y, GROUND_Y + self.radius)), game_world.OBJECT)

    def draw(self):
        size = self.image.w * self.radius / IMAGE_BALL_RADIUS
        self.image.composite_draw(self.rot, '', camera.sx(self.x), self.y, size, size)

    def get_bb(self):
        return self.x - self.radius, self.y - self.radius, self.x + self.radius, self.y + self.radius

    def handle_collision(self, group, other):
        if group in ('snowball:heater', 'snowball:spirit'):
            self.burst()
        elif group == 'snowball:fireball':
            # 눈덩이와 불덩이가 부딪히면 둘 다 김이 되어 사라진다.
            game_world.remove_object(self)
            game_world.add_object(Puff(self.x, self.y, count=4, size=34), game_world.OBJECT)
