import math
from pydantic import ValidationError
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QHBoxLayout, QWidget, QColorDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen

# Импортируем наши инструменты валидации
from core.planets_validator import check_collision, check_name_uniqueness, validate_body_params

class PlanetPreviewWidget(QWidget):
    """Виджет для логарифмического превью планеты в ячейке."""
    def __init__(self, color_hex: str, real_radius: float, parent=None):
        super().__init__(parent)
        self.color = QColor(color_hex)
        self.real_radius = real_radius
        self.setFixedSize(40, 40)

    def update_params(self, color_hex: str, radius: float):
        self.color = QColor(color_hex)
        self.real_radius = radius
        self.update()

    def paintEvent(self, event):
        # ЗАЩИТА: Если радиус некорректный, не рисуем ничего, чтобы math.log10 не упал
        if self.real_radius <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Логарифмический масштаб: даже очень большие радиусы не выйдут за 18px
        visual_r = min(18.0, max(3.0, math.log10(self.real_radius + 1) * 6.0))

        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        painter.drawEllipse(QPointF(20, 20), visual_r, visual_r)

class PlanetsManagerDialog(QDialog):
    planet_removed = pyqtSignal(int)
    planet_modified = pyqtSignal(int)

    def __init__(self, planets_info: list, parent=None):
        super().__init__(parent)
        self.planets_info = planets_info
        self.setWindowTitle("Реестр небесных тел")
        self.setMinimumSize(950, 450)
        
        # Стилизация остается без изменений
        self.setStyleSheet("""
            QDialog { 
                background-color: rgba(20, 22, 30, 240); 
                border: 1px solid rgba(255, 255, 255, 20); 
                border-radius: 12px;
            }
            QTableWidget { 
                background-color: transparent; 
                color: white; 
                gridline-color: rgba(255, 255, 255, 10); 
                font-size: 13px;
                border: none;
            }
            QHeaderView::section { 
                background-color: rgba(40, 45, 60, 200); 
                color: #bbb; 
                padding: 6px; 
                font-weight: bold;
            }
            QPushButton#DeleteBtn { 
                background-color: rgba(220, 50, 50, 30); 
                color: #ff8888; 
                border: 1px solid rgba(220, 50, 50, 80); 
                border-radius: 6px; 
            }
            QPushButton#CloseBtn { 
                background-color: rgba(255, 255, 255, 10); 
                border: 1px solid rgba(255, 255, 255, 30); 
                border-radius: 8px; 
                color: white; 
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "Вид", "Цвет", "Имя", "Масса", "Радиус", "X", "Y", "Vx", "Vy", "Удалить"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.verticalHeader().setVisible(False)

        self.table.cellChanged.connect(self._on_cell_changed)
        self.refresh_table()
        
        layout.addWidget(self.table)

        btn_close = QPushButton("Закрыть")
        btn_close.setObjectName("CloseBtn")
        btn_close.setFixedHeight(35)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def refresh_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for i, planet in enumerate(self.planets_info):
            self.table.insertRow(i)
            self.table.setCellWidget(i, 0, self._create_center_widget(PlanetPreviewWidget(planet.color, planet.radius)))
            
            btn_color = QPushButton()
            btn_color.setFixedSize(30, 20)
            btn_color.setStyleSheet(f"background-color: {planet.color}; border-radius: 4px; border: 1px solid #555;")
            btn_color.clicked.connect(lambda ch, idx=i: self._change_color(idx))
            self.table.setCellWidget(i, 1, self._create_center_widget(btn_color))

            self.table.setItem(i, 2, QTableWidgetItem(planet.name))
            self.table.setItem(i, 3, QTableWidgetItem(str(planet.mass)))
            self.table.setItem(i, 4, QTableWidgetItem(str(planet.radius)))
            self.table.setItem(i, 5, QTableWidgetItem(str(planet.position[0])))
            self.table.setItem(i, 6, QTableWidgetItem(str(planet.position[1])))
            self.table.setItem(i, 7, QTableWidgetItem(str(planet.velocity[0])))
            self.table.setItem(i, 8, QTableWidgetItem(str(planet.velocity[1])))

            btn_del = QPushButton("×")
            btn_del.setObjectName("DeleteBtn")
            btn_del.setFixedSize(30, 30)
            btn_del.clicked.connect(lambda ch, idx=i: self._on_delete(idx))
            self.table.setCellWidget(i, 9, self._create_center_widget(btn_del))
        self.table.blockSignals(False)

    def _create_center_widget(self, widget):
        container = QWidget()
        l = QHBoxLayout(container)
        l.addWidget(widget)
        l.setContentsMargins(0, 0, 0, 0)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return container

    def _on_cell_changed(self, row, col):
        """Валидация данных при изменении ячеек в реестре."""
        item = self.table.item(row, col)
        if not item: return
            
        val_text = item.text().replace(',', '.')
        
        try:
            # Создаем временную копию объекта для безопасной проверки
            temp_body = self.planets_info[row].model_copy(deep=True)
            
            if col == 2: temp_body.name = val_text.strip()
            elif col == 3: temp_body.mass = float(val_text)
            elif col == 4: temp_body.radius = float(val_text)
            elif col == 5: temp_body.position = (float(val_text), temp_body.position[1])
            elif col == 6: temp_body.position = (temp_body.position[0], float(val_text))
            elif col == 7: temp_body.velocity = (float(val_text), temp_body.velocity[1])
            elif col == 8: temp_body.velocity = (temp_body.velocity[0], float(val_text))
            
            # 1. Проверка физических параметров (масса, радиус > 0)
            phys_error = validate_body_params(temp_body)
            if phys_error:
                QMessageBox.warning(self, "Ошибка параметров", phys_error)
                self.refresh_table()
                return

            # 2. Проверка уникальности имени
            if col == 2 and not check_name_uniqueness(temp_body.name, self.planets_info, exclude_idx=row):
                QMessageBox.warning(self, "Ошибка", f"Имя '{temp_body.name}' уже занято.")
                self.refresh_table()
                return

            # 3. Проверка коллизий (при изменении позиции или радиуса)
            if col in (4, 5, 6):
                conflict = check_collision(temp_body, self.planets_info, exclude_idx=row)
                if conflict:
                    QMessageBox.warning(self, "Ошибка физики", f"Столкновение с телом '{conflict}'!")
                    self.refresh_table()
                    return

            # Если всё успешно — обновляем основные данные
            self.planets_info[row] = temp_body
            if col == 4: self._update_row_widgets(row)
            self.planet_modified.emit(row)
            
        except (ValueError, ValidationError):
            self.refresh_table()

    def _update_row_widgets(self, row):
        planet = self.planets_info[row]
        container_preview = self.table.cellWidget(row, 0)
        if container_preview:
            preview = container_preview.findChild(PlanetPreviewWidget)
            if preview: preview.update_params(planet.color, planet.radius)
        
        container_color = self.table.cellWidget(row, 1)
        if container_color:
            btn = container_color.findChild(QPushButton)
            if btn: btn.setStyleSheet(f"background-color: {planet.color}; border-radius: 4px; border: 1px solid #555;")

    def _change_color(self, index):
        planet = self.planets_info[index]
        color = QColorDialog.getColor(QColor(planet.color), self)
        if color.isValid():
            planet.color = color.name()
            self._update_row_widgets(index)
            self.planet_modified.emit(index)

    def _on_delete(self, index):
        self.planet_removed.emit(index)
        self.refresh_table()
