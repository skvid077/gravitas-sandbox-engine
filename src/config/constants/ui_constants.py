MAIN_WINDOW_TITLE: str = "Gravitas Sandbox"
MAIN_WINDOW_WIDTH: int = 1200
MAIN_WINDOW_HEIGHT: int = 800
MAIN_WINDOW_MIN_WIDTH: int = 640
MAIN_WINDOW_MIN_HEIGHT: int = 480
SCREEN_RATIO_DIVISOR: int = 2
DEFAULT_SCENARIO_NAME: str = "Новая симуляция"
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
BTN_TEXT_NEW: str = "Новый конструктор"
BTN_TEXT_LOAD: str = "Загрузить симуляцию (json)"
DIALOG_LOAD_TITLE: str = "Выберите файл сценария"
DIALOG_LOAD_FILTER: str = "JSON Files (*.json)"
STATUS_TEXT_PAUSED: str = "ПАУЗА (Нажмите Enter для запуска)"
STATUS_TEXT_RUNNING: str = "СИМУЛЯЦИЯ ЗАПУЩЕНА"
MENU_WIDTH: int = 320
TEXT_BTN_RESUME: str = "Продолжить"
TEXT_BTN_REGISTRY: str = "Реестр планет"
TEXT_BTN_ADD: str = "Добавить планету"
TEXT_BTN_EXPORT: str = "Скачать в JSON"
TEXT_BTN_EXIT: str = "Выход"
MANAGER_WINDOW_TITLE: str = "Реестр небесных тел"
MANAGER_MIN_WIDTH: int = 950
MANAGER_MIN_HEIGHT: int = 450
LABEL_COLOR: str = "Цвет"
TABLE_HEADERS: list[str] = [
    "Вид",
    "Цвет",
    "Имя",
    "Масса",
    "Радиус",
    "X",
    "Y",
    "Vx",
    "Vy",
    "Удалить",
]

COL_PREVIEW: int = 0
COL_COLOR: int = 1
COL_NAME: int = 2
COL_MASS: int = 3
COL_RADIUS: int = 4
COL_X: int = 5
COL_Y: int = 6
COL_VX: int = 7
COL_VY: int = 8
COL_DELETE: int = 9
PREVIEW_SIZE: int = 120
PREVIEW_CENTER: float = 60.0
PREVIEW_MAX_VISUAL_R: float = 50.0
PREVIEW_MIN_VISUAL_R: float = 4.0
PREVIEW_LOG_BASE: float = 12.0
PREVIEW_WIDGET_SIZE: int = 40
PREVIEW_MAX_RADIUS: float = 18.0
PREVIEW_MIN_RADIUS: float = 3.0
PREVIEW_LOG_FACTOR: float = 6.0
DIALOG_WIDTH: int = 500
DIALOG_HEIGHT: int = 480
DEFAULT_NAME: str = "Planet X"
DEFAULT_MASS: str = "1000.0"
DEFAULT_RADIUS: str = "20.0"
PANEL_TITLE: str = "Панель управления"
TEXT_GRAVITY_LBL: str = "Гравитация: {:.1f}x"
TEXT_TIME_LBL: str = "Скорость времени: {:.1f}x"
TEXT_BTN_CLEAR: str = "Очистить космос"
SLIDER_G_MIN: int = 0
SLIDER_G_MAX: int = 50
SLIDER_G_DEFAULT: int = 10
SLIDER_TIME_MIN: int = 1
SLIDER_TIME_MAX: int = 30
SLIDER_TIME_DEFAULT: int = 10
SLIDER_DIVIDER: float = 10.0
LAYOUT_SPACING: int = 20
UI_MARGIN: int = 20
UI_SPACING: int = 10
BTN_TOGGLE_SIZE: int = 56
BTN_TOGGLE_RADIUS: int = 28
BTN_TOGGLE_FONT_SIZE: int = 24
BTN_MENU_WIDTH: int = 160
BTN_MENU_HEIGHT: int = 40
BTN_MENU_RADIUS: int = 20
JSON_INDENT: int = 4
ERROR_MASS_ZERO: str = "Масса должна быть больше нуля (текущая: {})."
ERROR_RADIUS_ZERO: str = "Радиус должен быть больше нуля (текущий: {})."
ERROR_EMPTY_NAME: str = "Имя тела не может быть пустым."
ERROR_DUPLICATE_NAME: str = "Обнаружен дубликат имени: '{}'."
ERROR_COLLISION: str = "Тело '{}' накладывается на '{}' (дистанция меньше суммы радиусов)."

FPS_UPDATE_INTERVAL_MS: int = 1000
STATUS_LABEL_Y: int = 50
COORDINATE_LABEL_OFFSET: int = 15
TEXT_COLOR_LUMA_THRESHOLD: int = 140
PLANET_TEXT_WIDTH_FACTOR: float = 1.5
PLANET_TEXT_MAX_SCALE: float = 1.5
MENU_LAYOUT_SPACING: int = 15
MENU_MARGIN_HORIZONTAL: int = 30
MENU_MARGIN_VERTICAL: int = 40
TABLE_ROW_HEIGHT: int = 45
CLOSE_BUTTON_HEIGHT: int = 35
COLOR_BUTTON_WIDTH: int = 30
COLOR_BUTTON_HEIGHT: int = 20
DELETE_BUTTON_SIZE: int = 30

DEFAULT_COORDINATE_TEXT: str = "0.0"
TEXT_TIMELINE_FORMAT: str = "Машина времени: {} / {}"
TEXT_FPS_FORMAT: str = "FPS: {}"
TEXT_COORDINATES_FORMAT: str = "X: {:.1f} | Y: {:.1f}"

DIALOG_EDIT_BODY_TITLE: str = "Редактирование тела"
DIALOG_NEW_BODY_TITLE: str = "Параметры нового тела"
DIALOG_SAVE_TITLE: str = "Сохранить симуляцию"
DIALOG_TITLE_ERROR: str = "Ошибка"
DIALOG_TITLE_LOAD_ERROR: str = "Ошибка загрузки"
DIALOG_TITLE_PARAMETER_ERROR: str = "Ошибка параметров"
DIALOG_TITLE_PHYSICS_ERROR: str = "Ошибка физики"
DIALOG_TITLE_SUCCESS: str = "Успех"
DIALOG_TITLE_SAVE_ERROR: str = "Ошибка сохранения"

LABEL_NAME: str = "Имя:"
LABEL_MASS: str = "Масса:"
LABEL_RADIUS: str = "Радиус:"
LABEL_X: str = "X:"
LABEL_Y: str = "Y:"
LABEL_VX: str = "Vx:"
LABEL_VY: str = "Vy:"
TEXT_SAVE: str = "Сохранить"
TEXT_ADD: str = "Добавить"
TEXT_CANCEL: str = "Отмена"
TEXT_CLOSE: str = "Закрыть"
TEXT_DELETE: str = "×"
TEXT_FILE_SAVED: str = "Файл успешно сохранен:\n{}"
JSON_FILE_EXTENSION: str = ".json"
BODY_STRING_FORMAT: str = "{} (масса: {:g}, радиус: {:g})"

ERROR_NON_FINITE_COORDINATES: str = "Координаты и скорость должны быть конечными числами."
ERROR_INVALID_GRAVITATIONAL_CONSTANT: str = (
    "Gravitational constant must be a finite, non-negative number."
)
ERROR_FILE_NOT_FOUND: str = "Файл не найден: {}"
ERROR_FILE_READ: str = "Не удалось прочитать файл: {}"
ERROR_UNKNOWN: str = "неизвестная ошибка"
ERROR_JSON_SYNTAX: str = "Ошибка синтаксиса JSON: {}"
ERROR_SCENARIO_PARAMETERS: str = "Некорректные параметры сценария:\n{}"
ERROR_SCENARIO_LOGIC: str = "Ошибка в логике сценария:\n{}"
ERROR_SCENARIO_SAVE: str = "Некорректный сценарий: {}"
ERROR_FILE_SAVE: str = "Не удалось сохранить файл: {}"
