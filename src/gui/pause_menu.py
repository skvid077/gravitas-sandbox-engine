from pathlib import Path
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QApplication, QWidget, QFileDialog, QMessageBox, QDialog
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import pyqtSignal, Qt

from config.constants import (
    STYLE_BTN_MENU,
    STYLE_BTN_MENU_CONTINUE,
    BTN_MENU_HEIGHT
)
from config.schemas import SimulationScenario
from core.load_json import save_scenario_to_file, ScenarioSaveError
from core.planets_validator import check_collision, check_name_uniqueness
from gui.add_planet import AddPlanetDialog
from gui.planets_manager import PlanetsManagerDialog

class DimmerOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))

class PauseMenu(QFrame):
    resume_requested = pyqtSignal()
    planet_added = pyqtSignal(object)
    planet_removed = pyqtSignal(int)
    planet_modified = pyqtSignal(int) # <-- ДОБАВЛЕН СИГНАЛ ИЗМЕНЕНИЯ

    def __init__(self, parent: QWidget, planets_info: list, scenario_name: str):
        super().__init__(parent)
        self.planets_info = planets_info
        self.scenario_name = scenario_name # Сохраняем имя сценария
        self.overlay = DimmerOverlay(parent)
        
        self.setFixedWidth(320)
        self.hide()
        
        self.setObjectName("PauseMenuPanel")
        self.setStyleSheet("""
            #PauseMenuPanel {
                background-color: rgba(25, 25, 35, 230);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 20px;
            }
        """)
        self._init_ui()
    
    def export_json_callback(self):
        """Логика сохранения текущего состояния в файл."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить симуляцию", "", "JSON Files (*.json)"
        )
        if not file_path: 
            return
        if not file_path.endswith('.json'): 
            file_path += '.json'
        
        # Создаем объект сценария для валидации перед сохранением
        try:
            scenario = SimulationScenario(
                name=self.scenario_name, 
                bodies=self.planets_info
            )
            save_scenario_to_file(scenario, file_path)
            QMessageBox.information(self, "Успех", f"Файл успешно сохранен:\n{file_path}")
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка валидации", f"Нельзя сохранить: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15) 
        layout.setContentsMargins(30, 40, 30, 40)

        self.btn_resume = QPushButton("Продолжить")
        self.btn_show_all = QPushButton("Реестр планет")
        self.btn_add = QPushButton("Добавить планету")
        self.btn_export = QPushButton("Скачать в JSON")
        self.btn_exit = QPushButton("Выход")

        self.btn_resume.setStyleSheet(STYLE_BTN_MENU_CONTINUE)
        for btn in [self.btn_show_all, self.btn_add, self.btn_export, self.btn_exit]:
            btn.setStyleSheet(STYLE_BTN_MENU)

        for btn in [self.btn_resume, self.btn_show_all, self.btn_add, self.btn_export, self.btn_exit]:
            btn.setFixedHeight(BTN_MENU_HEIGHT)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(btn)

        self.btn_resume.clicked.connect(self.resume_callback)
        self.btn_show_all.clicked.connect(self.show_all_callback)
        self.btn_add.clicked.connect(self.add_planet_callback)
        self.btn_export.clicked.connect(self.export_json_callback)
        self.btn_exit.clicked.connect(self.exit_callback)
        
        self.adjustSize()

    def toggle(self):
        if self.isVisible():
            self.hide()
            self.overlay.hide()
            self.resume_requested.emit()
        else:
            self.overlay.setGeometry(self.parent().rect())
            self.overlay.show()
            self.show()
            self._update_position()
            self.overlay.raise_()
            self.raise_()

    def _update_position(self):
        p = self.parent()
        x = (p.width() - self.width()) // 2
        y = (p.height() - self.height()) // 2
        self.move(x, y)

    def resume_callback(self):
        self.toggle() 

    def show_all_callback(self):
        self.hide()
        dialog = PlanetsManagerDialog(self.planets_info, self.parent())
        dialog.planet_removed.connect(self._on_planet_removed_from_manager)
        dialog.planet_modified.connect(self.planet_modified.emit) # <-- ПРОБРОС СИГНАЛА
        dialog.exec()
        self.show()

    def _on_planet_removed_from_manager(self, index):
        if 0 <= index < len(self.planets_info):
            self.planets_info.pop(index)
            self.planet_removed.emit(index)

    def add_planet_callback(self):
        self.hide()
        # Передаем self.planets_info для проверки уникальности и коллизий
        dialog = AddPlanetDialog(self.planets_info, self.parent())
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_planet = dialog.get_planet_data()
            self.planets_info.append(new_planet)
            self.planet_added.emit(new_planet)
                    
        self.show()
        self.overlay.show()

    def export_json_callback(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить симуляцию", "", "JSON Files (*.json)")
        if not file_path: return
        if not file_path.endswith('.json'): file_path += '.json'
        
        scenario = SimulationScenario(name="Save", bodies=self.planets_info)
        
        try:
            save_scenario_to_file(scenario, file_path)
            QMessageBox.information(self, "Успех", f"Сохранено: {file_path}")
        except ScenarioSaveError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка сценария", str(e))

    def exit_callback(self):
        QApplication.quit()
