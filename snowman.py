"""주인공 눈사람.

눈의 양이 곧 크기다. 크기는 큼, 중간, 작음 세 단계이고, 작을수록 빠르고 높이 뛴다.
눈덩이를 던지면 눈이 줄고, 열 구역에서는 녹고, 눈밭 위를 구르면 회복한다. 눈이 0 이 되면 녹아 버린다.
몸은 파츠 이미지 여러 장을 코드로 돌리고 늘려서 움직이는 컷아웃 애니메이션으로 그린다.
"""
import math
import random

from pico2d import get_canvas_width, clamp
from sdl2 import (SDL_KEYDOWN, SDL_KEYUP, SDLK_LEFT, SDLK_RIGHT, SDLK_UP, SDLK_DOWN, SDLK_SPACE,
                  SDLK_1, SDLK_2, SDLK_3, SDLK_MINUS, SDLK_EQUALS)
from transitions import Machine

import asset_loader
import game_framework
import game_world
from effects import Drip
from rules import (PIXEL_PER_METER, GRAVITY_PPS2, GROUND_Y, kmph_to_pps,
                   MAX_SNOW, BIG_SNOW, MIDDLE_SNOW, SIZE_TABLE, ROLL_SPEED_RATE,
                   THROW_COST, THROW_COOLDOWN, HEAT_MELT_PER_SEC, ROLL_RECOVER_PER_SEC)
from snowball import Snowball

STEP_LENGTH_PX = 90  # 걸을 때 한 번 통통 튀며 나아가는 거리(큰 눈사람 기준)
THROW_DURATION = 0.26  # 팔을 젖혔다가 휘두르기까지 걸리는 시간
THROW_RELEASE = 0.55  # 던지는 동작의 이 비율쯤에서 눈덩이가 손을 떠난다.
DRIP_INTERVAL = 0.08  # 열 구역에서 물방울이 떨어지는 간격
MELT_DURATION = 1.2  # 눈이 0 이 되어 녹아내리는 시간
RESTART_DELAY = 2.0  # 녹기 시작해서 다시 시작하기까지의 시간

# 파츠 이미지의 원래 크기를 기준으로 한 값
BASE_SCALE = 0.62
BODY_RADIUS = 112
HEAD_RADIUS = 80
ARM_PIVOT_TO_CENTER = 67
ARM_LENGTH = 140
TAIL_PIVOT_TO_CENTER = 50

# 개발용 단축키. 크기 단계를 바로 바꿔 보는 데 쓴다.
DEBUG_SNOW_KEYS = {SDLK_1: 25, SDLK_2: 50, SDLK_3: MAX_SNOW}
DEBUG_SNOW_STEP = 5


def level_of(snow):
    if snow >= BIG_SNOW:
        return 'BIG'
    if snow >= MIDDLE_SNOW:
        return 'MIDDLE'
    return 'SMALL'


def throw_arm_angle(t):
    """던지는 팔의 각도. t 가 0 에서 1 로 가는 동안 팔을 뒤로 젖혔다가 앞으로 휘두른다."""
    wind_up = 0.35
    if t < wind_up:
        return 0.6 + (2.4 - 0.6) * (t / wind_up)
    u = (t - wind_up) / (1 - wind_up)
    return 2.4 + (-0.2 - 2.4) * (1 - (1 - u) ** 2)


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
        snowman.move_x(snowman.speed())
        snowman.phase += 2.5 * game_framework.frame_time
        if snowman.fall():
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


class Melt:
    """눈이 0 이 되어 녹아내린다. 입력은 더 받지 않는다."""

    def enter(self, snowman):
        snowman.melt_time = 0.0

    def do(self, snowman):
        snowman.melt_time += game_framework.frame_time
        snowman.fall()  # 공중에서 녹으면 땅으로 떨어진다.

    def pose(self, snowman):
        # 몸통이 퍼지며 주저앉으면, 그 위의 머리와 냄비도 따라 내려온다. 팔은 축 늘어진다.
        pose = Pose()
        t = min(1.0, snowman.melt_time / MELT_DURATION)
        pose.squash_x, pose.squash_y = 1 + 0.6 * t, 1 - 0.75 * t
        pose.arm_front = 0.25 - 0.9 * t
        pose.arm_back = 0.2 - 0.9 * t
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

        self.throw_time = -1.0  # 던지는 동작이 시작된 뒤 지난 시간. 던지는 중이 아니면 음수다.
        self.throw_released = False
        self.throw_cooldown = 0.0

        self.in_heat = False  # 이번 프레임에 열 구역 안에 있었는지. 충돌 처리에서 켠다.
        self.drip_timer = 0.0
        self.melt_time = 0.0

        self.body = asset_loader.image('body.png')
        self.body_shade = asset_loader.image('body_shade.png')
        self.head = asset_loader.image('head.png')
        self.pot = asset_loader.image('pot.png')
        self.arm_a = asset_loader.image('arm_a.png')
        self.arm_b = asset_loader.image('arm_b.png')
        self.scarf = asset_loader.image('scarf.png')
        self.tail = asset_loader.image('scarf_tail.png')
        self.shadow = asset_loader.image('shadow.png')

        self.states = {'IDLE': Idle(), 'WALK': Walk(), 'ROLL': Roll(), 'JUMP': Jump(), 'MELT': Melt()}
        self.machine = Machine(
            model=self,
            states=['IDLE', 'WALK', 'ROLL', 'JUMP', 'MELT'],
            transitions=[
                {'trigger': 'stop', 'source': ['WALK', 'ROLL', 'JUMP'], 'dest': 'IDLE'},
                {'trigger': 'walk', 'source': ['IDLE', 'ROLL', 'JUMP'], 'dest': 'WALK'},
                {'trigger': 'roll', 'source': ['IDLE', 'WALK', 'JUMP'], 'dest': 'ROLL'},
                {'trigger': 'jump', 'source': ['IDLE', 'WALK', 'ROLL'], 'dest': 'JUMP'},
                {'trigger': 'melt_down', 'source': ['IDLE', 'WALK', 'ROLL', 'JUMP'], 'dest': 'MELT'},
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

    def on_enter_MELT(self):
        self.states['MELT'].enter(self)

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

    # 눈의 양

    def set_snow(self, amount):
        self.snow = clamp(0, amount, MAX_SNOW)

    def melt(self, amount):
        if self.state == 'MELT':
            return
        self.snow = max(0.0, self.snow - amount)
        if self.snow <= 0:
            self.melt_down()

    def melt_finished(self):
        return self.state == 'MELT' and self.melt_time >= RESTART_DELAY

    # 입력과 상태 전환

    def handle_event(self, event):
        if self.state == 'MELT':
            return
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
            if event.key == SDLK_SPACE:
                self.start_throw()
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

    # 던지기

    def start_throw(self):
        # 구르는 중에는 팔을 쓸 수 없다. 눈이 던질 만큼 없으면 던지지 않는다.
        if self.state == 'ROLL' or self.throw_cooldown > 0 or self.snow <= THROW_COST:
            return
        self.snow -= THROW_COST
        self.throw_time = 0.0
        self.throw_released = False
        self.throw_cooldown = THROW_COOLDOWN

    def hand_position(self):
        """던지는 팔의 손끝 위치. 지금 팔 각도를 그대로 따른다."""
        k = BASE_SCALE * self.scale
        angle = throw_arm_angle(min(1.0, self.throw_time / THROW_DURATION))
        shoulder_x, shoulder_y = BODY_RADIUS * k * 0.66, BODY_RADIUS * k * 1.48
        return (self.x + (shoulder_x + math.cos(angle) * ARM_LENGTH * k) * self.face,
                self.y + shoulder_y + math.sin(angle) * ARM_LENGTH * k)

    def update_throw(self, dt):
        self.throw_cooldown = max(0.0, self.throw_cooldown - dt)
        if self.throw_time < 0:
            return
        self.throw_time += dt
        if not self.throw_released and self.throw_time >= THROW_DURATION * THROW_RELEASE:
            self.throw_released = True
            x, y = self.hand_position()
            ball = Snowball(x, y, self.face, self.scale)
            game_world.add_object(ball, game_world.OBJECT)
            game_world.add_collision_pair('snowball:heater', ball, None)
        if self.throw_time >= THROW_DURATION:
            self.throw_time = -1.0

    # 매 프레임

    def move_x(self, speed):
        moved = speed * game_framework.frame_time
        self.x += self.dir * moved
        return moved

    def fall(self):
        """중력으로 떨어진다. 땅에 닿은 프레임에 True 를 돌려준다."""
        dt = game_framework.frame_time
        if self.y <= GROUND_Y and self.vy <= 0:
            self.y, self.vy = GROUND_Y, 0.0
            return False
        # 이번 프레임의 처음과 끝 속도의 평균으로 움직여야 프레임 속도와 상관없이 같은 높이까지 오른다.
        old_vy = self.vy
        self.vy -= GRAVITY_PPS2 * dt
        self.y += (old_vy + self.vy) / 2 * dt
        if self.y <= GROUND_Y:
            self.y, self.vy = GROUND_Y, 0.0
            return True
        return False

    def update(self):
        dt = game_framework.frame_time

        # 지난 프레임에 열 구역 안에 있었으면 물방울을 떨어뜨린다.
        if self.in_heat and self.state != 'MELT':
            self.drip_timer -= dt
            if self.drip_timer <= 0:
                self.drip_timer = DRIP_INTERVAL
                r = self.body_radius()
                drip = Drip(self.x + random.uniform(-0.8, 0.8) * r, self.y + r * random.uniform(0.6, 1.8))
                game_world.add_object(drip, game_world.OBJECT)
        self.in_heat = False

        self.states[self.state].do(self)
        self.update_throw(dt)

        target = SIZE_TABLE[self.size_level()]['scale']
        self.scale += (target - self.scale) * min(1.0, dt * 8)

        margin = self.body_radius() + 20
        self.x = clamp(margin, self.x, get_canvas_width() - margin)

        moving = self.state not in ('IDLE', 'MELT')
        self.pot_rot += ((0.16 if moving else 0.0) - self.pot_rot) * min(1.0, dt * 8)
        self.tail_rot += ((-0.55 if moving else -0.06) - self.tail_rot) * min(1.0, dt * 6)
        self.land_squash = max(0.0, self.land_squash - dt * 5)

    # 충돌

    def get_bb(self):
        r = self.body_radius()
        return self.x - r, self.y, self.x + r, self.y + 2 * r

    def handle_collision(self, group, other):
        dt = game_framework.frame_time
        if group == 'snowman:heat':
            self.in_heat = True
            self.melt(HEAT_MELT_PER_SEC * dt)
        elif group == 'snowman:snowfield' and self.state == 'ROLL':
            room = MAX_SNOW - self.snow
            if room > 0:
                self.snow += other.give(min(ROLL_RECOVER_PER_SEC * dt, room))

    # 그리기

    def place(self, image, lx, ly, rad=0.0, scale_x=1.0, scale_y=1.0, mirrored=False):
        """오른쪽을 본다고 가정한 위치(lx, ly)에 파츠를 그린다. 왼쪽을 보면 통째로 뒤집는다."""
        flip = 'h' if (self.face == -1) != mirrored else ''
        image.composite_draw(rad * self.face, flip, self.x + lx * self.face, ly,
                             image.w * scale_x, image.h * scale_y)

    def draw(self):
        pose = self.states[self.state].pose(self)
        if self.throw_time >= 0:
            pose.arm_front = throw_arm_angle(min(1.0, self.throw_time / THROW_DURATION))

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
        # 던질 때는 머리 뒤로 젖힌 팔이 가려지지 않도록 맨 마지막에 그린다.
        sx, sy = rotated(BODY_RADIUS * k * 0.66, body_h * 0.48)
        angle = tilt + pose.arm_front
        front_arm = (self.arm_a, sx + math.cos(angle) * ARM_PIVOT_TO_CENTER * k,
                     sy + math.sin(angle) * ARM_PIVOT_TO_CENTER * k, angle, k, k)
        throwing = self.throw_time >= 0
        if not throwing:
            self.place(*front_arm)

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

        if throwing:
            self.place(*front_arm)
