"""눈사람 파츠 PNG 를 코드로 그린다. 표준 라이브러리만 쓴다.

실행하면 ../assets 에 파츠 이미지가 만들어진다. 좌표는 이미지 왼쪽 위가 원점이다.
"""
import math
import os
import struct
import zlib

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

INK = (38, 44, 72)
SNOW = (248, 251, 255)
SNOW_SHADOW = (205, 221, 242)
DIRT = (128, 98, 74)
TWIG = (112, 78, 52)
TWIG_LIGHT = (150, 110, 76)
RED = (196, 52, 58)
RED_DARK = (150, 34, 48)
CREAM = (240, 226, 196)


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        # 투명한 곳의 색도 외곽선 색으로 둔다. 확대/축소할 때 가장자리가 검게 번지는 것을 막는다.
        self.px = [[INK[0], INK[1], INK[2], 0.0] for _ in range(w * h)]

    def paint(self, sdf, color, opacity=1.0, clip=None, box=None):
        """sdf 가 음수인 영역을 color 로 칠한다. color 는 (r, g, b) 또는 (x, y) -> (r, g, b).

        box=(x0, y0, x1, y1) 을 주면 그 사각형 안만 검사한다. 큰 배경 그림에서 작은 도형을 빨리 그릴 때 쓴다.
        """
        x0, y0, x1, y1 = (0, 0, self.w, self.h) if box is None else box
        x0, y0 = max(0, int(x0) - 2), max(0, int(y0) - 2)
        x1, y1 = min(self.w, int(x1) + 3), min(self.h, int(y1) + 3)
        for y in range(y0, y1):
            for x in range(x0, x1):
                d = sdf(x + 0.5, y + 0.5)
                if d > 0.7:
                    continue
                cover = clamp01(0.5 - d) * opacity
                if clip is not None:
                    cover *= clamp01(0.5 - clip(x + 0.5, y + 0.5))
                if cover <= 0.0:
                    continue
                c = color(x + 0.5, y + 0.5) if callable(color) else color
                p = self.px[y * self.w + x]
                a = cover + p[3] * (1.0 - cover)
                for i in range(3):
                    p[i] = (c[i] * cover + p[i] * p[3] * (1.0 - cover)) / a
                p[3] = a

    def save(self, name):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)
            for x in range(self.w):
                p = self.px[y * self.w + x]
                raw += bytes((round(p[0]), round(p[1]), round(p[2]), round(p[3] * 255)))
        write_png(os.path.join(OUT_DIR, name), self.w, self.h, bytes(raw))


def write_png(path, w, h, raw):
    def chunk(tag, data):
        body = tag + data
        return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body))

    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)))
        f.write(chunk(b'IDAT', zlib.compress(raw, 9)))
        f.write(chunk(b'IEND', b''))


def clamp01(v):
    return max(0.0, min(1.0, v))


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


# ---------- 도형 ----------

def circle(cx, cy, r, wobble=0.0, seed=0.0):
    def f(x, y):
        dx, dy = x - cx, y - cy
        a = math.atan2(dy, dx)
        w = math.sin(3 * a + seed) * 0.6 + math.sin(5 * a + seed * 2) * 0.3 + math.sin(9 * a + seed * 3) * 0.1
        return math.hypot(dx, dy) - r * (1.0 + wobble * w)
    return f


def ellipse(cx, cy, rx, ry):
    def f(x, y):
        px, py = x - cx, y - cy
        k0 = math.hypot(px / rx, py / ry)
        k1 = math.hypot(px / (rx * rx), py / (ry * ry))
        return k0 * (k0 - 1.0) / k1 if k1 > 0 else -min(rx, ry)
    return f


def stroke(points, r0, r1=None):
    """점들을 잇는 굵은 선. 굵기는 r0 에서 r1 로 변한다."""
    r1 = r0 if r1 is None else r1
    lengths = [math.dist(points[i], points[i + 1]) for i in range(len(points) - 1)]
    total = sum(lengths)

    def f(x, y):
        best = 1e9
        walked = 0.0
        for i, length in enumerate(lengths):
            ax, ay = points[i]
            bx, by = points[i + 1]
            vx, vy = bx - ax, by - ay
            t = clamp01(((x - ax) * vx + (y - ay) * vy) / (length * length))
            r = r0 + (r1 - r0) * (walked + t * length) / total
            best = min(best, math.hypot(x - ax - vx * t, y - ay - vy * t) - r)
            walked += length
        return best
    return f


def polygon(points):
    def f(x, y):
        d = 1e18
        inside = False
        n = len(points)
        for i in range(n):
            ax, ay = points[i]
            bx, by = points[(i + 1) % n]
            vx, vy = bx - ax, by - ay
            t = clamp01(((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy))
            d = min(d, (x - ax - vx * t) ** 2 + (y - ay - vy * t) ** 2)
            if (ay > y) != (by > y) and x < vx * (y - ay) / (by - ay) + ax:
                inside = not inside
        return -math.sqrt(d) if inside else math.sqrt(d)
    return f


def union(*shapes):
    return lambda x, y: min(s(x, y) for s in shapes)


def grow(shape, amount):
    return lambda x, y: shape(x, y) - amount


def outlined(canvas, shape, color, width, clip=None):
    canvas.paint(grow(shape, width), INK, clip=clip)
    canvas.paint(shape, color, clip=clip)


def snow_color(cx, cy, r):
    """왼쪽 위에서 빛이 오는 눈덩이. 그늘 경계를 살짝 흔들어 손으로 칠한 느낌을 낸다."""
    def f(x, y):
        nx, ny = (x - cx) / r, (y - cy) / r
        light = nx * -0.55 + ny * -0.7 + math.sin(x * 0.09 + y * 0.05) * 0.04
        return mix(SNOW_SHADOW, SNOW, clamp01((light + 0.34) * 7.0))
    return f


# ---------- 파츠 ----------

def draw_button(canvas, cx, cy, r, color):
    canvas.paint(circle(cx, cy, r + 3), INK)
    canvas.paint(circle(cx, cy, r), color)
    canvas.paint(circle(cx - r * 0.2, cy - r * 0.25, r * 0.28), mix(color, (255, 255, 255), 0.55))
    hole = r * 0.3
    canvas.paint(circle(cx - hole, cy + hole * 0.6, 2.2), INK)
    canvas.paint(circle(cx + hole, cy + hole * 0.6, 2.2), INK)


def make_body():
    s, c, r = 256, 128, 112
    canvas = Canvas(s, s)
    ball = circle(c, c, r, 0.012, 1.0)
    outlined(canvas, ball, SNOW, 5)

    # 굴러갈 때 도는 것이 보이도록 흙 얼룩과 잔가지를 둔다.
    for x, y, pr, seed in ((86, 186, 19, 1.2), (176, 104, 14, 2.6), (150, 204, 10, 4.1),
                           (62, 92, 11, 5.3), (128, 54, 8, 0.4)):
        patch = circle(x, y, pr, 0.2, seed)
        outlined(canvas, patch, DIRT, 2, clip=ball)
        canvas.paint(circle(x - pr * 0.25, y - pr * 0.25, pr * 0.35), mix(DIRT, SNOW, 0.3), 0.7, clip=ball)
    for points in (((186, 150), (210, 138)), ((104, 128), (120, 148)), ((42, 142), (60, 156))):
        outlined(canvas, stroke(points, 3.2, 2.0), TWIG, 1.5, clip=ball)
    canvas.save('body.png')

    # 그늘을 몸통에 그려 넣으면 구를 때 빛 방향까지 같이 돈다. 그래서 돌지 않는 이미지로 따로 둔다.
    shade = Canvas(s, s)

    def shade_area(x, y):
        nx, ny = (x - c) / r, (y - c) / r
        light = nx * -0.55 + ny * -0.7 + math.sin(x * 0.09 + y * 0.05) * 0.04
        return max(ball(x, y), (light + 0.34) * 30)

    shade.paint(shade_area, (120, 152, 208), 0.34)
    shade.save('body_shade.png')


def make_head():
    s, c, r = 184, 92, 80
    canvas = Canvas(s, s)
    outlined(canvas, circle(c, c, r, 0.012, 3.0), snow_color(c, c, r), 5)

    # 오른쪽을 보는 3/4 얼굴이라 먼 쪽 눈을 더 작게 그린다.
    canvas.paint(ellipse(c - 28, c + 22, 13, 8), (244, 170, 170), 0.55)
    draw_button(canvas, c - 8, c - 18, 16, (206, 54, 60))
    draw_button(canvas, c + 42, c - 22, 12, (58, 104, 190))

    nose = polygon(((c + 12, c - 4), (c + 15, c + 20), (c + 73, c + 10)))
    outlined(canvas, nose, (238, 136, 48), 3)
    canvas.paint(stroke(((c + 30, c + 3), (c + 36, c + 9)), 1.4), (178, 86, 26))
    canvas.paint(stroke(((c + 46, c + 7), (c + 50, c + 12)), 1.4), (178, 86, 26))

    canvas.paint(stroke(((c - 28, c + 36), (c - 6, c + 50), (c + 22, c + 48), (c + 42, c + 32)), 3.6, 2.6), INK)
    canvas.save('head.png')


def make_pot():
    w, h = 170, 116
    canvas = Canvas(w, h)
    # 왼쪽 위가 찌그러진 냄비를 뒤집어 쓴 모양.
    shell = polygon(((30, 98), (140, 98), (132, 18), (66, 14), (58, 34), (40, 42)))
    rim = stroke(((22, 100), (148, 100)), 7)
    handle = stroke(((136, 58), (158, 54)), 5.5, 7)
    silhouette = union(shell, rim, handle)
    canvas.paint(grow(silhouette, 4), INK)

    def metal(x, y):
        t = clamp01((x - 30) / 110)
        base = mix((198, 208, 222), (116, 128, 150), t)
        if 52 < x + y * 0.12 < 66:
            return mix(base, (240, 245, 250), 0.75)
        return base

    canvas.paint(shell, metal)
    canvas.paint(handle, (92, 100, 118))
    canvas.paint(rim, (150, 160, 178))
    canvas.paint(stroke(((30, 96), (140, 96)), 1.2), (214, 222, 232))
    canvas.paint(stroke(((62, 40), (80, 30), (96, 32)), 2.4, 1.4), (108, 118, 138))
    for x in (48, 122):
        canvas.paint(circle(x, 74, 3), INK)
    canvas.save('pot.png')


def make_arm(name, branch, tip):
    w, h = 150, 70
    canvas = Canvas(w, h)
    main = stroke(((8, 38), (58, 35), (100, 24), tip), 6.5, 2.6)
    fork = stroke(((72, 32), (102, 44), branch), 4.2, 2.2)
    twig = union(main, fork)
    outlined(canvas, twig, lambda x, y: mix(TWIG_LIGHT, TWIG, clamp01((y % 9) / 5)), 2.5)
    canvas.save(name)


def knit(x, y):
    return RED if int(x / 11 + y / 26) % 2 == 0 else RED_DARK


def make_scarf():
    w, h = 176, 62
    canvas = Canvas(w, h)
    band = stroke(((20, 22), (56, 34), (88, 38), (120, 34), (156, 22)), 16)
    outlined(canvas, band, knit, 4)
    canvas.save('scarf.png')


def make_scarf_tail():
    w, h = 64, 124
    canvas = Canvas(w, h)
    for x in (18, 28, 38, 48):
        outlined(canvas, stroke(((x, 96), (x - 1, 116)), 3), CREAM, 1.5)
    tail = stroke(((32, 12), (31, 92)), 15, 18)

    def color(x, y):
        if 68 < y < 80:
            return CREAM
        return knit(x, y)

    outlined(canvas, tail, color, 4)
    canvas.save('scarf_tail.png')


def make_shadow():
    w, h = 200, 40
    canvas = Canvas(w, h)
    for i in range(6):
        canvas.paint(ellipse(100, 20, 96 - i * 8, 18 - i * 1.5), (60, 84, 130), 0.07)
    canvas.save('shadow.png')


IRON_LIGHT = (104, 98, 118)
IRON_DARK = (54, 50, 66)
FIRE_RED = (232, 82, 46)
FIRE_ORANGE = (250, 150, 50)
FIRE_YELLOW = (255, 228, 120)
ICE = (188, 222, 248)


def make_snowball():
    s, c, r = 48, 24, 19
    canvas = Canvas(s, s)
    outlined(canvas, circle(c, c, r, 0.03, 2.0), snow_color(c, c, r), 3)
    canvas.paint(circle(c - 7, c - 7, 4), (255, 255, 255), 0.8)
    canvas.save('snowball.png')


def make_heater(name, frozen):
    """배가 불룩한 무쇠 난로. 위가 뚫려 있어 불꽃이 솟는다. frozen 이면 꺼지고 얼어붙은 모습."""
    w, h = 150, 190
    canvas = Canvas(w, h)
    legs = union(stroke(((46, 168), (36, 184)), 6), stroke(((104, 168), (114, 184)), 6))
    outlined(canvas, legs, IRON_DARK, 3)

    belly = ellipse(75, 120, 58, 54)
    neck = polygon(((34, 66), (116, 66), (126, 100), (24, 100)))
    body = union(belly, neck)

    def iron(x, y):
        t = clamp01((x - 20) / 110)
        base = mix(IRON_LIGHT, IRON_DARK, t)
        if 40 < x - y * 0.18 < 50:
            return mix(base, (170, 166, 186), 0.6)
        return base

    outlined(canvas, body, iron, 4)
    lip = stroke(((20, 64), (130, 64)), 9)
    outlined(canvas, lip, (82, 76, 96), 3)
    canvas.paint(ellipse(75, 64, 46, 5), (110, 70, 60) if frozen else FIRE_ORANGE)

    window = stroke(((62, 124), (88, 124)), 17)
    if frozen:
        outlined(canvas, window, (44, 54, 84), 3)
    else:
        def glow(x, y):
            return mix(FIRE_YELLOW, FIRE_RED, clamp01((y - 108) / 34))
        outlined(canvas, window, glow, 3)
    for x in (66, 75, 84):
        canvas.paint(stroke(((x, 108), (x, 140)), 1.6), INK, clip=window)
    for x, y in ((36, 108), (114, 108), (44, 150), (106, 150)):
        canvas.paint(circle(x, y, 3), INK)

    if frozen:
        # 서리가 덮이고, 눈이 소복이 쌓이고, 고드름이 매달린다.
        canvas.paint(body, (210, 232, 252), 0.38)
        for x0, x1, length in ((34, 46, 22), (58, 66, 14), (96, 106, 26), (118, 126, 12)):
            outlined(canvas, polygon(((x0, 68), (x1, 68), ((x0 + x1) / 2, 68 + length))), ICE, 2)
        cap = union(circle(36, 58, 14, 0.1, 1.0), circle(60, 52, 18, 0.1, 2.0), circle(88, 52, 17, 0.1, 3.0),
                    circle(114, 58, 14, 0.1, 4.0), stroke(((24, 62), (126, 62)), 7))
        outlined(canvas, cap, snow_color(75, 50, 50), 3)
    canvas.save(name)


def make_flame():
    w, h = 90, 120
    canvas = Canvas(w, h)
    outer = union(stroke(((45, 88), (40, 36), (52, 6)), 30, 2), circle(45, 90, 28))
    outlined(canvas, outer, lambda x, y: mix(FIRE_ORANGE, FIRE_RED, clamp01((y - 30) / 80)), 3)
    canvas.paint(union(stroke(((45, 96), (42, 62), (49, 38)), 17, 2), circle(45, 98, 16)), FIRE_ORANGE)
    canvas.paint(union(stroke(((45, 102), (44, 82), (47, 66)), 9, 1.5), circle(45, 104, 8)), FIRE_YELLOW)
    canvas.save('flame.png')


def make_heat():
    """난로 열 구역에 겹쳐 그리는 아지랑이.

    열의 세기는 구역 안 어디서나 같으므로 안쪽은 고르게 칠하고, 경계가 보이도록 가장자리에서만 빠르게 옅어진다.
    """
    w, h = 64, 256
    canvas = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            side = clamp01((1.0 - abs(x + 0.5 - w / 2) / (w / 2)) / 0.12)
            side = side * side * (3 - 2 * side)
            low = ((y + 0.5) / h) ** 1.2
            canvas.px[y * w + x] = [255, 136, 70, 0.36 * side * low]
    canvas.save('heat.png')


def make_snowfield():
    """난로를 끈 자리에 생기는 눈밭. 아래쪽은 이미지 밖으로 이어져 외곽선이 생기지 않는다."""
    w, h = 320, 56
    canvas = Canvas(w, h)
    bumps = [circle(x, h + r - 34 + dy, r, 0.05, x * 0.1) for x, r, dy in
             ((40, 30, 8), (86, 40, 0), (140, 44, -4), (192, 42, -2), (244, 38, 2), (284, 28, 10))]
    mound = union(*bumps)
    outlined(canvas, mound, lambda x, y: mix(SNOW, SNOW_SHADOW, clamp01((y - 18) / 40)), 3)
    for x, y in ((70, 30), (150, 22), (210, 28), (262, 36)):
        canvas.paint(stroke(((x, y), (x + 9, y - 2)), 1.6), (170, 200, 236))
    canvas.save('snowfield.png')


def make_drop():
    w, h = 16, 22
    canvas = Canvas(w, h)
    outlined(canvas, union(stroke(((8, 15), (8, 4)), 5, 1.2), circle(8, 15, 5)), (150, 200, 245), 1.5)
    canvas.paint(circle(6.5, 14, 1.6), (230, 244, 255))
    canvas.save('drop.png')


def make_spirit():
    """불꽃 정령. 오른쪽을 보는 화난 얼굴의 불꽃."""
    w, h = 110, 130
    canvas = Canvas(w, h)
    body = union(stroke(((55, 94), (50, 46), (64, 8)), 36, 3), circle(55, 94, 33))
    outlined(canvas, body, lambda x, y: mix((252, 166, 60), (226, 70, 50), clamp01((y - 20) / 100)), 3.5)
    canvas.paint(union(stroke(((55, 104), (53, 70), (60, 46)), 20, 2), circle(55, 104, 19)), (255, 200, 90))
    for ex in (48, 74):
        canvas.paint(ellipse(ex, 90, 9, 11), INK)
        canvas.paint(ellipse(ex, 90, 7, 9), (255, 255, 255))
        canvas.paint(circle(ex + 3, 92, 4.5), INK)
    canvas.paint(stroke(((37, 74), (56, 82)), 2.6), INK)
    canvas.paint(stroke(((86, 72), (66, 81)), 2.6), INK)
    canvas.paint(stroke(((52, 110), (60, 106), (70, 110)), 2.2), INK)
    canvas.save('spirit.png')


def make_fireball():
    s, c = 44, 22
    canvas = Canvas(s, s)
    outlined(canvas, circle(c, c, 14, 0.12, 1.0), lambda x, y: mix(FIRE_ORANGE, FIRE_RED, clamp01((y - 8) / 28)), 3)
    canvas.paint(circle(c - 2, c - 2, 7, 0.1, 2.0), FIRE_YELLOW)
    canvas.save('fireball.png')


def make_steam():
    """김. 가운데가 진하고 가장자리로 갈수록 투명해지는 둥근 덩어리."""
    s = 64
    canvas = Canvas(s, s)
    for y in range(s):
        for x in range(s):
            d = math.hypot(x + 0.5 - s / 2, y + 0.5 - s / 2) / (s / 2)
            canvas.px[y * s + x] = [250, 252, 255, 0.8 * clamp01(1 - d) ** 1.5]
    canvas.save('steam.png')


def make_frost():
    """난로를 끈 자리의 얼어붙은 땅. 땅 위에 납작하게 깔린다."""
    w, h = 512, 44
    canvas = Canvas(w, h)
    patch = ellipse(256, 24, 250, 17)
    canvas.paint(grow(patch, 2), (178, 206, 236))
    canvas.paint(patch, lambda x, y: mix((244, 249, 255), (214, 230, 248), clamp01((y - 10) / 26)))
    for points in (((120, 20), (150, 26), (170, 22)), ((300, 30), (330, 24), (352, 28)), ((420, 22), (440, 28))):
        canvas.paint(stroke(points, 1.2), (176, 204, 234))
    canvas.save('frost.png')


# ---------- 배경 (스테이지 1: 겨울이 사라진 마을) ----------
# 화면은 1280x720 이고 땅은 아래쪽 96 픽셀이다. 가로로 스크롤되는 층은 1280 픽셀마다 이어지도록
# 사인 곡선의 주기를 1280 의 약수로 맞춘다.

SCREEN_W, SCREEN_H, GROUND_TOP = 1280, 720, 96
TAU = math.pi * 2


def wave(x, n, phase=0.0):
    """1280 픽셀 안에 n 번 반복되는 사인 곡선. 층을 이어 붙여도 이음매가 생기지 않는다."""
    return math.sin(TAU * n * x / SCREEN_W + phase)


def fill_below(canvas, top_of, color_of):
    """열마다 top_of(x) 아래를 칠한다. 경계 픽셀은 반투명하게 해서 계단을 줄인다."""
    for x in range(canvas.w):
        top = top_of(x + 0.5)
        for y in range(max(0, int(top)), canvas.h):
            c = color_of(x, y, top)
            canvas.px[y * canvas.w + x] = [c[0], c[1], c[2], clamp01(y + 1 - top)]


def make_sky():
    """움직이지 않는 하늘과 땅. 땅에는 무늬를 넣지 않는다. 무늬가 있으면 스크롤할 때 멈춰 보인다."""
    w, h = SCREEN_W, SCREEN_H
    canvas = Canvas(w, h)
    horizon = h - GROUND_TOP
    for y in range(h):
        if y < horizon:
            c = mix((124, 170, 222), (242, 230, 208), clamp01(y / horizon) ** 1.3)
        else:
            c = mix((150, 146, 104), (116, 102, 80), clamp01((y - horizon) / GROUND_TOP))
        for x in range(w):
            canvas.px[y * w + x] = [c[0], c[1], c[2], 1.0]
    canvas.save('bg_sky.png')


def make_far_hills():
    canvas = Canvas(SCREEN_W, 260)
    fill_below(canvas, lambda x: 100 + 34 * wave(x, 2, 0.8) + 12 * wave(x, 5),
               lambda x, y, top: mix((202, 210, 200), (180, 192, 182), clamp01((y - top) / 50)))
    canvas.save('bg_far.png')


def draw_house(canvas, cx, base, w, h, roof_h, wall, roof):
    left, right, top = cx - w / 2, cx + w / 2, base - h
    box = (left - 14, top - roof_h - 30, right + 14, base)
    canvas.paint(polygon(((left, base), (right, base), (right, top), (left, top))), wall, box=box)
    chimney_x = cx + w * 0.22
    canvas.paint(polygon(((chimney_x, top - roof_h * 0.4), (chimney_x + 14, top - roof_h * 0.4),
                          (chimney_x + 14, top - roof_h * 0.4 - 30), (chimney_x, top - roof_h * 0.4 - 30))),
                 mix(roof, (60, 50, 50), 0.3), box=box)
    canvas.paint(polygon(((left - 12, top + 2), (right + 12, top + 2), (cx, top - roof_h))), roof, box=box)
    canvas.paint(stroke(((left - 12, top + 2), (right + 12, top + 2)), 2.5), mix(roof, (40, 30, 30), 0.35), box=box)
    # 창문마다 난로 불빛이 새어 나온다.
    for wx in (cx - w * 0.25, cx + w * 0.25):
        window = polygon(((wx - 9, top + 18), (wx + 9, top + 18), (wx + 9, top + 36), (wx - 9, top + 36)))
        canvas.paint(grow(window, 2), mix(wall, (60, 50, 50), 0.4), box=box)
        canvas.paint(window, (255, 208, 120), box=box)
    door = polygon(((cx - 8, base), (cx + 8, base), (cx + 8, base - 28), (cx - 8, base - 28)))
    canvas.paint(door, mix(roof, (50, 40, 40), 0.45), box=box)


def make_village():
    canvas = Canvas(SCREEN_W, 240)

    def hill_top(x):
        return 176 + 12 * wave(x, 3, 1.7) + 6 * wave(x, 7)

    fill_below(canvas, hill_top, lambda x, y, top: mix((178, 190, 150), (160, 174, 136), clamp01((y - top) / 40)))
    walls = ((224, 206, 178), (208, 194, 174), (230, 216, 190))
    roofs = ((170, 98, 86), (124, 114, 146), (154, 122, 84))
    for i, (cx, w, h, roof_h) in enumerate(((110, 92, 70, 40), (300, 120, 82, 52), (520, 100, 66, 44),
                                            (760, 130, 90, 56), (1000, 96, 72, 42), (1190, 110, 76, 48))):
        draw_house(canvas, cx, hill_top(cx) + 8, w, h, roof_h, walls[i % 3], roofs[i % 3])
    canvas.save('bg_village.png')


def make_near_hills():
    canvas = Canvas(SCREEN_W, 170)

    def hill_top(x):
        return 112 + 14 * wave(x, 3, 2.2) + 8 * wave(x, 8, 0.5)

    fill_below(canvas, hill_top, lambda x, y, top: mix((154, 168, 114), (138, 150, 102), clamp01((y - top) / 40)))
    bark = (108, 90, 74)
    for tx in (180, 470, 690, 1050):
        base = hill_top(tx) + 6
        trunk = stroke(((tx, base), (tx - 3, base - 46), (tx + 4, base - 84)), 5, 2)
        branches = union(stroke(((tx - 2, base - 40), (tx - 26, base - 66)), 2.6, 1.2),
                         stroke(((tx + 1, base - 58), (tx + 24, base - 80)), 2.4, 1.1),
                         stroke(((tx - 1, base - 70), (tx - 14, base - 92)), 2, 1))
        canvas.paint(union(trunk, branches), bark, box=(tx - 40, base - 100, tx + 40, base + 4))
    canvas.save('bg_near.png')


def make_ground_details():
    """땅 위의 풀, 자갈, 녹은 눈 웅덩이. 화면 속도 그대로 스크롤되어 움직임이 느껴지게 한다."""
    import random
    w, h = SCREEN_W, GROUND_TOP
    canvas = Canvas(w, h)
    rng = random.Random(7)
    items = [(rng.choice('ggpppm'), rng.uniform(0, w), rng.uniform(8, h - 8)) for _ in range(46)]
    items += [('w', x, y) for x, y in ((160, 60), (610, 40), (980, 72))]
    for kind, x0, y in items:
        for x in (x0 - w, x0, x0 + w):  # 가장자리에 걸친 것은 반대쪽에도 그려 이음매를 없앤다.
            if not -40 < x < w + 40:
                continue
            box = (x - 40, y - 16, x + 40, y + 10)
            if kind == 'g':
                tuft = union(stroke(((x, y), (x - 5, y - 10)), 1.6, 0.8), stroke(((x, y), (x + 1, y - 12)), 1.6, 0.8),
                             stroke(((x, y), (x + 6, y - 9)), 1.6, 0.8))
                canvas.paint(tuft, (108, 126, 72), box=box)
            elif kind == 'p':
                canvas.paint(ellipse(x, y, 4, 2.6), (152, 142, 126), box=box)
                canvas.paint(ellipse(x - 1, y - 1, 1.6, 1), (196, 188, 172), box=box)
            elif kind == 'm':
                canvas.paint(ellipse(x, y, 18, 4), (120, 104, 82), 0.5, box=box)
            else:
                canvas.paint(ellipse(x, y, 34, 6), (138, 124, 100), box=box)
                canvas.paint(ellipse(x, y, 31, 4.5), (170, 196, 214), box=box)
                canvas.paint(stroke(((x - 14, y - 1), (x + 4, y - 2)), 1), (226, 238, 246), box=box)
    canvas.save('bg_ground.png')


JOBS = {
    'body': make_body,
    'head': make_head,
    'pot': make_pot,
    'arm': lambda: (make_arm('arm_a.png', (138, 50), (140, 10)), make_arm('arm_b.png', (130, 56), (142, 18))),
    'scarf': lambda: (make_scarf(), make_scarf_tail()),
    'shadow': make_shadow,
    'snowball': make_snowball,
    'heater': lambda: (make_heater('heater_on.png', frozen=False), make_heater('heater_off.png', frozen=True)),
    'flame': make_flame,
    'heat': make_heat,
    'snowfield': make_snowfield,
    'drop': make_drop,
    'spirit': make_spirit,
    'fireball': make_fireball,
    'steam': make_steam,
    'frost': make_frost,
    'bg': lambda: (make_sky(), make_far_hills(), make_village(), make_near_hills(), make_ground_details()),
}


def main():
    """인자 없이 실행하면 전부, 이름을 주면 그것만 만든다. 예: python make_parts.py spirit bg"""
    import sys
    os.makedirs(OUT_DIR, exist_ok=True)
    names = sys.argv[1:] or list(JOBS)
    for name in names:
        JOBS[name]()


if __name__ == '__main__':
    main()
