"""Константы физического движка и математических расчетов."""

# Параметры движка
GRAVITY_CONSTANT: float = 9.81
PHYSICS_TICK_RATE: int = 16   # мс (~60 FPS)
SOFTENING_CONSTANT: float = 2.0
DEFAULT_SUB_STEPS: int = 128
DEFAULT_RESTITUTION: float = 0.8  # 1.0 - упругий, 0.0 - слипание

# Лимиты физических величин
MIN_MASS: float = 0.0001
MAX_MASS: float = 1e9
MIN_RADIUS: float = 0.1
MAX_RADIUS: float = 10000.0
MIN_COORD: float = -1e9
MAX_COORD: float = 1e9
MIN_VEL: float = -10000.0
MAX_VEL: float = 10000.0

BH_THETA: float = 0.5  # Порог точности (0.0 - точный O(N^2), 1.0 - быстро, но грубо)
BH_SOFTENING: float = 1e-4  # Сглаживание сингулярности при близких пролетах

DEFAULT_MAX_SECONDS_FOR_TIME_MACHINE: int = 30
DEFAULT_FPS_FOR_TIME_MACHINE: int = 60

MIN_BODIES_FOR_PHYSICS = 2
BOUNDING_BOX_PADDING = 0.5
BOUNDING_BOX_SIZE_OFFSET = 1.0
CELL_SIZE_MULTIPLIER = 2.1
MIN_CELL_SIZE = 1.0

SPACE_DIMENSIONS = 2
SUBDIVISION_FACTOR = 2.0
MIN_DIST_EPSILON = 1e-10
DEFAULT_BH_THETA = 0.5
DEFAULT_SOFTENING = 1e-4
