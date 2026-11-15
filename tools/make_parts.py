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

    def paint(self, sdf, color, opacity=1.0, clip=None):
        """sdf 가 음수인 영역을 color 로 칠한다. color 는 (r, g, b) 또는 (x, y) -> (r, g, b)."""
        for y in range(self.h):
            for x in range(self.w):
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


def make_background():
    # 게임 화면(1280x720)과 같은 크기로 만든다. 땅은 아래쪽 96 픽셀이다.
    w, h = 1280, 720
    canvas = Canvas(w, h)
    ground_y = h - 96
    for y in range(h):
        for x in range(w):
            sky = mix((126, 172, 222), (222, 236, 248), clamp01(y / ground_y))
            far = ground_y - 74 - math.sin(x * 0.009 + 0.8) * 34 - math.sin(x * 0.023) * 12
            near = ground_y - 22 - math.sin(x * 0.014 + 2.2) * 15
            if y > ground_y:
                color = mix((246, 250, 255), (214, 228, 245), clamp01((y - ground_y) / 96))
            elif y > near:
                color = (232, 241, 251)
            elif y > far:
                color = (200, 218, 238)
            else:
                color = sky
            canvas.px[y * w + x] = [color[0], color[1], color[2], 1.0]
    canvas.save('background.png')


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    make_body()
    make_head()
    make_pot()
    make_arm('arm_a.png', (138, 50), (140, 10))
    make_arm('arm_b.png', (130, 56), (142, 18))
    make_scarf()
    make_scarf_tail()
    make_shadow()
    make_background()


if __name__ == '__main__':
    main()
