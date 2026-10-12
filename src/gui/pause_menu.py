from typing import Any, cast

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPaintEvent
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.constants import (
    BTN_MENU_HEIGHT,
    DIALOG_LOAD_FILTER,
    DIALOG_SAVE_TITLE,
    DIALOG_TITLE_SAVE_ERROR,
    DIALOG_TITLE_SUCCESS,
    DIMMER_COLOR,
    JSON_FILE_EXTENSION,
    MENU_LAYOUT_SPACING,
    MENU_MARGIN_HORIZONTAL,
    MENU_MARGIN_VERTICAL,
    MENU_STYLE_SHEET,
    MENU_WIDTH,
    PAUSE_MENU_OBJECT_NAME,
    STYLE_BTN_MENU,
    STYLE_BTN_MENU_CONTINUE,
    TEXT_BTN_ADD,
    TEXT_BTN_EXIT,
    TEXT_BTN_EXPORT,
    TEXT_BTN_REGISTRY,
    TEXT_BTN_RESUME,
    TEXT_FILE_SAVED,
)
from config.models import BodyState, SimulationScenario
from core.load_json import ScenarioFileService, ScenarioSaveError
from gui.add_planet import AddPlanetDialog
from gui.planets_manager import PlanetsManagerDialog


class DimmerOverlay(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.hide()

    def paintEvent(self, event: QPaintEvent | None) -> None:
        if event is None:
            return
        painter = QPainter(self)
        painter.fillRect(self.rect(), DIMMER_COLOR)


class PauseMenu(QFrame):
    resume_requested = pyqtSignal()
    planet_added = pyqtSignal(object)  # Передает BodyState
    planet_removed = pyqtSignal(int)
    planet_modified = pyqtSignal(int)

    def __init__(self, parent: QWidget, planets_info: list[BodyState], scenario_name: str) -> None:
        super().__init__(parent)
        self.planets_info = planets_info
        self.scenario_name = scenario_name

        self.overlay = DimmerOverlay(parent)

        self.setFixedWidth(MENU_WIDTH)
        self.hide()

        self.setObjectName(PAUSE_MENU_OBJECT_NAME)
        self.setStyleSheet(MENU_STYLE_SHEET)
        self.btn_resume: QPushButton
        self.btn_show_all: QPushButton
        self.btn_add: QPushButton
        self.btn_export: QPushButton
        self.btn_exit: QPushButton

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(MENU_LAYOUT_SPACING)
        layout.setContentsMargins(
            MENU_MARGIN_HORIZONTAL,
            MENU_MARGIN_VERTICAL,
            MENU_MARGIN_HORIZONTAL,
            MENU_MARGIN_VERTICAL,
        )

        self.btn_resume = QPushButton(TEXT_BTN_RESUME)
        self.btn_show_all = QPushButton(TEXT_BTN_REGISTRY)
        self.btn_add = QPushButton(TEXT_BTN_ADD)
        self.btn_export = QPushButton(TEXT_BTN_EXPORT)
        self.btn_exit = QPushButton(TEXT_BTN_EXIT)

        self.btn_resume.setStyleSheet(STYLE_BTN_MENU_CONTINUE)
        for btn in [self.btn_show_all, self.btn_add, self.btn_export, self.btn_exit]:
            btn.setStyleSheet(STYLE_BTN_MENU)

        for btn in [
            self.btn_resume,
            self.btn_show_all,
            self.btn_add,
            self.btn_export,
            self.btn_exit,
        ]:
            btn.setFixedHeight(BTN_MENU_HEIGHT)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(btn)

        cast(Any, self.btn_resume.clicked).connect(self.resume_callback)
        cast(Any, self.btn_show_all.clicked).connect(self.show_all_callback)
        cast(Any, self.btn_add.clicked).connect(self.add_planet_callback)
        cast(Any, self.btn_export.clicked).connect(self.export_json_callback)
        cast(Any, self.btn_exit.clicked).connect(self.exit_callback)

        self.adjustSize()

    def toggle(self) -> None:
        parent_widget = self.parentWidget()
        if not parent_widget:
            return

        if self.isVisible():
            self.hide()
            self.overlay.hide()
            cast(Any, self.resume_requested).emit()
        else:
            self.overlay.setGeometry(parent_widget.rect())
            self.overlay.show()
            self.show()
            self.update_position()
            self.overlay.raise_()
            self.raise_()

    def update_position(self) -> None:
        parent_widget = self.parentWidget()
        if parent_widget:
            x = (parent_widget.width() - self.width()) // 2
            y = (parent_widget.height() - self.height()) // 2
            self.move(x, y)

    def resume_callback(self, _checked: bool = False) -> None:
        self.toggle()

    def show_all_callback(self, _checked: bool = False) -> None:
        self.hide()
        dialog = PlanetsManagerDialog(self.planets_info, self.parentWidget())
        cast(Any, dialog.planet_removed).connect(self._on_planet_removed_from_manager)
        cast(Any, dialog.planet_modified).connect(cast(Any, self.planet_modified).emit)
        dialog.exec()
        self.show()

    def _on_planet_removed_from_manager(self, index: int) -> None:
        if 0 <= index < len(self.planets_info):
            self.planets_info.pop(index)
            cast(Any, self.planet_removed).emit(index)

    def add_planet_callback(self, _checked: bool = False) -> None:
        self.hide()
        dialog = AddPlanetDialog(self.planets_info, self.parentWidget())

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_planet = dialog.get_planet_data()
            self.planets_info.append(new_planet)
            cast(Any, self.planet_added).emit(new_planet)

        self.show()
        self.overlay.show()

    def export_json_callback(self, _checked: bool = False) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, DIALOG_SAVE_TITLE, "", DIALOG_LOAD_FILTER)

        if not file_path:
            return
        if not file_path.endswith(JSON_FILE_EXTENSION):
            file_path += JSON_FILE_EXTENSION

        try:
            scenario = SimulationScenario(name=self.scenario_name, bodies=self.planets_info)
            ScenarioFileService.save(scenario, file_path)
            QMessageBox.information(self, DIALOG_TITLE_SUCCESS, TEXT_FILE_SAVED.format(file_path))

        except ScenarioSaveError as e:
            QMessageBox.critical(self, DIALOG_TITLE_SAVE_ERROR, str(e))

    @staticmethod
    def exit_callback(_checked: bool = False) -> None:
        QApplication.quit()
