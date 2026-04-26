"""Константы физического движка и математических расчетов."""

# Параметры движка
GRAVITY_CONSTANT: float = 10.0
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
