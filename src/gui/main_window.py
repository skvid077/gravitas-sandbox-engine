import json
from typing import Optional, Any, List, Dict

from PyQt6.QtCore import QEvent, QPointF, QTimer, Qt
from PyQt6.QtGui import QKeyEvent, QMouseEvent, QResizeEvent
from gui.pause_menu import PauseMenu
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
)

from config.models import PlanetItem
from gui.add_planet import AddPlanetDialog
from PyQt6.QtWidgets import QDialog

from config.constants import *
from config.schemas import BodyState, SimulationScenario
from gui.space import SpaceScene, SpaceView

class MainWindow(QMainWindow):
    def __init__(self, scenario: Optional[SimulationScenario] = None) -> None:
        super().__init__()
        self.setWindowTitle("Gravitas Sandbox")
        self.resize(1024, 768)
        
        # Если сценарий передан, берем данные из него, иначе создаем пустые
        if scenario:
            self.planets_info = scenario.bodies
            self.scenario_name = scenario.name
        else:
            self.planets_info = []
            self.scenario_name = "Новая симуляция"

        self.scene = SpaceScene()
        self.view = SpaceView(self.scene)
        self.setCentralWidget(self.view)
        
        self._init_ui()
        self._render_initial_planets()

    def _init_ui(self) -> None:
        # Передаем текущее название сценария в меню для корректного экспорта
        self.menu = PauseMenu(self, self.planets_info, self.scenario_name)
        
        self.menu.planet_added.connect(self._on_planet_added)
        self.menu.planet_removed.connect(self._on_planet_removed)
        self.menu.planet_modified.connect(self._on_planet_modified)
        
        self._frame_count = 0
        self.lbl_fps = QLabel("FPS: 0", self)
        self.lbl_fps.setStyleSheet(FPS_LABEL_STYLE)
        self.lbl_fps.move(20, 20)

        self.fps_timer = QTimer(self)
        self.fps_timer.timeout.connect(self._update_fps_display)
        self.fps_timer.start(1000)

        self.lbl_coords = QLabel("X: 0.0 | Y: 0.0", self)
        self.lbl_coords.setStyleSheet(COORD_LABEL_STYLE)
        self.lbl_coords.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.lbl_coords.adjustSize()

        self.view.viewport().installEventFilter(self)
    
    def _open_edit_dialog(self, item):
        """Открывает диалог редактирования конкретной планеты."""
        # Передаем тело планеты вторым аргументом
        dialog = AddPlanetDialog(self.planets_info, self, edit_body=item.body_state)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Т.к. данные в item.body_state обновились в диалоге, просто перерисовываем
            item.update_visuals()
            # Если нужно обновить реестр, кидаем сигнал
            idx = self.planets_info.index(item.body_state)
            self.menu.planet_modified.emit(idx)

    def _on_planet_added(self, new_planet):
        """Отрисовка новой планеты на сцене с передачей коллбэка редактирования."""
        if hasattr(self.scene, 'add_body'):
            # ВАЖНО: передаем два аргумента
            self.scene.add_body(new_planet, self._open_edit_dialog)

    def _render_initial_planets(self):
        """Отрисовка тел, загруженных из файла сценария."""
        for planet in self.planets_info:
            self._on_planet_added(planet)

    def _on_planet_removed(self, index):
        if hasattr(self.scene, 'remove_body_by_index'):
            self.scene.remove_body_by_index(index)

    def _on_planet_modified(self, index):
        """Вызывается при изменении данных в Реестре."""
        if hasattr(self.scene, 'update_body_by_index'):
            # ВАЖНО: передаем обновленный объект состояния по индексу
            new_state = self.planets_info[index]
            self.scene.update_body_by_index(index, new_state)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.menu.toggle()
        super().keyPressEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        
        if hasattr(self, 'lbl_fps'):
            self.lbl_fps.move(20, 20)

        if self.menu.isVisible():
            self.menu.overlay.setGeometry(self.rect())
            self.menu._update_position()

    def eventFilter(self, obj, event: QEvent):
        if obj == self.view.viewport():
            if event.type() == QEvent.Type.Paint:
                self._frame_count += 1
            elif event.type() == QEvent.Type.MouseMove:
                mouse_event: QMouseEvent = event
                scene_pos = self.view.mapToScene(mouse_event.pos())
                self._update_coords_display(scene_pos.x(), scene_pos.y())
                
                window_pos = self.mapFromGlobal(mouse_event.globalPosition().toPoint())
                self.lbl_coords.move(window_pos.x() + 15, window_pos.y() + 15)
        return super().eventFilter(obj, event)

    def _update_coords_display(self, x: float, y: float) -> None:
        self.lbl_coords.setText(f"X: {x:.1f} | Y: {y:.1f}")
        self.lbl_coords.adjustSize()

    def _update_fps_display(self):
        self.lbl_fps.setText(f"FPS: {self._frame_count}")
        self.lbl_fps.adjustSize()
        self._frame_count = 0
