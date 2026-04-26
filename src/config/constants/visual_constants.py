"""Константы визуального оформления, генерации звезд и настройки View."""
from typing import Tuple

# Генерация космоса и чанки
SPACE_COLOR: str = "#0C021C"
CHUNK_SIZE: int = 512
RENDER_DISTANCE: int = 1
COUNT_CHUNKS: int = 1_000_000
HASH_SEED_X: int = 397
HASH_SEED_Y: int = 433
BACKGROUND_VALUE: int = -10

# Отрисовка звезд
MIN_STARS_PER_CHUNK: int = 0
MAX_STARS_PER_CHUNK: int = 10
SIZE_STAR_MIN: float = 2.0
SIZE_STAR_MAX: float = 5.0
OPACITY_MIN: float = 0.4
OPACITY_MAX: float = 1.0
COLOR_ALPHA_MAX: int = 255
STARS_LOD_THRESHOLD: int = 10000
MAX_VISIBLE_CHUNKS: int = 400

STAR_PALETTE: Tuple[str, ...] = (
    "#0b45f0", "#0b45f0", "#ffffff", "#ffffff", 
    "#ffffff", "#e7d638", "#ec881c", "#f22121"
)

# Параметры планет и текста
DEFAULT_PLANET_NAME: str = "New Planet"
DEFAULT_PLANET_MASS: float = 50.0
DEFAULT_PLANET_RADIUS: float = 10.0
DEFAULT_COLOR: str = "#FF6464"
PLANET_Z_VALUE: int = 10

RANDOM_COLORS: list[str] = [
    "#FF6464", "#64FF64", "#6464FF", "#FFFF64", 
    "#FF64FF", "#64FFFF", "#E0E5E5", "#DDAA55"
]

# Расчет яркости для контраста текста (Luma)
LUMA_R_WEIGHT: int = 299
LUMA_G_WEIGHT: int = 587
LUMA_B_WEIGHT: int = 114
LUMA_DENOMINATOR: int = 1000
LUMA_THRESHOLD: int = 128

# Масштабирование текста
TEXT_DEFAULT_SCALE: float = 1.0
TEXT_FIT_MULTIPLIER: float = 1.35

# Настройки камеры (Zoom)
VIEW_CENTER_X: int = 0
VIEW_CENTER_Y: int = 0
ZOOM_FACTOR: float = 1.15
ZOOM_IN_FACTOR: float = 1.05
ZOOM_MIN_SCALE: float = 0.005
ZOOM_MAX_SCALE: float = 50.0
TEXT_VISIBLE_ZOOM_THRESHOLD: float = 0.3
