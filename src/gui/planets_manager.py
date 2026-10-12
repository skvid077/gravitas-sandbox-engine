import math
from dataclasses import replace
from typing import Any, cast

from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import (
    QColorDialog,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.constants import (
    CLOSE_BUTTON_HEIGHT,
    CLOSE_BUTTON_OBJECT_NAME,
    COL_COLOR,
    COL_DELETE,
    COL_MASS,
    COL_NAME,
    COL_PREVIEW,
    COL_RADIUS,
    COL_VX,
    COL_VY,
    COL_X,
    COL_Y,
    COLOR_BUTTON_HEIGHT,
    COLOR_BUTTON_WIDTH,
    DELETE_BUTTON_OBJECT_NAME,
    DELETE_BUTTON_SIZE,
    DIALOG_TITLE_ERROR,
    DIALOG_TITLE_PARAMETER_ERROR,
    DIALOG_TITLE_PHYSICS_ERROR,
    ERROR_COLLISION,
    ERROR_DUPLICATE_NAME,
    MANAGER_COLOR_BUTTON_STYLE,
    MANAGER_MIN_HEIGHT,
    MANAGER_MIN_WIDTH,
    MANAGER_STYLE_SHEET,
    MANAGER_WINDOW_TITLE,
    PREVIEW_LOG_FACTOR,
    PREVIEW_MAX_RADIUS,
    PREVIEW_MIN_RADIUS,
    PREVIEW_WIDGET_SIZE,
    TABLE_HEADERS,
    TABLE_ROW_HEIGHT,
    TEXT_CLOSE,
    TEXT_DELETE,
)
from config.models import BodyState
from core.planets_validator import ScenarioValidator


class PlanetPreviewWidget(QWidget):
    def __init__(self, color_hex: str, real_radius: float, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.color = QColor(color_hex)
        self.real_radius = real_radius
        self.setFixedSize(PREVIEW_WIDGET_SIZE, PREVIEW_WIDGET_SIZE)

    def update_params(self, color_hex: str, radius: float) -> None:
        self.color = QColor(color_hex)
        self.real_radius = radius
        self.update()

    def paintEvent(self, _event: QPaintEvent | None) -> None:
        if self.real_radius <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        visual_r = min(
            PREVIEW_MAX_RADIUS,
            max(PREVIEW_MIN_RADIUS, math.log10(self.real_radius + 1) * PREVIEW_LOG_FACTOR),
        )

        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        painter.drawEllipse(
            QPointF(PREVIEW_WIDGET_SIZE / 2, PREVIEW_WIDGET_SIZE / 2), visual_r, visual_r
        )


class PlanetsManagerDialog(QDialog):
    planet_removed = pyqtSignal(int)
    planet_modified = pyqtSignal(int)

    def __init__(self, planets_info: list[BodyState], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.planets_info = planets_info

        self.setWindowTitle(MANAGER_WINDOW_TITLE)
        self.setMinimumSize(MANAGER_MIN_WIDTH, MANAGER_MIN_HEIGHT)
        self.setStyleSheet(MANAGER_STYLE_SHEET)

        self.table: QTableWidget
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, len(TABLE_HEADERS))
        self.table.setHorizontalHeaderLabels(TABLE_HEADERS)

        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        v_header = self.table.verticalHeader()
        if v_header:
            v_header.setDefaultSectionSize(TABLE_ROW_HEIGHT)
            v_header.setVisible(False)

        cast(Any, self.table.cellChanged).connect(self._on_cell_changed)
        self.refresh_table()

        layout.addWidget(self.table)

        btn_close = QPushButton(TEXT_CLOSE)
        btn_close.setObjectName(CLOSE_BUTTON_OBJECT_NAME)
        btn_close.setFixedHeight(CLOSE_BUTTON_HEIGHT)
        cast(Any, btn_close.clicked).connect(self.accept)
        layout.addWidget(btn_close)

    def refresh_table(self) -> None:
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        for i, planet in enumerate(self.planets_info):
            self.table.insertRow(i)
            self.table.setCellWidget(
                i,
                COL_PREVIEW,
                self._create_center_widget(PlanetPreviewWidget(planet.color, planet.radius)),
            )

            btn_color = QPushButton()
            btn_color.setFixedSize(COLOR_BUTTON_WIDTH, COLOR_BUTTON_HEIGHT)
            btn_color.setStyleSheet(MANAGER_COLOR_BUTTON_STYLE.format(planet.color))
            # Используем параметр по умолчанию в lambda, чтобы захватить текущее значение i
            cast(Any, btn_color.clicked).connect(lambda _checked, idx=i: self._change_color(idx))
            self.table.setCellWidget(i, COL_COLOR, self._create_center_widget(btn_color))

            self.table.setItem(i, COL_NAME, QTableWidgetItem(planet.name))
            self.table.setItem(i, COL_MASS, QTableWidgetItem(str(planet.mass)))
            self.table.setItem(i, COL_RADIUS, QTableWidgetItem(str(planet.radius)))
            self.table.setItem(i, COL_X, QTableWidgetItem(str(planet.position[0])))
            self.table.setItem(i, COL_Y, QTableWidgetItem(str(planet.position[1])))
            self.table.setItem(i, COL_VX, QTableWidgetItem(str(planet.velocity[0])))
            self.table.setItem(i, COL_VY, QTableWidgetItem(str(planet.velocity[1])))

            btn_del = QPushButton(TEXT_DELETE)
            btn_del.setObjectName(DELETE_BUTTON_OBJECT_NAME)
            btn_del.setFixedSize(DELETE_BUTTON_SIZE, DELETE_BUTTON_SIZE)
            cast(Any, btn_del.clicked).connect(lambda _checked, idx=i: self._on_delete(idx))
            self.table.setCellWidget(i, COL_DELETE, self._create_center_widget(btn_del))

        self.table.blockSignals(False)

    @staticmethod
    def _create_center_widget(widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return container

    def _on_cell_changed(self, row: int, col: int) -> None:
        item = self.table.item(row, col)
        if not item:
            return

        val_text = item.text().replace(",", ".")

        try:
            temp_body = replace(self.planets_info[row])

            if col == COL_NAME:
                temp_body.name = val_text.strip()
            elif col == COL_MASS:
                temp_body.mass = float(val_text)
            elif col == COL_RADIUS:
                temp_body.radius = float(val_text)
            elif col == COL_X:
                temp_body.position = (float(val_text), temp_body.position[1])
            elif col == COL_Y:
                temp_body.position = (temp_body.position[0], float(val_text))
            elif col == COL_VX:
                temp_body.velocity = (float(val_text), temp_body.velocity[1])
            elif col == COL_VY:
                temp_body.velocity = (temp_body.velocity[0], float(val_text))
            phys_error = ScenarioValidator.validate_body_params(temp_body)
            if phys_error:
                QMessageBox.warning(self, DIALOG_TITLE_PARAMETER_ERROR, phys_error)
                self.refresh_table()
                return
            if col == COL_NAME and not ScenarioValidator.check_name_uniqueness(
                temp_body.name, self.planets_info, exclude_idx=row
            ):
                QMessageBox.warning(
                    self, DIALOG_TITLE_ERROR, ERROR_DUPLICATE_NAME.format(temp_body.name)
                )
                self.refresh_table()
                return
            if col in (COL_RADIUS, COL_X, COL_Y):
                conflict = ScenarioValidator.check_collision(
                    temp_body, self.planets_info, exclude_idx=row
                )
                if conflict:
                    QMessageBox.warning(
                        self,
                        DIALOG_TITLE_PHYSICS_ERROR,
                        ERROR_COLLISION.format(temp_body.name, conflict),
                    )
                    self.refresh_table()
                    return
            self.planets_info[row] = temp_body
            if col == COL_RADIUS:
                self._update_row_widgets(row)

            cast(Any, self.planet_modified).emit(row)

        except ValueError:
            self.refresh_table()

    def _update_row_widgets(self, row: int) -> None:
        planet = self.planets_info[row]
        container_preview = self.table.cellWidget(row, COL_PREVIEW)
        if container_preview:
            preview = container_preview.findChild(PlanetPreviewWidget)
            if isinstance(preview, PlanetPreviewWidget):
                preview.update_params(planet.color, planet.radius)

        container_color = self.table.cellWidget(row, COL_COLOR)
        if container_color:
            btn = container_color.findChild(QPushButton)
            if isinstance(btn, QPushButton):
                btn.setStyleSheet(MANAGER_COLOR_BUTTON_STYLE.format(planet.color))

    def _change_color(self, index: int) -> None:
        planet = self.planets_info[index]
        color = QColorDialog.getColor(QColor(planet.color), self)
        if color.isValid():
            planet.color = color.name()
            self._update_row_widgets(index)
            cast(Any, self.planet_modified).emit(index)

    def _on_delete(self, index: int) -> None:
        cast(Any, self.planet_removed).emit(index)
        self.refresh_table()
