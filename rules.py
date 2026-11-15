"""게임 규칙과 수치를 한곳에 모은다. 플레이해 보면서 여기 값만 바꾸면 된다."""

# ---------- 세계 ----------

PIXEL_PER_METER = 100.0  # 100 픽셀이 1 m 다. 큰 눈사람의 키가 2.8 m 쯤 된다.
GRAVITY_PPS2 = 20.0 * PIXEL_PER_METER  # 실제 중력(9.8)보다 세게 해서 점프가 둥둥 뜨지 않게 한다.
GROUND_Y = 74  # 땅 위에 선 물체의 발밑 높이


def kmph_to_pps(kmph):
    return kmph * 1000.0 / 3600.0 * PIXEL_PER_METER


# ---------- 눈의 양과 크기 ----------

MAX_SNOW = 100
BIG_SNOW = 67  # 눈이 이 값 이상이면 큼
MIDDLE_SNOW = 34  # 이 값 이상이면 중간, 그보다 적으면 작음

# 크기 단계별 수치. 작을수록 빠르고 높이 뛴다.
SIZE_TABLE = {
    'BIG': {'scale': 1.0, 'speed_kmph': 6.0, 'jump_m': 1.0},
    'MIDDLE': {'scale': 0.78, 'speed_kmph': 8.0, 'jump_m': 1.4},
    'SMALL': {'scale': 0.55, 'speed_kmph': 10.0, 'jump_m': 1.8},
}
ROLL_SPEED_RATE = 1.3  # 구르면 걷기보다 빠르다.

# ---------- 던지기 ----------

THROW_COST = 5  # 눈덩이 하나에 드는 눈. 눈이 이보다 많을 때만 던질 수 있어서 던지다 녹아 죽지는 않는다.
THROW_COOLDOWN = 0.35  # 다음 눈덩이를 던지기까지 기다리는 시간(초)
# 눈덩이가 날아가는 거리는 열 구역보다 짧아야 한다. 그래야 난로를 맞히려면 열 구역에 들어가야 한다.
THROW_SPEED_X = 380  # 던진 눈덩이의 처음 가로 속도(px/s)
THROW_SPEED_Y = 120  # 처음 세로 속도(px/s). 살짝 위로 던져서 포물선을 그린다.
SNOWBALL_GRAVITY = 1100  # 눈덩이에 걸리는 중력(px/s^2)
SNOWBALL_RADIUS = 16  # 큰 눈사람이 던지는 눈덩이의 반지름. 몸이 작으면 눈덩이도 작아진다.

# ---------- 난로와 열 ----------

HEATER_HP = 3  # 난로 하나를 끄는 데 필요한 눈덩이 수
HEAT_RANGE = 380  # 난로 중심에서 좌우로 열이 닿는 거리(px)
HEAT_HEIGHT = 330  # 열 구역의 높이(px)
HEAT_MELT_PER_SEC = 4  # 열 구역 안에서 1초에 녹는 눈

# ---------- 눈밭 ----------

# 눈밭 하나에 들어 있는 눈. 처음엔 던지기 15 의 두 배인 30 이었지만, 열을 버티는 값(6 쯤)과
# 빗나간 눈덩이까지 치면 끄는 데 25~30 이 들어서 남는 게 없었다. 끄면 확실히 이득이 되게 40 으로 올렸다.
SNOWFIELD_SNOW = 40
SNOWFIELD_WIDTH = 420  # 처음 생긴 눈밭의 너비(px). 눈을 가져갈수록 좁아진다.
ROLL_RECOVER_PER_SEC = 8  # 눈밭 위를 구를 때 1초에 회복하는 눈

# ---------- 난로 종류 ----------
# small: 길 중간의 작은 난로. 끌지 말지 고른다.
# goal: 스테이지 끝의 큰 난로. 끄면 스테이지 클리어다.
HEATER_KINDS = {
    'small': {'hp': HEATER_HP, 'scale': 1.0, 'heat_range': HEAT_RANGE, 'heat_height': HEAT_HEIGHT,
              'field_snow': SNOWFIELD_SNOW, 'field_width': SNOWFIELD_WIDTH},
    'goal': {'hp': 6, 'scale': 1.5, 'heat_range': 520, 'heat_height': 460,
             'field_snow': 45, 'field_width': 560},
}

# ---------- 불꽃 정령 ----------

SPIRIT_HP = 2  # 쓰러뜨리는 데 필요한 눈덩이 수
SPIRIT_SPEED = 120  # 움직이는 빠르기(px/s)
# 정령이 유지하는 거리는 눈덩이가 닿는 곳에 맞췄다. 작은 눈사람의 눈덩이는 250px 쯤 날아간다.
# 싸울 때는 눈사람 손 높이 근처로 내려온다(spirit.py 의 target_height).
SPIRIT_HOVER_HEIGHT = 90  # 떠다닐 때 땅에서 떠 있는 높이(px)
SPIRIT_NOTICE_RANGE = 600  # 눈사람이 이 거리 안에 들어오면 쫓아온다.
SPIRIT_GIVE_UP_RANGE = 900  # 이보다 멀어지면 포기하고 제자리로 돌아간다.
SPIRIT_KEEP_MIN = 180  # 눈사람과 이 거리보다 가까우면 물러난다.
SPIRIT_KEEP_MAX = 320  # 이 거리보다 멀면 다가간다.
SPIRIT_LEASH = 500  # 처음 자리에서 이보다 멀리 가지 않는다.
SPIRIT_AIM_TIME = 0.6  # 쏘기 전에 부풀어 오르며 알려 주는 시간(초)
SPIRIT_FIRE_COOLDOWN = 1.8  # 한 번 쏜 뒤 다시 쏘기까지의 시간(초)

FIREBALL_SPEED = 300  # 불덩이 속도(px/s). 쏠 때의 눈사람 위치를 향해 곧게 날아간다.
FIREBALL_DAMAGE = 8  # 불덩이에 맞으면 녹는 눈
HIT_INVINCIBLE_TIME = 1.2  # 맞은 뒤 다시 맞지 않는 시간(초)
