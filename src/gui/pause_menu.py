from typing import List, Optional

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QPushButton, QApplication, 
    QWidget, QFileDialog, QMessageBox, QDialog
)
from PyQt6.QtGui import QPainter, QPaintEvent
from PyQt6.QtCore import pyqtSignal, Qt

from config.schemas import BodyState, SimulationScenario
from core.load_json import save_scenario_to_file, ScenarioSaveError
from gui.add_planet import AddPlanetDialog
from gui.planets_manager import PlanetsManagerDialog
from config.constants import (
    STYLE_BTN_MENU,
    STYLE_BTN_MENU_CONTINUE,
    BTN_MENU_HEIGHT,
    MENU_WIDTH,
    DIMMER_COLOR,
    TEXT_BTN_RESUME,
    TEXT_BTN_REGISTRY,
    TEXT_BTN_ADD,
    TEXT_BTN_EXPORT,
    TEXT_BTN_EXIT,
    MENU_STYLE_SHEET
)

class DimmerOverlay(QWidget):
    """
    Полупрозрачный виджет, который затемняет задний фон (всю сцену)
    при открытии меню паузы для создания эффекта фокуса.
    """
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.hide()

    def paintEvent(self, event: Optional[QPaintEvent]) -> None:
        """Отрисовывает полупрозрачный слой."""
        if event is None:
            return
        painter = QPainter(self)
        painter.fillRect(self.rect(), DIMMER_COLOR)


class PauseMenu(QFrame):
    """
    Всплывающее меню паузы.
    Обеспечивает доступ к реестру планет, добавлению новых тел,
    экспорту текущего состояния в JSON и выходу из приложения.
    """
    
    resume_requested = pyqtSignal()
    planet_added = pyqtSignal(object)  # Передает BodyState
    planet_removed = pyqtSignal(int)
    planet_modified = pyqtSignal(int)

    def __init__(self, parent: QWidget, planets_info: List[BodyState], scenario_name: str) -> None:
        """
        Инициализирует меню паузы.

        Args:
            parent (QWidget): Родительское окно (MainWindow), необходимо для расчета позиционирования.
            planets_info (List[BodyState]): Ссылка на массив объектов симуляции.
            scenario_name (str): Имя текущего запущенного сценария.
        """
        super().__init__(parent)
        self.planets_info = planets_info
        self.scenario_name = scenario_name
        
        self.overlay = DimmerOverlay(parent)
        
        self.setFixedWidth(MENU_WIDTH)
        self.hide()
        
        self.setObjectName("PauseMenuPanel")
        self.setStyleSheet(MENU_STYLE_SHEET)
        
        # Кнопки инициализируются в _init_ui
        self.btn_resume: QPushButton
        self.btn_show_all: QPushButton
        self.btn_add: QPushButton
        self.btn_export: QPushButton
        self.btn_exit: QPushButton
        
        self._init_ui()

    def _init_ui(self) -> None:
        """Настраивает компоновку, кнопки и подключает сигналы."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15) 
        layout.setContentsMargins(30, 40, 30, 40)

        self.btn_resume = QPushButton(TEXT_BTN_RESUME)
        self.btn_show_all = QPushButton(TEXT_BTN_REGISTRY)
        self.btn_add = QPushButton(TEXT_BTN_ADD)
        self.btn_export = QPushButton(TEXT_BTN_EXPORT)
        self.btn_exit = QPushButton(TEXT_BTN_EXIT)

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

    def toggle(self) -> None:
        """
        Переключает видимость меню паузы.
        Если меню открывается, автоматически центрирует его и активирует затемнение фона.
        """
        parent_widget = self.parentWidget()
        if not parent_widget:
            return

        if self.isVisible():
            self.hide()
            self.overlay.hide()
            self.resume_requested.emit()
        else:
            self.overlay.setGeometry(parent_widget.rect())
            self.overlay.show()
            self.show()
            self._update_position()
            self.overlay.raise_()
            self.raise_()

    def _update_position(self) -> None:
        """Центрирует меню относительно родительского окна."""
        parent_widget = self.parentWidget()
        if parent_widget:
            x = (parent_widget.width() - self.width()) // 2
            y = (parent_widget.height() - self.height()) // 2
            self.move(x, y)

    def resume_callback(self, checked: bool = False) -> None:
        """Слот обработки нажатия 'Продолжить'."""
        self.toggle() 

    def show_all_callback(self, checked: bool = False) -> None:
        """Скрывает меню и открывает диалог реестра планет."""
        self.hide()
        dialog = PlanetsManagerDialog(self.planets_info, self.parentWidget())
        dialog.planet_removed.connect(self._on_planet_removed_from_manager)
        dialog.planet_modified.connect(self.planet_modified.emit)
        dialog.exec()
        
        # Показываем меню обратно после закрытия реестра
        self.show()

    def _on_planet_removed_from_manager(self, index: int) -> None:
        """
        Обрабатывает удаление планеты через реестр.
        
        Args:
            index (int): Индекс удаленной планеты.
        """
        if 0 <= index < len(self.planets_info):
            self.planets_info.pop(index)
            self.planet_removed.emit(index)

    def add_planet_callback(self, checked: bool = False) -> None:
        """Скрывает меню и открывает диалог добавления новой планеты."""
        self.hide()
        dialog = AddPlanetDialog(self.planets_info, self.parentWidget())
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_planet = dialog.get_planet_data()
            self.planets_info.append(new_planet)
            self.planet_added.emit(new_planet)
                    
        self.show()
        self.overlay.show()

    def export_json_callback(self, checked: bool = False) -> None:
        """
        Открывает диалог сохранения файла, сериализует текущее 
        состояние планет и сохраняет его в формате JSON.
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить симуляцию", "", "JSON Files (*.json)"
        )
        
        if not file_path: 
            return
        if not file_path.endswith('.json'): 
            file_path += '.json'
        
        try:
            # Создаем объект сценария для валидации перед сохранением
            scenario = SimulationScenario(
                name=self.scenario_name, 
                bodies=self.planets_info
            )
            save_scenario_to_file(scenario, file_path)
            QMessageBox.information(self, "Успех", f"Файл успешно сохранен:\n{file_path}")
            
        except ScenarioSaveError as e:
            QMessageBox.critical(self, "Ошибка сохранения", str(e))
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка сценария", f"Нельзя сохранить: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def exit_callback(self, checked: bool = False) -> None:
        """Завершает работу всего приложения."""
        QApplication.quit()
