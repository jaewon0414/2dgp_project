BACKGROUND, OBJECT, UI = 0, 1, 2

world = [[], [], []]  # 0: 배경, 1: 게임 객체, 2: UI


def add_object(o, depth=OBJECT):
    world[depth].append(o)


def remove_object(o):
    for layer in world:
        if o in layer:
            layer.remove(o)
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
