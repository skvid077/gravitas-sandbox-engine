import math
from typing import List, Optional

from pydantic import ValidationError
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QPushButton, QColorDialog, QWidget, QMessageBox
)
from PyQt6.QtGui import QDoubleValidator, QColor, QPainter, QBrush, QPen, QPaintEvent
from PyQt6.QtCore import Qt, QPointF, QLocale

from config.schemas import BodyState
from core.planets_validator import check_collision, check_name_uniqueness, validate_body_params
from config.constants import (
    STYLE_BTN_MENU_CONTINUE,
    STYLE_BTN_MENU,
    PREVIEW_SIZE,
    PREVIEW_CENTER,
    PREVIEW_MAX_VISUAL_R,
    PREVIEW_MIN_VISUAL_R,
    PREVIEW_LOG_BASE,
    DIALOG_WIDTH,
    DIALOG_HEIGHT,
    DEFAULT_COLOR,
    DEFAULT_NAME,
    DEFAULT_MASS,
    DEFAULT_RADIUS
)


class PlanetPreviewWidget(QWidget):
    """
    Виджет для отображения логарифмического превью планеты.
    Позволяет визуально оценить размер и цвет тела перед добавлением.
    """
    def __init__(self, color_hex: str, radius: float, parent: Optional[QWidget] = None) -> None:
        """
        Инициализирует виджет превью.

        Args:
            color_hex (str): HEX-код цвета.
            radius (float): Реальный физический радиус.
            parent (Optional[QWidget]): Родительский виджет.
        """
        super().__init__(parent)
        self.color = QColor(color_hex)
        self.radius = radius
        self.setFixedSize(PREVIEW_SIZE, PREVIEW_SIZE)

    def update_params(self, color: QColor, radius: float) -> None:
        """Обновляет параметры и перерисовывает виджет."""
        self.color = color
        self.radius = radius
        self.update()

    def paintEvent(self, event: Optional[QPaintEvent]) -> None:
        """Отрисовывает планету с использованием логарифмического масштаба."""
        if event is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.radius <= 0:
            return

        # Логарифмический масштаб для превью
        visual_r = min(
            PREVIEW_MAX_VISUAL_R, 
            max(PREVIEW_MIN_VISUAL_R, math.log10(self.radius + 1) * PREVIEW_LOG_BASE)
        )
        
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.drawEllipse(QPointF(PREVIEW_CENTER, PREVIEW_CENTER), visual_r, visual_r)


class AddPlanetDialog(QDialog):
    """
    Диалоговое окно для создания нового небесного тела или редактирования существующего.
    Включает в себя форму ввода параметров и интерактивное превью.
    """
    def __init__(self, planets_info: List[BodyState], parent: Optional[QWidget] = None, edit_body: Optional[BodyState] = None) -> None:
        """
        Инициализирует диалог.

        Args:
            planets_info (List[BodyState]): Список существующих тел для проверки коллизий.
            parent (Optional[QWidget]): Родительское окно.
            edit_body (Optional[BodyState]): Объект для редактирования. Если None — создается новая планета.
        """
        super().__init__(parent)
        self.planets_info = planets_info
        self.edit_body = edit_body
        
        title = "Редактирование тела" if edit_body else "Параметры нового тела"
        self.setWindowTitle(title)
        self.setFixedSize(DIALOG_WIDTH, DIALOG_HEIGHT)
        
        self.selected_color = QColor(edit_body.color if edit_body else DEFAULT_COLOR)
        
        # Декларация атрибутов для mypy
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
        """Создает форму ввода и элементы управления."""
        main_layout = QHBoxLayout(self)
        form_container = QWidget()
        form_layout = QFormLayout(form_container)
        
        val = QDoubleValidator(self)
        val.setLocale(QLocale(QLocale.Language.English))

        b = self.edit_body
        self.in_name = QLineEdit(b.name if b else DEFAULT_NAME)
        self.in_mass = self._create_input(str(b.mass) if b else DEFAULT_MASS, val)
        self.in_radius = self._create_input(str(b.radius) if b else DEFAULT_RADIUS, val)
        self.in_x = self._create_input(str(b.position[0]) if b else "0.0", val)
        self.in_y = self._create_input(str(b.position[1]) if b else "0.0", val)
        self.in_vx = self._create_input(str(b.velocity[0]) if b else "0.0", val)
        self.in_vy = self._create_input(str(b.velocity[1]) if b else "0.0", val)

        self.in_radius.textChanged.connect(self._sync_preview)

        form_layout.addRow("Имя:", self.in_name)
        form_layout.addRow("Масса:", self.in_mass)
        form_layout.addRow("Радиус:", self.in_radius)
        form_layout.addRow("X:", self.in_x)
        form_layout.addRow("Y:", self.in_y)
        form_layout.addRow("Vx:", self.in_vx)
        form_layout.addRow("Vy:", self.in_vy)

        self.btn_col = QPushButton("Цвет")
        self.btn_col.setStyleSheet(f"background-color: {self.selected_color.name()}; border-radius: 6px; height: 25px;")
        self.btn_col.clicked.connect(self._pick_color)
        form_layout.addRow(self.btn_col)

        right_panel = QVBoxLayout()
        initial_radius = b.radius if b else float(DEFAULT_RADIUS)
        self.preview = PlanetPreviewWidget(self.selected_color.name(), initial_radius)
        right_panel.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignCenter)
        right_panel.addStretch()
        
        btn_ok_text = "Сохранить" if self.edit_body else "Добавить"
        btn_ok = QPushButton(btn_ok_text)
        btn_ok.setStyleSheet(STYLE_BTN_MENU_CONTINUE)
        btn_ok.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setStyleSheet(STYLE_BTN_MENU)
        btn_cancel.clicked.connect(self.reject)
        
        right_panel.addWidget(btn_ok)
        right_panel.addWidget(btn_cancel)

        main_layout.addWidget(form_container)
        main_layout.addLayout(right_panel)

    def _create_input(self, text: str, validator: QDoubleValidator) -> QLineEdit:
        """Создает поле ввода с валидатором числовых значений."""
        line = QLineEdit(text)
        line.setValidator(validator)
        return line

    def _sync_preview(self) -> None:
        """Синхронизирует виджет превью с введенным радиусом."""
        try:
            text = self.in_radius.text().replace(',', '.')
            r = float(text) if text else 0.0
            self.preview.update_params(self.selected_color, r)
        except ValueError: 
            pass

    def _pick_color(self) -> None:
        """Открывает диалог выбора цвета."""
        color = QColorDialog.getColor(self.selected_color, self)
        if color.isValid():
            self.selected_color = color
            self.btn_col.setStyleSheet(f"background-color: {self.selected_color.name()}; border-radius: 6px; height: 25px;")
            self._sync_preview()

    def accept(self) -> None:
        """Выполняет валидацию данных и закрывает диалог с сохранением."""
        try:
            new_planet_data = self.get_planet_data()
            
            exclude_idx = None
            if self.edit_body and self.edit_body in self.planets_info:
                exclude_idx = self.planets_info.index(self.edit_body)

            # Валидация физики, имен и коллизий
            phys_error = validate_body_params(new_planet_data)
            if phys_error:
                QMessageBox.warning(self, "Ошибка параметров", phys_error)
                return

            if not check_name_uniqueness(new_planet_data.name, self.planets_info, exclude_idx=exclude_idx):
                QMessageBox.warning(self, "Ошибка", f"Имя '{new_planet_data.name}' уже занято.")
                return

            conflict = check_collision(new_planet_data, self.planets_info, exclude_idx=exclude_idx)
            if conflict:
                QMessageBox.warning(self, "Ошибка", f"Пересечение с телом '{conflict}'!")
                return

            # Обновление существующего объекта
            if self.edit_body:
                self.edit_body.name = new_planet_data.name
                self.edit_body.mass = new_planet_data.mass
                self.edit_body.radius = new_planet_data.radius
                self.edit_body.position = new_planet_data.position
                self.edit_body.velocity = new_planet_data.velocity
                self.edit_body.color = new_planet_data.color
            
            super().accept()

        except ValidationError as e:
            error_msg = "\n".join([f"- {err['msg']}" for err in e.errors()])
            QMessageBox.critical(self, "Ошибка валидации", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def get_planet_data(self) -> BodyState:
        """
        Собирает данные из полей ввода и формирует объект BodyState.
        
        Returns:
            BodyState: Сформированный объект состояния тела.
        """
        def f(x: str) -> float:
            val = x.replace(',', '.')
            return float(val) if val.strip() and val != "." else 0.0

        return BodyState(
            name=self.in_name.text().strip(),
            mass=f(self.in_mass.text()),
            radius=f(self.in_radius.text()),
            position=(f(self.in_x.text()), f(self.in_y.text())),
            velocity=(f(self.in_vx.text()), f(self.in_vy.text())),
            color=self.selected_color.name()
        )
