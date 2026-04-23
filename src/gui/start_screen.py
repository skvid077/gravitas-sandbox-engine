import os
from typing import Callable, Optional

from pydantic import ValidationError
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QMessageBox
)

from config.constants import *
from config.schemas import SimulationScenario
from core.load_json import ScenarioLoadError, load_scenario_from_file
from gui.main_window import MainWindow


class StartScreen(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Gravitas sandbox engine - Стартовое окно")
        self.setFixedSize(START_WINDOW_WIDTH, START_WINDOW_HEIGHT)
        self._main_window: Optional[MainWindow] = None
        self._init_ui()

    def _init_ui(self) -> None:
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

        self._btn_new = self._create_button("Новый конструктор", self.start_sandbox_callback)
        layout.addWidget(self._btn_new, alignment=Qt.AlignmentFlag.AlignCenter)

        self._btn_load = self._create_button("Загрузить симуляцию (json)", self.load_from_json_callback)
        layout.addWidget(self._btn_load, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(START_STRETCH_FACTOR)

    def _create_button(
        self, 
        message: str, 
        callback: Callable[[], None], 
        height: int = START_BTN_HEIGHT, 
        width: int = START_BTN_WIDTH
    ) -> QPushButton:
        btn = QPushButton(message)
        btn.setFixedSize(width, height)
        btn.setStyleSheet(START_BTN_STYLE_SHEET)
        btn.clicked.connect(callback)
        return btn
    
    def start_sandbox_callback(self) -> None:
        self.start_sandbox()
    
    def load_from_json_callback(self) -> None:
        self.load_from_json()

    def load_from_json(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл сценария",
            "",
            "JSON Files (*.json)"
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
        self._main_window = MainWindow(scenario)
        self._main_window.showMaximized()
        self.close()
