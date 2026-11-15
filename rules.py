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

SNOWFIELD_SNOW = 30  # 눈밭 하나에 들어 있는 눈. 난로를 끄는 데 쓴 15 의 두 배다.
SNOWFIELD_WIDTH = 420  # 처음 생긴 눈밭의 너비(px). 눈을 가져갈수록 좁아진다.
ROLL_RECOVER_PER_SEC = 8  # 눈밭 위를 구를 때 1초에 회복하는 눈
