from typing import Tuple

# =========================================
# ГЕНЕРАЦИЯ КОСМОСА И ЧАНКИ
# =========================================

CHUNK_SIZE: int = 512
RENDER_DISTANCE: int = 1
COUNT_CHUNKS: int = 1_000_000

HASH_SEED_X: int = 397
HASH_SEED_Y: int = 433

SPACE_COLOR: str = "#0C021C"
BACKGROUND_VALUE: int = -10

# =========================================
# ОТРИСОВКА ЗВЕЗД И ОПТИМИЗАЦИЯ
# =========================================

MIN_STARS_PER_CHUNK: int = 0
MAX_STARS_PER_CHUNK: int = 100
SIZE_STAR_MIN: float = 2.0
SIZE_STAR_MAX: float = 5.0
OPACITY_MIN: float = 0.4
OPACITY_MAX: float = 1.0
COLOR_ALPHA_MAX: int = 255

STARS_LOD_THRESHOLD: int = 10000
MAX_VISIBLE_CHUNKS: int = 400

# Используем кортеж (tuple) для защиты от мутаций во время работы программы

STAR_PALETTE: Tuple[str, ...] = (
    "#0b45f0", 
    "#0b45f0",
    "#ffffff", 
    "#ffffff", 
    "#ffffff",
    "#e7d638",
    "#ec881c",
    "#f22121",
)

# =========================================
# ФИЗИКА И РЕНДЕР ПЛАНЕТ
# =========================================

PLANET_Z_VALUE: int = 10
LUMA_R_WEIGHT: int = 299
LUMA_G_WEIGHT: int = 587
LUMA_B_WEIGHT: int = 114
LUMA_DENOMINATOR: int = 1000
LUMA_THRESHOLD: int = 128
TEXT_DEFAULT_SCALE: float = 1.0
TEXT_FIT_MULTIPLIER: float = 1.35
MIN_MASS: float = 0.0001
MAX_MASS: float = 1e9
MIN_RADIUS: float = 0.1
MAX_RADIUS: float = 10000.0
MIN_COORD: float = -1e9
MAX_COORD: float = 1e9
MIN_VEL: float = -10000.0
MAX_VEL: float = 10000.0

# =========================================
# НАСТРОЙКИ КАМЕРЫ (VIEW)
# =========================================

VIEW_CENTER_X: int = 0
VIEW_CENTER_Y: int = 0
ZOOM_FACTOR: float = 1.15
TEXT_VISIBLE_ZOOM_THRESHOLD: float = 0.3

# =========================================
# РАЗМЕРЫ ОКОН И ОТСТУПЫ
# =========================================

MAIN_WINDOW_MIN_WIDTH: int = 640
MAIN_WINDOW_MIN_HEIGHT: int = 480
SCREEN_RATIO_DIVISOR: int = 2

START_WINDOW_WIDTH: int = 400
START_WINDOW_HEIGHT: int = 300
START_BACKGROUND_IMAGE_PATH: str = "src/gui/data/start_screen_background.jpg"

START_LAYOUT_MARGIN_LEFT: int = 0
START_LAYOUT_MARGIN_TOP: int = 30
START_LAYOUT_MARGIN_RIGHT: int = 0
START_LAYOUT_MARGIN_BOTTOM: int = 30
START_LAYOUT_SPACING: int = 15
START_STRETCH_FACTOR: int = 1

START_BTN_WIDTH: int = 275
START_BTN_HEIGHT: int = 50

UI_MARGIN: int = 20
UI_SPACING: int = 10

BTN_TOGGLE_SIZE: int = 56
BTN_TOGGLE_RADIUS: int = 28
BTN_TOGGLE_FONT_SIZE: int = 24

BTN_MENU_WIDTH: int = 160
BTN_MENU_HEIGHT: int = 40
BTN_MENU_RADIUS: int = 20

JSON_INDENT: int = 4

# =========================================
# QSS СТИЛИ ИНТЕРФЕЙСА
# =========================================

START_BTN_STYLE_SHEET: str = """
QPushButton {
    background-color: rgba(0, 0, 0, 100); 
    color: white; 
    border: 1px solid rgba(255, 255, 255, 100); 
    border-radius: 5px; 
    font-size: 14px;
    font-family: "Arial";
}
QPushButton:hover {
    background-color: rgba(255, 255, 255, 40); 
    color: white; 
    border: 1px solid white; 
}
QPushButton:pressed {
    background-color: rgba(0, 0, 0, 180); 
    color: rgba(255, 255, 255, 200); 
    border: 1px solid white;
}
"""

COORD_LABEL_STYLE: str = """
color: #00FF00; 
background-color: rgba(0, 0, 0, 150); 
padding: 4px; 
border-radius: 4px; 
font-family: monospace;
"""

FPS_LABEL_STYLE: str = """
color: #FFFF00; 
background-color: rgba(0, 0, 0, 150); 
padding: 4px; 
border-radius: 4px; 
font-family: monospace; 
font-weight: bold;
"""

STYLE_BTN_TOGGLE_CLOSED: str = f"""
QPushButton {{ 
    background-color: #6200EE; 
    color: white; 
    border-radius: {BTN_TOGGLE_RADIUS}px; 
    font-size: {BTN_TOGGLE_FONT_SIZE}px; 
}}
QPushButton:hover {{ 
    background-color: #7c4dff; 
}}
"""

STYLE_BTN_TOGGLE_OPEN: str = f"""
QPushButton {{ 
    background-color: #eb4034; 
    color: white; 
    border-radius: {BTN_TOGGLE_RADIUS}px; 
    font-size: {BTN_TOGGLE_FONT_SIZE}px; 
}}
QPushButton:hover {{ 
    background-color: #ff5c5c; 
}}
"""

# Базовый стиль для обычных кнопок (Выход, Все планеты, Отмена и т.д.)
STYLE_BTN_MENU = """
    QPushButton {
        background-color: rgba(45, 50, 65, 180);
        color: #E0E0E0;
        border: 1px solid rgba(120, 130, 160, 80);
        border-radius: 8px;
        padding: 8px 15px;
        font-size: 14px;
        font-weight: 500;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QPushButton:hover {
        background-color: rgba(65, 75, 95, 220);
        border: 1px solid rgba(150, 160, 200, 150);
        color: #FFFFFF;
    }
    QPushButton:pressed {
        background-color: rgba(30, 35, 45, 255);
        border: 1px solid rgba(80, 90, 120, 200);
        color: #AAAAAA;
    }
"""

# Акцентный стиль для главных действий (Продолжить, Добавить, Сохранить)
STYLE_BTN_MENU_CONTINUE = """
    QPushButton {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2b5876, stop:1 #4e4376);
        color: #FFFFFF;
        border: 1px solid rgba(255, 255, 255, 40);
        border-radius: 8px;
        padding: 8px 15px;
        font-size: 14px;
        font-weight: bold;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QPushButton:hover {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b6886, stop:1 #5e5386);
        border: 1px solid rgba(255, 255, 255, 80);
    }
    QPushButton:pressed {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1b4866, stop:1 #3e3366);
        border: 1px solid rgba(255, 255, 255, 20);
        color: #CCCCCC;
    }
"""
