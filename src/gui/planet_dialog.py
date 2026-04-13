from typing import Optional, List
from pydantic import ValidationError

from PyQt6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget
)
from PyQt6.QtGui import QColor

from config.constants import *
from config.schemas import BodyState


class PlanetDialog(QDialog):
    """
    Диалоговое окно для создания или редактирования параметров физического тела (планеты).
    
    Обеспечивает ввод данных пользователем, первичную UI-валидацию (проверку 
    уникальности имени и предотвращение коллизий геометрии) и формирует 
    валидный объект BodyState.
    """

    def __init__(
        self, 
        parent: Optional[QWidget] = None, 
        default_x: float = 0.0, 
        default_y: float = 0.0, 
        existing_body: Optional[BodyState] = None, 
        all_bodies: Optional[List[BodyState]] = None
    ) -> None:
        """
        Инициализирует диалоговое окно настроек планеты.

        Args:
            parent (Optional[QWidget]): Родительский виджет окна.
            default_x (float): Координата X по умолчанию (для спавна новой планеты).
            default_y (float): Координата Y по умолчанию.
            existing_body (Optional[BodyState]): Состояние планеты при редактировании.
            all_bodies (Optional[List[BodyState]]): Список всех планет для проверки коллизий.
        """
        super().__init__(parent)
        self.setWindowTitle("Настройки планеты")
        self.setMinimumWidth(350)
        
        # Инкапсуляция внутреннего состояния
        self._all_bodies: List[BodyState] = all_bodies or []
        self._existing_body: Optional[BodyState] = existing_body
        self._color_hex: str = existing_body.color if existing_body else "#FFFFFF"
        self._final_body_state: Optional[BodyState] = None

        self.layout = QFormLayout(self)
        self._init_ui(default_x, default_y)

    @property
    def final_body_state(self) -> Optional[BodyState]:
        """
        Optional[BodyState]: Геттер для получения итогового состояния планеты 
        после успешной валидации и закрытия окна.
        """
        return self._final_body_state

    def _init_ui(self, default_x: float, default_y: float) -> None:
        """
        Создает и размещает элементы пользовательского интерфейса.
        """
        # --- Имя ---
        initial_name: str = self._existing_body.name if self._existing_body else "Новая Планета"
        self.name_input = QLineEdit(initial_name)
        self.layout.addRow("Имя:", self.name_input)

        # --- Цвет ---
        self.color_btn = QPushButton()
        self.color_btn.setStyleSheet(f"background-color: {self._color_hex};")
        self.color_btn.clicked.connect(self._choose_color)
        self.layout.addRow("Цвет:", self.color_btn)

        # --- Масса и Радиус ---
        initial_mass: float = self._existing_body.mass if self._existing_body else 100.0
        self.mass_input = self._create_spinbox(MIN_MASS, MAX_MASS, initial_mass)
        self.layout.addRow("Масса:", self.mass_input)

        initial_radius: float = self._existing_body.radius if self._existing_body else 20.0
        self.radius_input = self._create_spinbox(MIN_RADIUS, MAX_RADIUS, initial_radius)
        self.layout.addRow("Радиус:", self.radius_input)

        # --- Позиция ---
        pos_x_val: float = self._existing_body.position[0] if self._existing_body else default_x
        pos_y_val: float = self._existing_body.position[1] if self._existing_body else default_y
        
        self.pos_x = self._create_spinbox(MIN_COORD, MAX_COORD, pos_x_val)
        self.pos_y = self._create_spinbox(MIN_COORD, MAX_COORD, pos_y_val)
        
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(self.pos_x)
        pos_layout.addWidget(self.pos_y)
        self.layout.addRow("Позиция (X, Y):", pos_layout)

        # --- Скорость ---
        vel_x_val: float = self._existing_body.velocity[0] if self._existing_body else 0.0
        vel_y_val: float = self._existing_body.velocity[1] if self._existing_body else 0.0
        
        self.vel_x = self._create_spinbox(MIN_VEL, MAX_VEL, vel_x_val)
        self.vel_y = self._create_spinbox(MIN_VEL, MAX_VEL, vel_y_val)
        
        vel_layout = QHBoxLayout()
        vel_layout.addWidget(self.vel_x)
        vel_layout.addWidget(self.vel_y)
        self.layout.addRow("Скорость (Vx, Vy):", vel_layout)

        # --- Кнопки управления ---
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def _create_spinbox(self, min_val: float, max_val: float, default_val: float) -> QDoubleSpinBox:
        """
        Фабричный метод для создания числовых полей ввода с заданными лимитами.
        """
        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default_val)
        return spinbox

    def _choose_color(self) -> None:
        """
        Открывает системный диалог выбора цвета и применяет его к кнопке.
        """
        color: QColor = QColorDialog.getColor()
        if color.isValid():
            self._color_hex = color.name().upper()
            self.color_btn.setStyleSheet(f"background-color: {self._color_hex};")

    def _has_collisions(self, new_state: BodyState) -> bool:
        """
        Проверяет геометрические пересечения создаваемой/редактируемой планеты 
        с остальными объектами симуляции.
        """
        for body in self._all_bodies:
            if body is self._existing_body:
                continue
            
            dx: float = new_state.position[0] - body.position[0]
            dy: float = new_state.position[1] - body.position[1]
            min_distance: float = new_state.radius + body.radius
            
            # Сравнение квадратов расстояний
            if (dx * dx + dy * dy) < (min_distance * min_distance):
                return True
        return False

    def accept(self) -> None:
        """
        Обработчик подтверждения формы (кнопка OK).
        Проводит проверки бизнес-логики и валидацию Pydantic.
        """
        new_name: str = self.name_input.text().strip()
        
        # 1. Проверка уникальности имени
        for body in self._all_bodies:
            if body is not self._existing_body and body.name == new_name:
                QMessageBox.warning(
                    self, 
                    "Ошибка имени", 
                    f"Планета с именем '{new_name}' уже существует!\nПожалуйста, выберите уникальное имя."
                )
                return 

        try:
            # 2. Создание объекта (делегирование строгой проверки типов схеме Pydantic)
            temp_state = BodyState(
                name=new_name,
                color=self._color_hex,
                mass=self.mass_input.value(),
                radius=self.radius_input.value(),
                position=(self.pos_x.value(), self.pos_y.value()),
                velocity=(self.vel_x.value(), self.vel_y.value())
            )
            
            # 3. Проверка коллизий на сцене
            if self._has_collisions(temp_state):
                QMessageBox.warning(
                    self, 
                    "Космо-ДТП!", 
                    "Планета пересекается с другим объектом.\nИзмените координаты или радиус."
                )
                return

            # Если всё прошло успешно, фиксируем состояние и закрываем окно
            self._final_body_state = temp_state
            super().accept()
            
        except ValidationError as e:
            error_messages: str = "\n".join([f"- Поле '{err['loc'][0]}': {err['msg']}" for err in e.errors()])
            QMessageBox.warning(
                self, 
                "Ошибка ввода", 
                f"Пожалуйста, исправьте следующие ошибки:\n{error_messages}"
            )
