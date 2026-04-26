"""Константы интерфейса, путей и текстовых сообщений."""
from typing import List

# Главное окно
MAIN_WINDOW_TITLE: str = "Gravitas Sandbox"
MAIN_WINDOW_WIDTH: int = 1200
MAIN_WINDOW_HEIGHT: int = 800
MAIN_WINDOW_MIN_WIDTH: int = 640
MAIN_WINDOW_MIN_HEIGHT: int = 480
SCREEN_RATIO_DIVISOR: int = 2
DEFAULT_SCENARIO_NAME: str = "Новая симуляция"

# Стартовое окно
START_WINDOW_TITLE: str = "Gravitas sandbox engine - Стартовое окно"
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

# Тексты кнопок
BTN_TEXT_NEW: str = "Новый конструктор"
BTN_TEXT_LOAD: str = "Загрузить симуляцию (json)"
DIALOG_LOAD_TITLE: str = "Выберите файл сценария"
DIALOG_LOAD_FILTER: str = "JSON Files (*.json)"

# Индикаторы статуса
STATUS_TEXT_PAUSED: str = "ПАУЗА (Нажмите Enter для запуска)"
STATUS_TEXT_RUNNING: str = "СИМУЛЯЦИЯ ЗАПУЩЕНА"

# Меню паузы и диалоги
MENU_WIDTH: int = 320
TEXT_BTN_RESUME: str = "Продолжить"
TEXT_BTN_REGISTRY: str = "Реестр планет"
TEXT_BTN_ADD: str = "Добавить планету"
TEXT_BTN_EXPORT: str = "Скачать в JSON"
TEXT_BTN_EXIT: str = "Выход"

# Реестр планет (Table)
MANAGER_WINDOW_TITLE: str = "Реестр небесных тел"
MANAGER_MIN_WIDTH: int = 950
MANAGER_MIN_HEIGHT: int = 450
TABLE_HEADERS: List[str] = ["Вид", "Цвет", "Имя", "Масса", "Радиус", "X", "Y", "Vx", "Vy", "Удалить"]

COL_PREVIEW, COL_COLOR, COL_NAME = 0, 1, 2
COL_MASS, COL_RADIUS, COL_X, COL_Y = 3, 4, 5, 6
COL_VX, COL_VY, COL_DELETE = 7, 8, 9

# Параметры превью
PREVIEW_SIZE: int = 120
PREVIEW_CENTER: float = 60.0
PREVIEW_MAX_VISUAL_R: float = 50.0
PREVIEW_MIN_VISUAL_R: float = 4.0
PREVIEW_LOG_BASE: float = 12.0
PREVIEW_WIDGET_SIZE: int = 40
PREVIEW_MAX_RADIUS: float = 18.0
PREVIEW_MIN_RADIUS: float = 3.0
PREVIEW_LOG_FACTOR: float = 6.0

# Окно добавления
DIALOG_WIDTH: int = 500
DIALOG_HEIGHT: int = 480
DEFAULT_NAME: str = "Planet X"
DEFAULT_MASS: str = "1000.0"
DEFAULT_RADIUS: str = "20.0"

# Панель управления
PANEL_TITLE: str = "Панель управления"
TEXT_GRAVITY_LBL: str = "Гравитация: {:.1f}x"
TEXT_TIME_LBL: str = "Скорость времени: {:.1f}x"
TEXT_BTN_CLEAR: str = "Очистить космос"
SLIDER_G_MIN, SLIDER_G_MAX, SLIDER_G_DEFAULT = 0, 50, 10
SLIDER_TIME_MIN, SLIDER_TIME_MAX, SLIDER_TIME_DEFAULT = 1, 30, 10
SLIDER_DIVIDER: float = 10.0
LAYOUT_SPACING: int = 20

# Прочее
UI_MARGIN, UI_SPACING = 20, 10
BTN_TOGGLE_SIZE, BTN_TOGGLE_RADIUS, BTN_TOGGLE_FONT_SIZE = 56, 28, 24
BTN_MENU_WIDTH, BTN_MENU_HEIGHT, BTN_MENU_RADIUS = 160, 40, 20
JSON_INDENT: int = 4

# Ошибки
ERROR_MASS_ZERO: str = "Масса должна быть больше нуля (текущая: {})."
ERROR_RADIUS_ZERO: str = "Радиус должен быть больше нуля (текущий: {})."
ERROR_EMPTY_NAME: str = "Имя тела не может быть пустым."
ERROR_DUPLICATE_NAME: str = "Обнаружен дубликат имени: '{}'."
ERROR_COLLISION: str = "Тело '{}' накладывается на '{}' (дистанция меньше суммы радиусов)."
