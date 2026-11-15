import time

running = False
stack = []
frame_time = 0.0

# 창을 끌거나 잠깐 멈췄다 돌아오면 한 프레임 시간이 크게 튄다.
# 그때 눈사람이 순간이동하거나 땅을 뚫지 않도록 한 프레임 시간의 최댓값을 둔다.
MAX_FRAME_TIME = 0.1


def change_mode(mode):
    if stack:
        stack.pop().finish()
    stack.append(mode)
    mode.init()


def push_mode(mode):
    if stack:
        stack[-1].pause()
    stack.append(mode)
    mode.init()


def pop_mode():
    if stack:
        stack.pop().finish()
    if stack:
        stack[-1].resume()
    else:
        quit()


def quit():
    global running
    running = False


def run(start_mode):
    global running, stack, frame_time
    running = True
    stack = [start_mode]
    try:
        start_mode.init()

        frame_time = 0.0
        current_time = time.time()
        while running:
            stack[-1].handle_events()
            stack[-1].update()
            stack[-1].render()
            now = time.time()
            frame_time = min(now - current_time, MAX_FRAME_TIME)
            current_time = now
    finally:
        while stack:
            stack.pop().finish()
        running = False
