import math
from pydantic import ValidationError
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QPushButton, QLabel, QColorDialog, QWidget, QMessageBox
)
from PyQt6.QtGui import QDoubleValidator, QColor, QPainter, QBrush, QPen
from PyQt6.QtCore import Qt, QPointF, QLocale

from config.schemas import BodyState
from config.constants import STYLE_BTN_MENU_CONTINUE, STYLE_BTN_MENU
from core.planets_validator import check_collision, check_name_uniqueness, validate_body_params

class PlanetPreviewWidget(QWidget):
    """Виджет логарифмического превью для окна создания/редактирования."""
    def __init__(self, color_hex: str, radius: float, parent=None):
        super().__init__(parent)
        self.color = QColor(color_hex)
        self.radius = radius
        self.setFixedSize(120, 120)

    def update_params(self, color: QColor, radius: float):
        self.color = color
        self.radius = radius
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.radius <= 0:
            return

        # Логарифмический масштаб для превью
        visual_r = min(50.0, max(4.0, math.log10(self.radius + 1) * 12.0))
        
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.drawEllipse(QPointF(60, 60), visual_r, visual_r)

class AddPlanetDialog(QDialog):
    def __init__(self, planets_info: list, parent=None, edit_body: BodyState = None):
        super().__init__(parent)
        self.planets_info = planets_info
        self.edit_body = edit_body
        
        # Динамическая настройка заголовка в зависимости от режима
        title = "Редактирование тела" if edit_body else "Параметры нового тела"
        self.setWindowTitle(title)
        self.setFixedSize(500, 480)
        
        # Инициализация цвета из параметров редактируемой планеты или дефолтного
        self.selected_color = QColor(edit_body.color if edit_body else "#FF6464")
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        form_container = QWidget()
        form_layout = QFormLayout(form_container)
        
        val = QDoubleValidator(self)
        val.setLocale(QLocale(QLocale.Language.English))

        # Предзаполнение полей данными, если передан объект для редактирования
        b = self.edit_body
        self.in_name = QLineEdit(b.name if b else "Planet X")
        self.in_mass = self._create_input(str(b.mass) if b else "1000.0", val)
        self.in_radius = self._create_input(str(b.radius) if b else "20.0", val)
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
        # Превью сразу отображает текущий радиус
        initial_radius = b.radius if b else 20.0
        self.preview = PlanetPreviewWidget(self.selected_color.name(), initial_radius)
        right_panel.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignCenter)
        right_panel.addStretch()
        
        # Текст кнопки подтверждения зависит от режима
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

    def _create_input(self, text, validator):
        line = QLineEdit(text)
        line.setValidator(validator)
        return line

    def _sync_preview(self):
        try:
            text = self.in_radius.text().replace(',', '.')
            r = float(text) if text else 0.0
            self.preview.update_params(self.selected_color, r)
        except ValueError: 
            pass

    def _pick_color(self):
        color = QColorDialog.getColor(self.selected_color, self)
        if color.isValid():
            self.selected_color = color
            self.btn_col.setStyleSheet(f"background-color: {self.selected_color.name()}; border-radius: 6px; height: 25px;")
            self._sync_preview()

    def accept(self):
        """Метод подтверждения с полной валидацией и обновлением данных."""
        try:
            new_planet_data = self.get_planet_data()
            
            # Находим индекс текущей планеты, чтобы исключить её из проверок уникальности
            exclude_idx = None
            if self.edit_body and self.edit_body in self.planets_info:
                exclude_idx = self.planets_info.index(self.edit_body)

            # 1. Проверка физических параметров (масса/радиус > 0)
            phys_error = validate_body_params(new_planet_data)
            if phys_error:
                QMessageBox.warning(self, "Ошибка параметров", phys_error)
                return

            # 2. Проверка уникальности имени с учетом исключения текущего объекта
            if not check_name_uniqueness(new_planet_data.name, self.planets_info, exclude_idx=exclude_idx):
                QMessageBox.warning(self, "Ошибка", f"Имя '{new_planet_data.name}' уже занято.")
                return

            # 3. Проверка коллизий (пересечений)
            conflict = check_collision(new_planet_data, self.planets_info, exclude_idx=exclude_idx)
            if conflict:
                QMessageBox.warning(self, "Ошибка", f"Пересечение с телом '{conflict}'!")
                return

            # Если мы в режиме редактирования, обновляем поля оригинального объекта
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
        """Сборка текущих данных из формы в модель BodyState."""
        f = lambda x: float(x.replace(',', '.')) if x.strip() else 0.0
        return BodyState(
            name=self.in_name.text().strip(),
            mass=f(self.in_mass.text()),
            radius=f(self.in_radius.text()),
            position=(f(self.in_x.text()), f(self.in_y.text())),
            velocity=(f(self.in_vx.text()), f(self.in_vy.text())),
            color=self.selected_color.name()
        )
