import os
from pathlib import Path
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
from gui.main_window import MainWindow


class StartScreen(QMainWindow):
    """
    Стартовое окно приложения (Главное меню).
    
    Отвечает за выбор режима запуска: создание пустой симуляции 
    или загрузка готового сценария из JSON-файла с автоматической валидацией.
    """

    def __init__(self) -> None:
        """Инициализирует окно главного меню."""
        super().__init__()
        self.setWindowTitle("Gravitas sandbox engine - Стартовое окно")
        self.setFixedSize(START_WINDOW_WIDTH, START_WINDOW_HEIGHT)
        
        # Храним ссылку на главное окно, чтобы его не уничтожил сборщик мусора
        self._main_window: Optional[MainWindow] = None
        
        self._init_ui()

    def _init_ui(self) -> None:
        """Инициализирует и компонует элементы пользовательского интерфейса."""
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

        self._btn_new = self._create_button("Новый конструктор", self.start_sandbox)
        layout.addWidget(self._btn_new, alignment=Qt.AlignmentFlag.AlignCenter)

        self._btn_load = self._create_button("Загрузить симуляцию (json)", self.load_from_json)
        layout.addWidget(self._btn_load, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(START_STRETCH_FACTOR)

    def _create_button(
        self, 
        message: str, 
        callback: Callable[[], None], 
        height: int = START_BTN_HEIGHT, 
        width: int = START_BTN_WIDTH
    ) -> QPushButton:
        """
        Фабричный метод для создания стилизованных кнопок главного меню.
        
        Args:
            message (str): Текст на кнопке.
            callback (Callable): Метод, который вызовется при клике.
            height (int): Высота кнопки.
            width (int): Ширина кнопки.
            
        Returns:
            QPushButton: Готовый виджет кнопки.
        """
        btn = QPushButton(message)
        btn.setFixedSize(width, height)
        btn.setStyleSheet(START_BTN_STYLE_SHEET)
        btn.clicked.connect(callback)
        return btn

    def load_from_json(self) -> None:
        """
        Открывает диалог выбора файла, делегирует валидацию Pydantic
        и запускает движок в случае успеха.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл сценария",
            "",
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            # Pydantic сам проверит типы, дубликаты имен и коллизии внутри load_from_json
            scenario: SimulationScenario = SimulationScenario.load_from_json(Path(file_path))
            self.start_sandbox(scenario)
            
        except ValidationError as e:
            # Pydantic отдает детальный список ошибок (включая наши кастомные из @model_validator)
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
        Закрывает стартовое меню и разворачивает основное окно симулятора.
        
        Args:
            scenario (Optional[SimulationScenario]): Готовый сценарий (если загружен из JSON).
        """
        self._main_window = MainWindow(scenario)
        self._main_window.showMaximized()
        self.close()
