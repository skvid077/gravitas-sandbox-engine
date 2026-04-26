import math
from typing import List, Optional

from pydantic import ValidationError
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QHBoxLayout, QWidget, QColorDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QPaintEvent

from config.schemas import BodyState
from core.planets_validator import check_collision, check_name_uniqueness, validate_body_params
from config.constants import (
    PREVIEW_LOG_FACTOR,
    PREVIEW_MIN_RADIUS,
    MANAGER_STYLE_SHEET,
    TABLE_HEADERS,
    COL_PREVIEW,
    COL_COLOR,
    COL_NAME,
    COL_MASS,
    COL_RADIUS,
    COL_X,
    COL_Y,
    COL_VX,
    COL_VY,
    COL_DELETE,
    MANAGER_WINDOW_TITLE,
    MANAGER_MIN_WIDTH,
    MANAGER_MIN_HEIGHT,
    PREVIEW_WIDGET_SIZE,
    PREVIEW_MAX_RADIUS
)

class PlanetPreviewWidget(QWidget):
    """
    Виджет для отрисовки графического превью планеты внутри ячейки таблицы.
    Использует логарифмический масштаб для безопасного отображения огромных радиусов.
    """

    def __init__(self, color_hex: str, real_radius: float, parent: Optional[QWidget] = None) -> None:
        """
        Инициализирует виджет превью.

        Args:
            color_hex (str): Цвет планеты в HEX формате (например, '#FFFFFF').
            real_radius (float): Физический радиус планеты.
            parent (Optional[QWidget], optional): Родительский виджет. По умолчанию None.
        """
        super().__init__(parent)
        self.color = QColor(color_hex)
        self.real_radius = real_radius
        self.setFixedSize(PREVIEW_WIDGET_SIZE, PREVIEW_WIDGET_SIZE)

    def update_params(self, color_hex: str, radius: float) -> None:
        """
        Обновляет параметры отображения и вызывает перерисовку виджета.

        Args:
            color_hex (str): Новый цвет.
            radius (float): Новый физический радиус.
        """
        self.color = QColor(color_hex)
        self.real_radius = radius
        self.update()

    def paintEvent(self, event: Optional[QPaintEvent]) -> None:
        """
        Отрисовывает круг планеты в логарифмическом масштабе.
        
        Args:
            event (Optional[QPaintEvent]): Событие отрисовки PyQt.
        """
        # ЗАЩИТА: Если радиус некорректный, не рисуем ничего, чтобы math.log10 не упал
        if self.real_radius <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Логарифмический масштаб: даже очень большие радиусы не выйдут за PREVIEW_MAX_RADIUS
        visual_r = min(
            PREVIEW_MAX_RADIUS, 
            max(PREVIEW_MIN_RADIUS, math.log10(self.real_radius + 1) * PREVIEW_LOG_FACTOR)
        )

        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        painter.drawEllipse(QPointF(PREVIEW_WIDGET_SIZE / 2, PREVIEW_WIDGET_SIZE / 2), visual_r, visual_r)


class PlanetsManagerDialog(QDialog):
    """
    Диалоговое окно для детального управления всеми объектами симуляции.
    Представляет данные в виде редактируемой таблицы с валидацией изменений "на лету".
    """
    
    planet_removed = pyqtSignal(int)
    planet_modified = pyqtSignal(int)

    def __init__(self, planets_info: List[BodyState], parent: Optional[QWidget] = None) -> None:
        """
        Инициализирует менеджер планет.

        Args:
            planets_info (List[BodyState]): Ссылка на массив объектов симуляции.
            parent (Optional[QWidget], optional): Родительское окно. По умолчанию None.
        """
        super().__init__(parent)
        self.planets_info = planets_info
        
        self.setWindowTitle(MANAGER_WINDOW_TITLE)
        self.setMinimumSize(MANAGER_MIN_WIDTH, MANAGER_MIN_HEIGHT)
        self.setStyleSheet(MANAGER_STYLE_SHEET)
        
        self.table: QTableWidget
        self._init_ui()

    def _init_ui(self) -> None:
        """Создает элементы интерфейса: таблицу и кнопку закрытия."""
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget(0, len(TABLE_HEADERS))
        self.table.setHorizontalHeaderLabels(TABLE_HEADERS)
        
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
        v_header = self.table.verticalHeader()
        if v_header:
            v_header.setDefaultSectionSize(45)
            v_header.setVisible(False)

        self.table.cellChanged.connect(self._on_cell_changed)
        self.refresh_table()
        
        layout.addWidget(self.table)

        btn_close = QPushButton("Закрыть")
        btn_close.setObjectName("CloseBtn")
        btn_close.setFixedHeight(35)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def refresh_table(self) -> None:
        """Полностью перестраивает таблицу на основе текущего массива планет."""
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        
        for i, planet in enumerate(self.planets_info):
            self.table.insertRow(i)
            self.table.setCellWidget(i, COL_PREVIEW, self._create_center_widget(PlanetPreviewWidget(planet.color, planet.radius)))
            
            btn_color = QPushButton()
            btn_color.setFixedSize(30, 20)
            btn_color.setStyleSheet(f"background-color: {planet.color}; border-radius: 4px; border: 1px solid #555;")
            # Используем параметр по умолчанию в lambda, чтобы захватить текущее значение i
            btn_color.clicked.connect(lambda checked, idx=i: self._change_color(idx))
            self.table.setCellWidget(i, COL_COLOR, self._create_center_widget(btn_color))

            self.table.setItem(i, COL_NAME, QTableWidgetItem(planet.name))
            self.table.setItem(i, COL_MASS, QTableWidgetItem(str(planet.mass)))
            self.table.setItem(i, COL_RADIUS, QTableWidgetItem(str(planet.radius)))
            self.table.setItem(i, COL_X, QTableWidgetItem(str(planet.position[0])))
            self.table.setItem(i, COL_Y, QTableWidgetItem(str(planet.position[1])))
            self.table.setItem(i, COL_VX, QTableWidgetItem(str(planet.velocity[0])))
            self.table.setItem(i, COL_VY, QTableWidgetItem(str(planet.velocity[1])))

            btn_del = QPushButton("×")
            btn_del.setObjectName("DeleteBtn")
            btn_del.setFixedSize(30, 30)
            btn_del.clicked.connect(lambda checked, idx=i: self._on_delete(idx))
            self.table.setCellWidget(i, COL_DELETE, self._create_center_widget(btn_del))
            
        self.table.blockSignals(False)

    def _create_center_widget(self, widget: QWidget) -> QWidget:
        """
        Оборачивает переданный виджет в контейнер для центрирования в ячейке таблицы.
        
        Args:
            widget (QWidget): Целевой виджет.
            
        Returns:
            QWidget: Контейнер с отцентрированным виджетом.
        """
        container = QWidget()
        l = QHBoxLayout(container)
        l.addWidget(widget)
        l.setContentsMargins(0, 0, 0, 0)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return container

    def _on_cell_changed(self, row: int, col: int) -> None:
        """
        Слот, вызываемый при ручном редактировании ячейки таблицы.
        Валидирует введенные данные через временную копию объекта.
        
        Args:
            row (int): Индекс строки.
            col (int): Индекс колонки.
        """
        item = self.table.item(row, col)
        if not item: 
            return
            
        val_text = item.text().replace(',', '.')
        
        try:
            # Создаем временную копию объекта для безопасной проверки (Pydantic v2)
            temp_body = self.planets_info[row].model_copy(deep=True)
            
            if col == COL_NAME: temp_body.name = val_text.strip()
            elif col == COL_MASS: temp_body.mass = float(val_text)
            elif col == COL_RADIUS: temp_body.radius = float(val_text)
            elif col == COL_X: temp_body.position = (float(val_text), temp_body.position[1])
            elif col == COL_Y: temp_body.position = (temp_body.position[0], float(val_text))
            elif col == COL_VX: temp_body.velocity = (float(val_text), temp_body.velocity[1])
            elif col == COL_VY: temp_body.velocity = (temp_body.velocity[0], float(val_text))
            
            # 1. Проверка физических параметров (масса, радиус > 0)
            phys_error = validate_body_params(temp_body)
            if phys_error:
                QMessageBox.warning(self, "Ошибка параметров", phys_error)
                self.refresh_table()
                return

            # 2. Проверка уникальности имени
            if col == COL_NAME and not check_name_uniqueness(temp_body.name, self.planets_info, exclude_idx=row):
                QMessageBox.warning(self, "Ошибка", f"Имя '{temp_body.name}' уже занято.")
                self.refresh_table()
                return

            # 3. Проверка коллизий (при изменении позиции или радиуса)
            if col in (COL_RADIUS, COL_X, COL_Y):
                conflict = check_collision(temp_body, self.planets_info, exclude_idx=row)
                if conflict:
                    QMessageBox.warning(self, "Ошибка физики", f"Столкновение с телом '{conflict}'!")
                    self.refresh_table()
                    return

            # Если всё успешно — применяем изменения к оригиналу
            self.planets_info[row] = temp_body
            if col == COL_RADIUS: 
                self._update_row_widgets(row)
                
            self.planet_modified.emit(row)
            
        except (ValueError, ValidationError):
            # В случае ввода некорректных данных (например, букв вместо чисел) просто откатываем таблицу
            self.refresh_table()

    def _update_row_widgets(self, row: int) -> None:
        """
        Точечно обновляет визуальные виджеты в строке (превью и кнопку цвета) без перерисовки всей таблицы.
        
        Args:
            row (int): Индекс обновляемой строки.
        """
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
                btn.setStyleSheet(f"background-color: {planet.color}; border-radius: 4px; border: 1px solid #555;")

    def _change_color(self, index: int) -> None:
        """
        Открывает диалог выбора цвета и применяет его к выбранной планете.
        
        Args:
            index (int): Индекс целевой планеты.
        """
        planet = self.planets_info[index]
        color = QColorDialog.getColor(QColor(planet.color), self)
        if color.isValid():
            planet.color = color.name()
            self._update_row_widgets(index)
            self.planet_modified.emit(index)

    def _on_delete(self, index: int) -> None:
        """
        Обрабатывает нажатие кнопки удаления в строке таблицы.
        
        Args:
            index (int): Индекс удаляемой планеты.
        """
        self.planet_removed.emit(index)
        self.refresh_table()
