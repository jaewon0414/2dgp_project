"""주인공 눈사람.

눈의 양이 곧 크기다. 크기는 큼, 중간, 작음 세 단계이고, 작을수록 빠르고 높이 뛴다.
몸은 파츠 이미지 여러 장을 코드로 돌리고 늘려서 움직이는 컷아웃 애니메이션으로 그린다.
"""
import math

from pico2d import get_canvas_width, clamp
from sdl2 import (SDL_KEYDOWN, SDL_KEYUP, SDLK_LEFT, SDLK_RIGHT, SDLK_UP, SDLK_DOWN,
                  SDLK_1, SDLK_2, SDLK_3, SDLK_MINUS, SDLK_EQUALS)
from transitions import Machine

import asset_loader
import game_framework

PIXEL_PER_METER = 100.0  # 100 픽셀이 1 m 다. 큰 눈사람의 키가 2.8 m 쯤 된다.


def kmph_to_pps(kmph):
    return kmph * 1000.0 / 3600.0 * PIXEL_PER_METER


GRAVITY_PPS2 = 20.0 * PIXEL_PER_METER  # 실제 중력(9.8)보다 세게 해서 점프가 둥둥 뜨지 않게 한다.
GROUND_Y = 74  # 눈사람 발밑의 높이

MAX_SNOW = 100
BIG_SNOW = 67  # 눈이 이 값 이상이면 큼
MIDDLE_SNOW = 34  # 이 값 이상이면 중간, 그보다 적으면 작음

# 크기 단계별 수치. 플레이해 보면서 조정한다.
SIZE_TABLE = {
    'BIG': {'scale': 1.0, 'speed_kmph': 6.0, 'jump_m': 1.0},
    'MIDDLE': {'scale': 0.78, 'speed_kmph': 8.0, 'jump_m': 1.4},
    'SMALL': {'scale': 0.55, 'speed_kmph': 10.0, 'jump_m': 1.8},
}
ROLL_SPEED_RATE = 1.3  # 구르면 걷기보다 빠르다.
STEP_LENGTH_PX = 90  # 걸을 때 한 번 통통 튀며 나아가는 거리(큰 눈사람 기준)

# 파츠 이미지의 원래 크기를 기준으로 한 값
BASE_SCALE = 0.62
BODY_RADIUS = 112
HEAD_RADIUS = 80
ARM_PIVOT_TO_CENTER = 67
TAIL_PIVOT_TO_CENTER = 50

# 개발용 단축키. 던지기와 열이 생기기 전까지 크기 단계를 바로 바꿔 보는 데 쓴다.
DEBUG_SNOW_KEYS = {SDLK_1: 25, SDLK_2: 50, SDLK_3: MAX_SNOW}
DEBUG_SNOW_STEP = 5


def level_of(snow):
    if snow >= BIG_SNOW:
        return 'BIG'
    if snow >= MIDDLE_SNOW:
        return 'MIDDLE'
    return 'SMALL'


class Pose:
    """한 프레임의 몸짓. 각 상태가 만들고, 그리기는 이 값대로 파츠를 놓는다.

    길이는 파츠 이미지 기준이고 그릴 때 현재 크기를 곱한다. 각도는 라디안이며 오른쪽을 볼 때 기준이다.
    """

    def __init__(self):
        self.lift = 0.0  # 몸이 땅에서 튀어 오른 높이
        self.tilt = 0.0  # 몸 전체의 기울기
        self.squash_x, self.squash_y = 1.0, 1.0  # 몸통을 가로, 세로로 늘이는 비율
        self.arm_front = 0.25  # 앞팔의 각도. 클수록 위로 든다.
        self.arm_back = 0.2  # 뒷팔의 각도
        self.head_shift = 0.0  # 머리가 몸통 위에서 좌우로 밀린 거리


class Idle:
    def enter(self, snowman):
        pass

    def do(self, snowman):
        snowman.phase += 2.5 * game_framework.frame_time

    def pose(self, snowman):
        pose = Pose()
        breath = math.sin(snowman.phase)
        pose.squash_x, pose.squash_y = 1 - breath * 0.015, 1 + breath * 0.015
        pose.arm_front += breath * 0.05
        pose.arm_back -= breath * 0.05
        return pose


class Walk:
    def enter(self, snowman):
        pass

    def do(self, snowman):
        moved = snowman.move_x(snowman.speed())
        # 통통 한 번이 phase 로 pi 만큼이다. 몸이 작으면 보폭도 짧아서 더 자주 튄다.
        snowman.phase += moved / (STEP_LENGTH_PX * math.sqrt(snowman.scale)) * math.pi

    def pose(self, snowman):
        # 다리가 없으니 통통 튀면서 좌우로 기우뚱거린다.
        pose = Pose()
        hop = abs(math.sin(snowman.phase))
        pose.lift = hop * 30
        pose.tilt = math.cos(snowman.phase) * 0.11
        pose.squash_x, pose.squash_y = 1.05 - hop * 0.08, 0.95 + hop * 0.08
        pose.arm_front += math.sin(snowman.phase) * 0.45
        pose.arm_back -= math.sin(snowman.phase) * 0.45
        return pose


class Roll:
    def enter(self, snowman):
        pass

    def do(self, snowman):
        moved = snowman.move_x(snowman.speed() * ROLL_SPEED_RATE)
        # 미끄러지지 않고 굴러가려면, 나아간 거리를 반지름으로 나눈 만큼 돌아야 한다.
        snowman.body_rot -= moved / snowman.body_radius()
        snowman.phase += 4.0 * game_framework.frame_time

    def pose(self, snowman):
        # 몸통만 굴리고, 머리는 공 위에서 균형을 잡듯 흔들린다.
        pose = Pose()
        pose.head_shift = math.sin(snowman.body_rot * 3) * 8
        pose.arm_front = 0.85 + math.sin(snowman.body_rot * 4) * 0.25
        pose.arm_back = 0.85 - math.sin(snowman.body_rot * 4) * 0.25
        return pose


class Jump:
    def enter(self, snowman):
        snowman.vy = snowman.jump_speed()

    def do(self, snowman):
        dt = game_framework.frame_time
        snowman.move_x(snowman.speed())
        snowman.phase += 2.5 * dt
        # 이번 프레임의 처음과 끝 속도의 평균으로 움직여야 프레임 속도와 상관없이 같은 높이까지 오른다.
        old_vy = snowman.vy
        snowman.vy -= GRAVITY_PPS2 * dt
        snowman.y += (old_vy + snowman.vy) / 2 * dt
        if snowman.y <= GROUND_Y:
            snowman.y, snowman.vy = GROUND_Y, 0.0
            snowman.land_squash = 1.0
            snowman.follow_keys()  # 착지하면 누르고 있는 키에 맞는 상태로 바뀐다.

    def pose(self, snowman):
        # 올라갈 때는 위로 길쭉해지며 팔을 들고, 떨어질 때는 팔을 옆으로 벌려 균형을 잡는다.
        pose = Pose()
        rise = clamp(-1.0, snowman.vy / snowman.jump_speed(), 1.0)
        pose.squash_x, pose.squash_y = 1 - rise * 0.07, 1 + rise * 0.07
        pose.tilt = -0.07 * abs(snowman.dir)
        pose.arm_front = 0.55 + rise * 0.5
        pose.arm_back = 0.5 + rise * 0.5
        return pose


class Snowman:
    def __init__(self, x=640):
        self.x, self.y = x, GROUND_Y
        self.vy = 0.0
        self.dir = 0
        self.face = 1
        self.pressed_keys = set()

        self.snow = MAX_SNOW
        # 화면에 그리는 크기. 크기 단계가 바뀌면 한 번에 바뀌지 않고 부드럽게 따라간다.
        self.scale = SIZE_TABLE[self.size_level()]['scale']

        self.phase = 0.0  # 숨쉬기와 걷기에 쓰는 시간 값
        self.body_rot = 0.0  # 구를 때 몸통의 회전 각도
        self.pot_rot = 0.0  # 냄비는 몸보다 늦게 따라와서 무게감을 준다.
        self.tail_rot = 0.0
        self.land_squash = 0.0  # 착지 직후 납작해지는 정도. 1 에서 0 으로 줄어든다.

        self.body = asset_loader.image('body.png')
        self.body_shade = asset_loader.image('body_shade.png')
        self.head = asset_loader.image('head.png')
        self.pot = asset_loader.image('pot.png')
        self.arm_a = asset_loader.image('arm_a.png')
        self.arm_b = asset_loader.image('arm_b.png')
        self.scarf = asset_loader.image('scarf.png')
        self.tail = asset_loader.image('scarf_tail.png')
        self.shadow = asset_loader.image('shadow.png')

        self.states = {'IDLE': Idle(), 'WALK': Walk(), 'ROLL': Roll(), 'JUMP': Jump()}
        self.machine = Machine(
            model=self,
            states=['IDLE', 'WALK', 'ROLL', 'JUMP'],
            transitions=[
                {'trigger': 'stop', 'source': ['WALK', 'ROLL', 'JUMP'], 'dest': 'IDLE'},
                {'trigger': 'walk', 'source': ['IDLE', 'ROLL', 'JUMP'], 'dest': 'WALK'},
                {'trigger': 'roll', 'source': ['IDLE', 'WALK', 'JUMP'], 'dest': 'ROLL'},
                {'trigger': 'jump', 'source': ['IDLE', 'WALK', 'ROLL'], 'dest': 'JUMP'},
            ],
            initial='IDLE',
            auto_transitions=False,
        )

    def on_enter_IDLE(self):
        self.states['IDLE'].enter(self)

    def on_enter_WALK(self):
        self.states['WALK'].enter(self)

    def on_enter_ROLL(self):
        self.states['ROLL'].enter(self)

    def on_enter_JUMP(self):
        self.states['JUMP'].enter(self)

    # 크기에 따라 달라지는 값들

    def size_level(self):
        return level_of(self.snow)

    def speed(self):
        return kmph_to_pps(SIZE_TABLE[self.size_level()]['speed_kmph'])

    def jump_speed(self):
        # 높이 h 까지 올라가려면 처음 속도가 sqrt(2gh) 여야 한다.
        height = SIZE_TABLE[self.size_level()]['jump_m'] * PIXEL_PER_METER
        return math.sqrt(2 * GRAVITY_PPS2 * height)

    def body_radius(self):
        return BODY_RADIUS * BASE_SCALE * self.scale

    def set_snow(self, amount):
        self.snow = clamp(0, amount, MAX_SNOW)

    # 입력과 상태 전환

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN:
            if event.key in DEBUG_SNOW_KEYS:
                self.set_snow(DEBUG_SNOW_KEYS[event.key])
                return
            if event.key == SDLK_MINUS:
                self.set_snow(self.snow - DEBUG_SNOW_STEP)
                return
            if event.key == SDLK_EQUALS:
                self.set_snow(self.snow + DEBUG_SNOW_STEP)
                return
            self.pressed_keys.add(event.key)
        elif event.type == SDL_KEYUP:
            self.pressed_keys.discard(event.key)
        else:
            return

        self.dir = int(SDLK_RIGHT in self.pressed_keys) - int(SDLK_LEFT in self.pressed_keys)
        if self.dir != 0:
            self.face = self.dir

        if self.state == 'JUMP':
            return  # 공중에서는 좌우 방향만 바꾼다. 상태는 착지할 때 고른다.
        if event.type == SDL_KEYDOWN and event.key == SDLK_UP:
            self.jump()
        else:
            self.follow_keys()

    def follow_keys(self):
        """땅 위에서, 누르고 있는 키에 맞는 상태로 바꾼다."""
        if self.dir == 0:
            wanted = 'IDLE'
        elif SDLK_DOWN in self.pressed_keys:
            wanted = 'ROLL'
        else:
            wanted = 'WALK'
        if wanted != self.state:
            {'IDLE': self.stop, 'WALK': self.walk, 'ROLL': self.roll}[wanted]()

    def move_x(self, speed):
        moved = speed * game_framework.frame_time
        self.x += self.dir * moved
        return moved

    def update(self):
        dt = game_framework.frame_time
        self.states[self.state].do(self)

        target = SIZE_TABLE[self.size_level()]['scale']
        self.scale += (target - self.scale) * min(1.0, dt * 8)

        margin = self.body_radius() + 20
        self.x = clamp(margin, self.x, get_canvas_width() - margin)

        moving = self.state != 'IDLE'
        self.pot_rot += ((0.16 if moving else 0.0) - self.pot_rot) * min(1.0, dt * 8)
        self.tail_rot += ((-0.55 if moving else -0.06) - self.tail_rot) * min(1.0, dt * 6)
        self.land_squash = max(0.0, self.land_squash - dt * 5)

    # 그리기

    def place(self, image, lx, ly, rad=0.0, scale_x=1.0, scale_y=1.0, mirrored=False):
        """오른쪽을 본다고 가정한 위치(lx, ly)에 파츠를 그린다. 왼쪽을 보면 통째로 뒤집는다."""
        flip = 'h' if (self.face == -1) != mirrored else ''
        image.composite_draw(rad * self.face, flip, self.x + lx * self.face, ly,
                             image.w * scale_x, image.h * scale_y)

    def draw(self):
        pose = self.states[self.state].pose(self)

        # 몸은 크기에 맞춰 줄고, 머리는 덜 줄어서 작을 때 더 귀엽게 보인다.
        k = BASE_SCALE * self.scale
        head_k = BASE_SCALE * self.scale ** 0.7

        squash_x = pose.squash_x * (1 + 0.14 * self.land_squash)
        squash_y = pose.squash_y * (1 - 0.14 * self.land_squash)
        tilt = pose.tilt
        head_shift = pose.head_shift * k

        body_h = BODY_RADIUS * k * squash_y
        center_y = self.y + body_h + pose.lift * k

        def rotated(lx, ly):
            # 몸통 중심 기준의 위치를 기울기만큼 돌린다.
            c, s = math.cos(tilt), math.sin(tilt)
            return lx * c - ly * s, center_y + lx * s + ly * c

        # 그림자는 땅에 붙어 있고, 몸이 높이 뜰수록 작아진다.
        height = center_y - body_h - GROUND_Y
        shadow_k = k * max(0.5, 1.25 - height * 0.004)
        self.shadow.draw(self.x, GROUND_Y + 2, self.shadow.w * shadow_k, self.shadow.h * shadow_k)

        # 팔은 몸통보다 먼저 그려서 뿌리가 눈 속에 박힌 것처럼 보이게 한다.
        sx, sy = rotated(BODY_RADIUS * k * 0.66, body_h * 0.48)
        angle = tilt + pose.arm_front
        self.place(self.arm_a, sx + math.cos(angle) * ARM_PIVOT_TO_CENTER * k,
                   sy + math.sin(angle) * ARM_PIVOT_TO_CENTER * k, angle, k, k)

        sx, sy = rotated(-BODY_RADIUS * k * 0.66, body_h * 0.48)
        angle = pose.arm_back - tilt
        self.place(self.arm_b, sx - math.cos(angle) * ARM_PIVOT_TO_CENTER * k,
                   sy + math.sin(angle) * ARM_PIVOT_TO_CENTER * k, -angle, k, k, mirrored=True)

        self.place(self.body, 0, center_y, self.body_rot + tilt, k * squash_x, k * squash_y)
        # 그늘은 구를 때 돌지 않는다. 왼쪽을 봐도 빛은 그대로 왼쪽 위에서 오므로 뒤집지 않는다.
        self.body_shade.composite_draw(0, '', self.x, center_y, self.body_shade.w * k * squash_x,
                                       self.body_shade.h * k * squash_y)

        hx, hy = rotated(head_shift, body_h + HEAD_RADIUS * head_k * 0.62)
        self.place(self.head, hx, hy, tilt * 0.6, head_k, head_k)

        # 목도리는 머리와 몸통이 만나는 곳을 덮는다.
        nx, ny = rotated(head_shift * 0.6, body_h * 0.98)
        tail_x = nx - 46 * head_k
        tail_y = ny - 2 * head_k
        rad = self.tail_rot + math.sin(self.phase * 1.3) * 0.08
        self.place(self.tail, tail_x + math.sin(rad) * TAIL_PIVOT_TO_CENTER * head_k,
                   tail_y - math.cos(rad) * TAIL_PIVOT_TO_CENTER * head_k, rad, head_k, head_k)
        self.place(self.scarf, nx, ny, tilt * 0.8, head_k, head_k)

        # 냄비는 머리에 올라타 있다.
        rad = tilt * 0.6 + self.pot_rot
        up = (HEAD_RADIUS * 0.66 + 49) * head_k
        self.place(self.pot, hx - math.sin(rad) * up - 6 * head_k, hy + math.cos(rad) * up, rad, head_k, head_k)
