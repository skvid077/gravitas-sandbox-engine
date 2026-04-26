import os
from typing import Callable, Optional

from pydantic import ValidationError
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QMessageBox
)

from config.schemas import SimulationScenario
from core.load_json import ScenarioLoadError, load_scenario_from_file
from gui.main_window import MainWindow
from config.constants import (
    START_WINDOW_HEIGHT,
    START_WINDOW_TITLE,
    BTN_TEXT_NEW,
    BTN_TEXT_LOAD,
    DIALOG_LOAD_TITLE,
    DIALOG_LOAD_FILTER,
    START_LAYOUT_MARGIN_LEFT,
    START_LAYOUT_MARGIN_TOP,
    START_LAYOUT_MARGIN_RIGHT,
    START_LAYOUT_MARGIN_BOTTOM,
    START_LAYOUT_SPACING,
    START_STRETCH_FACTOR,
    START_BTN_HEIGHT,
    START_BTN_WIDTH,
    START_BTN_STYLE_SHEET,
    START_BACKGROUND_IMAGE_PATH,
    START_WINDOW_WIDTH,
    START_WINDOW_HEIGHT
)


class StartScreen(QMainWindow):
    """
    Стартовое окно приложения (главное меню).
    
    Обеспечивает интерфейс для начала новой симуляции (пустой песочницы) 
    или загрузки существующего сценария из JSON-файла.
    """

    def __init__(self) -> None:
        """Инициализирует стартовое окно, задает заголовок, размеры и базовые атрибуты."""
        super().__init__()
        self.setWindowTitle(START_WINDOW_TITLE)
        self.setFixedSize(START_WINDOW_WIDTH, START_WINDOW_HEIGHT)
        
        # Строгая типизация всех атрибутов класса для mypy
        self._main_window: Optional[MainWindow] = None
        self._central_widget: QWidget
        self._btn_new: QPushButton
        self._btn_load: QPushButton
        
        self._init_ui()

    def _init_ui(self) -> None:
        """Создает и настраивает графические элементы окна (фон, кнопки, компоновку)."""
        path_to_photo: str = os.path.abspath(START_BACKGROUND_IMAGE_PATH)

        self._central_widget = QWidget()
        self._central_widget.setObjectName("centralWidget") 
        self.setCentralWidget(self._central_widget)

        self._central_widget.setStyleSheet(f"""
            #centralWidget {{
                border-image: url('{path_to_photo}') 0 0 0 0 stretch stretch;
            }}
        """)

        layout = QVBoxLayout(self._central_widget)
        layout.setContentsMargins(
            START_LAYOUT_MARGIN_LEFT, 
            START_LAYOUT_MARGIN_TOP, 
            START_LAYOUT_MARGIN_RIGHT, 
            START_LAYOUT_MARGIN_BOTTOM
        )
        layout.setSpacing(START_LAYOUT_SPACING)

        layout.addStretch(START_STRETCH_FACTOR)

        self._btn_new = self._create_button(BTN_TEXT_NEW, self.start_sandbox_callback)
        layout.addWidget(self._btn_new, alignment=Qt.AlignmentFlag.AlignCenter)

        self._btn_load = self._create_button(BTN_TEXT_LOAD, self.load_from_json_callback)
        layout.addWidget(self._btn_load, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(START_STRETCH_FACTOR)

    def _create_button(
        self, 
        message: str, 
        callback: Callable[[bool], None], 
        height: int = START_BTN_HEIGHT, 
        width: int = START_BTN_WIDTH
    ) -> QPushButton:
        """
        Создает и стилизует кнопку главного меню.

        Args:
            message (str): Текст, который будет отображаться на кнопке.
            callback (Callable[[bool], None]): Метод-обработчик, вызываемый при нажатии.
            height (int, optional): Высота кнопки в пикселях. По умолчанию START_BTN_HEIGHT.
            width (int, optional): Ширина кнопки в пикселях. По умолчанию START_BTN_WIDTH.

        Returns:
            QPushButton: Готовый экземпляр кнопки с подключенным сигналом.
        """
        btn = QPushButton(message)
        btn.setFixedSize(width, height)
        btn.setStyleSheet(START_BTN_STYLE_SHEET)
        # Сигнал clicked передает аргумент checked (bool), поэтому callback должен его ожидать
        btn.clicked.connect(callback)
        return btn
    
    @pyqtSlot(bool)
    def start_sandbox_callback(self, checked: bool = False) -> None:
        """
        Слот для обработки нажатия кнопки 'Новый конструктор'.
        
        Служит оберткой, чтобы предотвратить передачу булевого значения (checked) 
        в качестве аргумента scenario в метод start_sandbox.
        
        Args:
            checked (bool, optional): Состояние кнопки (передается сигналом). По умолчанию False.
        """
        self.start_sandbox()
    
    @pyqtSlot(bool)
    def load_from_json_callback(self, checked: bool = False) -> None:
        """
        Слот для обработки нажатия кнопки 'Загрузить симуляцию'.
        
        Args:
            checked (bool, optional): Состояние кнопки (передается сигналом). По умолчанию False.
        """
        self.load_from_json()

    def load_from_json(self) -> None:
        """
        Открывает диалог выбора файла, считывает JSON и запускает симуляцию.
        
        Обрабатывает ошибки чтения файла и валидации Pydantic, выводя
        соответствующие предупреждения в виде всплывающих окон (QMessageBox).
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            DIALOG_LOAD_TITLE,
            "",
            DIALOG_LOAD_FILTER
        )

        if not file_path:
            return

        try:
            scenario = load_scenario_from_file(file_path)
            self.start_sandbox(scenario)
            
        except ScenarioLoadError as e:
            QMessageBox.critical(self, "Ошибка загрузки", str(e))

        except ValidationError as e:
            error_msgs: str = "\n".join([f"- {err.get('msg', str(err))}" for err in e.errors()])
            QMessageBox.critical(
                self, 
                "Ошибка валидации файла", 
                f"Структура или логика файла нарушена:\n{error_msgs}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать файл:\n{e}")

    def start_sandbox(self, scenario: Optional[SimulationScenario] = None) -> None:
        """
        Инициализирует и открывает главное окно симуляции, после чего закрывает стартовое.

        Args:
            scenario (Optional[SimulationScenario], optional): Загруженный сценарий симуляции. 
                Если не передан (None), открывается пустая песочница. По умолчанию None.
        """
        self._main_window = MainWindow(scenario)
        self._main_window.showMaximized()
        self.close()
