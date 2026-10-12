import math
from typing import Any, cast

from PyQt6.QtCore import QLocale, QPointF, Qt
from PyQt6.QtGui import QBrush, QColor, QDoubleValidator, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import (
    QColorDialog,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.constants import (
    DEFAULT_COLOR,
    DEFAULT_COORDINATE_TEXT,
    DEFAULT_MASS,
    DEFAULT_NAME,
    DEFAULT_RADIUS,
    DIALOG_EDIT_BODY_TITLE,
    DIALOG_HEIGHT,
    DIALOG_NEW_BODY_TITLE,
    DIALOG_TITLE_ERROR,
    DIALOG_TITLE_PARAMETER_ERROR,
    DIALOG_WIDTH,
    ERROR_COLLISION,
    ERROR_DUPLICATE_NAME,
    LABEL_COLOR,
    LABEL_MASS,
    LABEL_NAME,
    LABEL_RADIUS,
    LABEL_VX,
    LABEL_VY,
    LABEL_X,
    LABEL_Y,
    PLANET_COLOR_BUTTON_STYLE,
    PREVIEW_CENTER,
    PREVIEW_LOG_BASE,
    PREVIEW_MAX_VISUAL_R,
    PREVIEW_MIN_VISUAL_R,
    PREVIEW_SIZE,
    STYLE_BTN_MENU,
    STYLE_BTN_MENU_CONTINUE,
    TEXT_ADD,
    TEXT_CANCEL,
    TEXT_SAVE,
)
from config.models import BodyState
from core.planets_validator import ScenarioValidator


class PlanetPreviewWidget(QWidget):
    def __init__(self, color_hex: str, radius: float, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.color = QColor(color_hex)
        self.radius = radius
        self.setFixedSize(PREVIEW_SIZE, PREVIEW_SIZE)

    def update_params(self, color: QColor, radius: float) -> None:
        self.color = color
        self.radius = radius
        self.update()

    def paintEvent(self, event: QPaintEvent | None) -> None:
        if event is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.radius <= 0:
            return
        visual_r = min(
            PREVIEW_MAX_VISUAL_R,
            max(PREVIEW_MIN_VISUAL_R, math.log10(self.radius + 1) * PREVIEW_LOG_BASE),
        )

        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.drawEllipse(QPointF(PREVIEW_CENTER, PREVIEW_CENTER), visual_r, visual_r)


class AddPlanetDialog(QDialog):
    def __init__(
        self,
        planets_info: list[BodyState],
        parent: QWidget | None = None,
        edit_body: BodyState | None = None,
    ) -> None:
        super().__init__(parent)
        self.planets_info = planets_info
        self.edit_body = edit_body

        title = DIALOG_EDIT_BODY_TITLE if edit_body else DIALOG_NEW_BODY_TITLE
        self.setWindowTitle(title)
        self.setFixedSize(DIALOG_WIDTH, DIALOG_HEIGHT)

        self.selected_color = QColor(edit_body.color if edit_body else DEFAULT_COLOR)
        self.in_name: QLineEdit
        self.in_mass: QLineEdit
        self.in_radius: QLineEdit
        self.in_x: QLineEdit
        self.in_y: QLineEdit
        self.in_vx: QLineEdit
        self.in_vy: QLineEdit
        self.btn_col: QPushButton
        self.preview: PlanetPreviewWidget

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        form_container = QWidget()
        form_layout = QFormLayout(form_container)

        val = QDoubleValidator(self)
        val.setLocale(QLocale(QLocale.Language.English))

        b = self.edit_body
        self.in_name = QLineEdit(b.name if b else DEFAULT_NAME)
        self.in_mass = self._create_input(str(b.mass) if b else DEFAULT_MASS, val)
        self.in_radius = self._create_input(str(b.radius) if b else DEFAULT_RADIUS, val)
        self.in_x = self._create_input(str(b.position[0]) if b else DEFAULT_COORDINATE_TEXT, val)
        self.in_y = self._create_input(str(b.position[1]) if b else DEFAULT_COORDINATE_TEXT, val)
        self.in_vx = self._create_input(str(b.velocity[0]) if b else DEFAULT_COORDINATE_TEXT, val)
        self.in_vy = self._create_input(str(b.velocity[1]) if b else DEFAULT_COORDINATE_TEXT, val)

        cast(Any, self.in_radius.textChanged).connect(self._sync_preview)

        form_layout.addRow(LABEL_NAME, self.in_name)
        form_layout.addRow(LABEL_MASS, self.in_mass)
        form_layout.addRow(LABEL_RADIUS, self.in_radius)
        form_layout.addRow(LABEL_X, self.in_x)
        form_layout.addRow(LABEL_Y, self.in_y)
        form_layout.addRow(LABEL_VX, self.in_vx)
        form_layout.addRow(LABEL_VY, self.in_vy)

        self.btn_col = QPushButton(LABEL_COLOR)
        self.btn_col.setStyleSheet(PLANET_COLOR_BUTTON_STYLE.format(self.selected_color.name()))
        cast(Any, self.btn_col.clicked).connect(self._pick_color)
        form_layout.addRow(self.btn_col)

        right_panel = QVBoxLayout()
        initial_radius = b.radius if b else float(DEFAULT_RADIUS)
        self.preview = PlanetPreviewWidget(self.selected_color.name(), initial_radius)
        right_panel.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignCenter)
        right_panel.addStretch()

        btn_ok_text = TEXT_SAVE if self.edit_body else TEXT_ADD
        btn_ok = QPushButton(btn_ok_text)
        btn_ok.setStyleSheet(STYLE_BTN_MENU_CONTINUE)
        cast(Any, btn_ok.clicked).connect(self.accept)

        btn_cancel = QPushButton(TEXT_CANCEL)
        btn_cancel.setStyleSheet(STYLE_BTN_MENU)
        cast(Any, btn_cancel.clicked).connect(self.reject)

        right_panel.addWidget(btn_ok)
        right_panel.addWidget(btn_cancel)

        main_layout.addWidget(form_container)
        main_layout.addLayout(right_panel)

    @staticmethod
    def _create_input(text: str, validator: QDoubleValidator) -> QLineEdit:
        line = QLineEdit(text)
        line.setValidator(validator)
        return line

    def _sync_preview(self) -> None:
        try:
            text = self.in_radius.text().replace(",", ".")
            r = float(text) if text else 0.0
            self.preview.update_params(self.selected_color, r)
        except ValueError:
            pass

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(self.selected_color, self)
        if color.isValid():
            self.selected_color = color
            self.btn_col.setStyleSheet(PLANET_COLOR_BUTTON_STYLE.format(self.selected_color.name()))
            self._sync_preview()

    def accept(self) -> None:
        try:
            new_planet_data = self.get_planet_data()

            exclude_idx = None
            if self.edit_body and self.edit_body in self.planets_info:
                exclude_idx = self.planets_info.index(self.edit_body)
            phys_error = ScenarioValidator.validate_body_params(new_planet_data)
            if phys_error:
                QMessageBox.warning(self, DIALOG_TITLE_PARAMETER_ERROR, phys_error)
                return

            if not ScenarioValidator.check_name_uniqueness(
                new_planet_data.name, self.planets_info, exclude_idx=exclude_idx
            ):
                QMessageBox.warning(
                    self, DIALOG_TITLE_ERROR, ERROR_DUPLICATE_NAME.format(new_planet_data.name)
                )
                return

            conflict = ScenarioValidator.check_collision(
                new_planet_data, self.planets_info, exclude_idx=exclude_idx
            )
            if conflict:
                QMessageBox.warning(
                    self,
                    DIALOG_TITLE_ERROR,
                    ERROR_COLLISION.format(new_planet_data.name, conflict),
                )
                return
            if self.edit_body:
                self.edit_body.name = new_planet_data.name
                self.edit_body.mass = new_planet_data.mass
                self.edit_body.radius = new_planet_data.radius
                self.edit_body.position = new_planet_data.position
                self.edit_body.velocity = new_planet_data.velocity
                self.edit_body.color = new_planet_data.color

            super().accept()

        except ValueError as error:
            QMessageBox.critical(self, DIALOG_TITLE_ERROR, str(error))

    def get_planet_data(self) -> BodyState:
        def f(x: str) -> float:
            val = x.replace(",", ".")
            return float(val) if val.strip() and val != "." else 0.0

        return BodyState(
            name=self.in_name.text().strip(),
            mass=f(self.in_mass.text()),
            radius=f(self.in_radius.text()),
            position=(f(self.in_x.text()), f(self.in_y.text())),
            velocity=(f(self.in_vx.text()), f(self.in_vy.text())),
            color=self.selected_color.name(),
        )
