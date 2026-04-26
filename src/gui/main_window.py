from typing import Optional

from PyQt6.QtCore import QEvent, QTimer, Qt
from PyQt6.QtGui import QKeyEvent, QMouseEvent, QResizeEvent
from PyQt6.QtWidgets import QMainWindow, QLabel, QDialog

from gui.pause_menu import PauseMenu
from gui.add_planet import AddPlanetDialog
from gui.space import SpaceScene, SpaceView

from config.constants import *
from config.schemas import SimulationScenario
from core.simulation import Simulation

class MainWindow(QMainWindow):
    def __init__(self, scenario: Optional[SimulationScenario] = None) -> None:
        super().__init__()
        self.setWindowTitle("Gravitas Sandbox")
        self.resize(1024, 768)
        
        initial_bodies = scenario.bodies if scenario else []
        self.simulation = Simulation(initial_bodies)
        self.scenario_name = scenario.name if scenario else "Новая симуляция"

        self.scene = SpaceScene()
        self.view = SpaceView(self.scene)
        self.setCentralWidget(self.view)
        
        self.is_running = False
        self._frame_count = 0
        
        self._init_ui()
        self._render_initial_planets()

    def _init_ui(self) -> None:
        self.menu = PauseMenu(self, self.simulation.bodies, self.scenario_name)
        
        self.menu.planet_added.connect(self._on_planet_added)
        self.menu.planet_removed.connect(self._on_planet_removed)
        self.menu.planet_modified.connect(self._on_planet_modified)
        
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

        self.lbl_status = QLabel("ПАУЗА (Нажмите Enter для запуска)", self)
        self.lbl_status.setStyleSheet("color: orange; font-weight: bold; background: rgba(0,0,0,100); padding: 5px;")
        self.lbl_status.move(20, 50)
        self.lbl_status.adjustSize()

        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self._physics_step)
        self.sim_timer.start(PHYSICS_TICK_RATE)

        # Единственное подключение для мыши
        self.view.right_click_empty.connect(self._add_planet_on_click)

    def _physics_step(self) -> None:
        if not self.is_running or self.menu.isVisible() or not self.simulation.bodies:
            return

        dt = PHYSICS_TICK_RATE / 1000.0
        self.simulation.step(dt)

        for i, state in enumerate(self.simulation.bodies):
            if hasattr(self.scene, 'update_body_by_index'):
                self.scene.update_body_by_index(i, state)

    def _add_planet_on_click(self, x: float, y: float) -> None:
        new_body = self.simulation.add_default_body(x, y)
        self._on_planet_added(new_body)

    def _open_edit_dialog(self, item) -> None:
        was_running = self.is_running
        self.is_running = False
        self._update_ui_state()

        dialog = AddPlanetDialog(self.simulation.bodies, self, edit_body=item.body_state)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            item.update_visuals()
            idx = self.simulation.bodies.index(item.body_state)
            self.menu.planet_modified.emit(idx)
            
        self.is_running = was_running
        self._update_ui_state()

    def _on_planet_added(self, new_planet) -> None:
        if hasattr(self.scene, 'add_body'):
            self.scene.add_body(new_planet, self._open_edit_dialog)

    def _render_initial_planets(self) -> None:
        for planet in self.simulation.bodies:
            self._on_planet_added(planet)

    def _on_planet_removed(self, index: int) -> None:
        if hasattr(self.scene, 'remove_body_by_index'):
            self.scene.remove_body_by_index(index)

    def _on_planet_modified(self, index: int) -> None:
        if hasattr(self.scene, 'update_body_by_index'):
            new_state = self.simulation.bodies[index]
            self.scene.update_body_by_index(index, new_state)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.is_running = not self.is_running
            self._update_ui_state()
        elif event.key() == Qt.Key.Key_Escape:
            self.is_running = False
            self._update_ui_state()
            self.menu.toggle()
        super().keyPressEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if hasattr(self, 'lbl_fps'):
            self.lbl_fps.move(20, 20)
        if self.menu.isVisible():
            self.menu.overlay.setGeometry(self.rect())
            self.menu._update_position()

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj == self.view.viewport():
            if event.type() == QEvent.Type.Paint:
                self._frame_count += 1
            elif event.type() == QEvent.Type.MouseMove:
                mouse_event: QMouseEvent = event
                scene_pos = self.view.mapToScene(mouse_event.pos())
                self.lbl_coords.setText(f"X: {scene_pos.x():.1f} | Y: {scene_pos.y():.1f}")
                self.lbl_coords.adjustSize()
                
                window_pos = self.mapFromGlobal(mouse_event.globalPosition().toPoint())
                self.lbl_coords.move(window_pos.x() + 15, window_pos.y() + 15)
        return super().eventFilter(obj, event)

    def _update_fps_display(self) -> None:
        self.lbl_fps.setText(f"FPS: {self._frame_count}")
        self.lbl_fps.adjustSize()
        self._frame_count = 0

    def _update_ui_state(self) -> None:
        text = "СИМУЛЯЦИЯ ЗАПУЩЕНА" if self.is_running else "ПАУЗА (Нажмите Enter)"
        color = "white" if self.is_running else "orange"
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"color: {color}; font-weight: bold; background: rgba(0,0,0,100); padding: 5px;")
        self.lbl_status.adjustSize()
