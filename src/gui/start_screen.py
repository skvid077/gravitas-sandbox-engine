import os
from collections.abc import Callable
from typing import Any, cast

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.constants import (
    BTN_TEXT_LOAD,
    BTN_TEXT_NEW,
    CENTRAL_WIDGET_OBJECT_NAME,
    DIALOG_LOAD_FILTER,
    DIALOG_LOAD_TITLE,
    DIALOG_TITLE_LOAD_ERROR,
    GRAVITY_CONSTANT,
    START_BACKGROUND_IMAGE_PATH,
    START_BTN_HEIGHT,
    START_BTN_STYLE_SHEET,
    START_BTN_WIDTH,
    START_LAYOUT_MARGIN_BOTTOM,
    START_LAYOUT_MARGIN_LEFT,
    START_LAYOUT_MARGIN_RIGHT,
    START_LAYOUT_MARGIN_TOP,
    START_LAYOUT_SPACING,
    START_STRETCH_FACTOR,
    START_WINDOW_HEIGHT,
    START_WINDOW_TITLE,
    START_WINDOW_WIDTH,
)
from config.models import SimulationScenario
from core.load_json import ScenarioFileService, ScenarioLoadError
from core.session_report import SessionReport
from gui.main_window import MainWindow


class StartScreen(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(START_WINDOW_TITLE)
        self.setFixedSize(START_WINDOW_WIDTH, START_WINDOW_HEIGHT)
        self._main_window: MainWindow | None = None
        self._session_report = SessionReport()
        self._central_widget: QWidget
        self._btn_new: QPushButton
        self._btn_load: QPushButton

        self._init_ui()
        application = QApplication.instance()
        if application is not None:
            cast(Any, application.aboutToQuit).connect(self._save_session_report)

    def _init_ui(self) -> None:
        path_to_photo: str = os.path.abspath(START_BACKGROUND_IMAGE_PATH)

        self._central_widget = QWidget()
        self._central_widget.setObjectName(CENTRAL_WIDGET_OBJECT_NAME)
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
            START_LAYOUT_MARGIN_BOTTOM,
        )
        layout.setSpacing(START_LAYOUT_SPACING)

        layout.addStretch(START_STRETCH_FACTOR)

        self._btn_new = self._create_button(BTN_TEXT_NEW, self.start_sandbox_callback)
        layout.addWidget(self._btn_new, alignment=Qt.AlignmentFlag.AlignCenter)

        self._btn_load = self._create_button(BTN_TEXT_LOAD, self.load_from_json_callback)
        layout.addWidget(self._btn_load, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(START_STRETCH_FACTOR)

    @staticmethod
    def _create_button(
        message: str,
        callback: Callable[[bool], None],
        height: int = START_BTN_HEIGHT,
        width: int = START_BTN_WIDTH,
    ) -> QPushButton:
        btn = QPushButton(message)
        btn.setFixedSize(width, height)
        btn.setStyleSheet(START_BTN_STYLE_SHEET)
        cast(Any, btn.clicked).connect(callback)
        return btn

    @pyqtSlot(bool)
    def start_sandbox_callback(self, _checked: bool = False) -> None:
        self.start_sandbox()

    @pyqtSlot(bool)
    def load_from_json_callback(self, _checked: bool = False) -> None:
        self.load_from_json()

    def load_from_json(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, DIALOG_LOAD_TITLE, "", DIALOG_LOAD_FILTER)

        if not file_path:
            return

        try:
            scenario = ScenarioFileService.load(file_path)
            self.start_sandbox(scenario)

        except ScenarioLoadError as error:
            QMessageBox.critical(self, DIALOG_TITLE_LOAD_ERROR, str(error))

    def start_sandbox(self, scenario: SimulationScenario | None = None) -> None:
        self._main_window = MainWindow(scenario, self._session_report)
        self._main_window.showMaximized()
        self.close()

    def _save_session_report(self) -> None:
        if self._main_window is not None:
            self._main_window.save_session_report()
            return
        self._session_report.save(
            final_body_count=0,
            final_gravity=GRAVITY_CONSTANT,
            final_time_scale=1.0,
        )
