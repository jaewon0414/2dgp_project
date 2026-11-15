BACKGROUND, GROUND, OBJECT, UI = 0, 1, 2, 3

world = [[], [], [], []]  # 0: 배경, 1: 땅에 깔리는 것(열 구역, 눈밭), 2: 게임 객체, 3: UI


def add_object(o, depth=OBJECT):
    world[depth].append(o)


def remove_object(o):
    for layer in world:
        if o in layer:
            layer.remove(o)
            remove_collision_object(o)
            return


def update():
    for layer in world:
        for o in layer[:]:
            o.update()


def render():
    for layer in world:
        for o in layer[:]:
            o.draw()


def clear():
    for layer in world:
        layer.clear()
    collision_pairs.clear()


# ---------- 충돌 ----------

# 'a:b' 이름의 그룹마다 [a 쪽 객체들, b 쪽 객체들] 을 두고, 두 쪽끼리만 충돌을 검사한다.
collision_pairs = {}


def add_collision_pair(group, a, b):
    if group not in collision_pairs:
        collision_pairs[group] = [[], []]
    if a is not None:
        collision_pairs[group][0].append(a)
    if b is not None:
        collision_pairs[group][1].append(b)


def remove_collision_object(o):
    for group_a, group_b in collision_pairs.values():
        if o in group_a:
            group_a.remove(o)
        if o in group_b:
            group_b.remove(o)


def collide(a, b):
    left_a, bottom_a, right_a, top_a = a.get_bb()
    left_b, bottom_b, right_b, top_b = b.get_bb()
    if left_a > right_b:
        return False
    if right_a < left_b:
        return False
    if top_a < bottom_b:
        return False
    if bottom_a > top_b:
        return False
    return True


def handle_collisions():
    for group, (group_a, group_b) in collision_pairs.items():
        for a in group_a[:]:
            for b in group_b[:]:
                # 앞의 충돌 처리에서 지워진 객체는 건너뛴다. (눈덩이 하나가 두 번 맞지 않게)
                if a not in group_a or b not in group_b:
                    continue
                if collide(a, b):
                    a.handle_collision(group, b)
                    b.handle_collision(group, a)
