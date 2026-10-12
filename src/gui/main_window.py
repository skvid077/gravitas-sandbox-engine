from typing import Any, cast

from PyQt6.QtCore import QEvent, QObject, Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QKeyEvent, QMouseEvent, QResizeEvent
from PyQt6.QtWidgets import QDialog, QLabel, QMainWindow

from config.constants import (
    COORD_LABEL_STYLE,
    COORDINATE_LABEL_OFFSET,
    DEFAULT_FPS_FOR_TIME_MACHINE,
    DEFAULT_MAX_SECONDS_FOR_TIME_MACHINE,
    DEFAULT_SCENARIO_NAME,
    FPS_LABEL_STYLE,
    FPS_UPDATE_INTERVAL_MS,
    MAIN_WINDOW_HEIGHT,
    MAIN_WINDOW_TITLE,
    MAIN_WINDOW_WIDTH,
    PHYSICS_TICK_INTERVAL_MS,
    STATUS_LABEL_Y,
    STATUS_STYLE_PAUSED,
    STATUS_STYLE_RUNNING,
    STATUS_TEXT_PAUSED,
    STATUS_TEXT_RUNNING,
    TEXT_COORDINATES_FORMAT,
    TEXT_FPS_FORMAT,
    UI_MARGIN,
)
from config.models import BodyState, SimulationScenario
from core.session_report import SessionReport
from core.simulation import Simulation
from core.time_machine import TimeMachine
from gui.add_planet import AddPlanetDialog
from gui.control_panel import ControlPanel
from gui.models import PlanetItem
from gui.pause_menu import PauseMenu
from gui.space import SpaceScene, SpaceView


class MainWindow(QMainWindow):
    def __init__(
        self,
        scenario: SimulationScenario | None = None,
        session_report: SessionReport | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle(MAIN_WINDOW_TITLE)
        self.resize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        initial_bodies = scenario.bodies if scenario is not None else []
        self.simulation = Simulation(initial_bodies)
        self.scenario_name = scenario.name if scenario else DEFAULT_SCENARIO_NAME
        self.session_report = session_report or SessionReport()
        self.session_report.set_initial_state(
            self.scenario_name,
            len(initial_bodies),
            self.simulation.physics_engine.gravitational_constant,
        )

        self.scene = SpaceScene()
        self.view = SpaceView(self.scene)
        self.setCentralWidget(self.view)

        self.is_running: bool = False
        self._frame_count: int = 0
        self.time_scale: float = 1.0
        self.time_machine = TimeMachine(
            max_seconds=DEFAULT_MAX_SECONDS_FOR_TIME_MACHINE,
            fps=DEFAULT_FPS_FOR_TIME_MACHINE,
        )
        self.time_machine.reset(self.simulation.bodies)
        self.panel: ControlPanel
        self.menu: PauseMenu
        self.lbl_fps: QLabel
        self.fps_timer: QTimer
        self.lbl_coordinates: QLabel
        self.lbl_status: QLabel
        self.sim_timer: QTimer

        self._init_ui()
        self._render_initial_planets()

    def _init_ui(self) -> None:
        self.panel = ControlPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.panel)

        cast(Any, self.panel.gravity_changed).connect(self._set_gravity)
        cast(Any, self.panel.time_scale_changed).connect(self._set_time_scale)
        cast(Any, self.panel.clear_scene_requested).connect(self._clear_scene)
        cast(Any, self.panel.timeline_pressed).connect(self._on_timeline_start)
        cast(Any, self.panel.timeline_changed).connect(self._on_timeline_scrub)
        self.menu = PauseMenu(self, self.simulation.bodies, self.scenario_name)
        cast(Any, self.menu.planet_added).connect(self._on_planet_added)
        cast(Any, self.menu.planet_removed).connect(self._on_planet_removed)
        cast(Any, self.menu.planet_modified).connect(self._on_planet_modified)
        self.lbl_fps = QLabel(TEXT_FPS_FORMAT.format(0), self)
        self.lbl_fps.setStyleSheet(FPS_LABEL_STYLE)
        self.lbl_fps.move(UI_MARGIN, UI_MARGIN)

        self.fps_timer = QTimer(self)
        QTimer.timeout.__get__(self.fps_timer, QTimer).connect(self._update_fps_display)
        self.fps_timer.start(FPS_UPDATE_INTERVAL_MS)

        self.lbl_coordinates = QLabel(TEXT_COORDINATES_FORMAT.format(0.0, 0.0), self)
        self.lbl_coordinates.setStyleSheet(COORD_LABEL_STYLE)
        self.lbl_coordinates.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.lbl_coordinates.adjustSize()
        viewport = self.view.viewport()
        if viewport is not None:
            viewport.installEventFilter(self)

        self.lbl_status = QLabel(STATUS_TEXT_PAUSED, self)
        self.lbl_status.setStyleSheet(STATUS_STYLE_PAUSED)
        self.lbl_status.move(UI_MARGIN, STATUS_LABEL_Y)
        self.lbl_status.adjustSize()
        self.sim_timer = QTimer(self)
        QTimer.timeout.__get__(self.sim_timer, QTimer).connect(self._physics_step)
        self.sim_timer.start(PHYSICS_TICK_INTERVAL_MS)

        cast(Any, self.view.right_click_empty).connect(self._add_planet_on_click)

    def _on_timeline_start(self) -> None:
        self.time_machine.pause()
        self.is_running = False
        self._update_ui_state()

    def _on_timeline_scrub(self, frame_index: int) -> None:
        snapshot = self.time_machine.jump_to(frame_index)

        if snapshot is not None:
            self.scene.clear_planets()
            self.simulation.bodies.clear()
            for body_snapshot in snapshot:
                body = body_snapshot.to_body_state()
                self.simulation.bodies.append(body)
                self.scene.add_body(body, self._open_edit_dialog)

            viewport = self.view.viewport()
            if viewport is not None:
                viewport.update()

    def _set_gravity(self, new_g: float) -> None:
        self.simulation.physics_engine.gravitational_constant = new_g

    def _set_time_scale(self, scale: float) -> None:
        self.time_scale = scale

    def _clear_scene(self) -> None:
        self.session_report.record_removed_bodies(len(self.simulation.bodies))
        self.scene.clear_planets()
        self.simulation.bodies.clear()
        self._record_scene_change()

    def _physics_step(self) -> None:
        if not self.is_running or self.menu.isVisible() or not self.simulation.bodies:
            return

        dt = (PHYSICS_TICK_INTERVAL_MS / 1000) * self.time_scale
        collision_events = self.simulation.step(dt)
        self.session_report.record_simulation_step(dt)
        self.session_report.record_collisions(collision_events)

        if not self.time_machine.is_paused:
            self.time_machine.save_snapshot(self.simulation.bodies)

        if not self.time_machine.is_paused:
            self.panel.update_timeline_range(
                self.time_machine.get_total_frames(), self.time_machine.get_current_frame_index()
            )

        # Слияние тел после столкновений может изменить состав и порядок списка.
        self.scene.sync_bodies(self.simulation.bodies, self._open_edit_dialog)

    def _add_planet_on_click(self, x: float, y: float) -> None:
        new_body = self.simulation.add_default_body(x, y)
        self._on_planet_added(new_body)

    def _open_edit_dialog(self, item: PlanetItem) -> None:
        was_running = self.is_running
        self.is_running = False
        self._update_ui_state()

        dialog = AddPlanetDialog(self.simulation.bodies, self, edit_body=item.body_state)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            item.update_visuals()
            idx = self.simulation.bodies.index(item.body_state)
            cast(Any, self.menu.planet_modified).emit(idx)

        self.is_running = was_running
        self._update_ui_state()

    def _on_planet_added(self, new_planet: BodyState) -> None:
        self.session_report.record_created_body()
        self.scene.add_body(new_planet, self._open_edit_dialog)
        self._record_scene_change()

    def _render_initial_planets(self) -> None:
        for planet in self.simulation.bodies:
            self.scene.add_body(planet, self._open_edit_dialog)

    def _on_planet_removed(self, _index: int) -> None:
        self.session_report.record_removed_bodies(1)
        self.scene.sync_bodies(self.simulation.bodies, self._open_edit_dialog)
        self._record_scene_change()

    def _on_planet_modified(self, index: int) -> None:
        new_state = self.simulation.bodies[index]
        self.scene.update_body_by_index(index, new_state)
        self._record_scene_change()

    def _record_scene_change(self) -> None:
        self.time_machine.record_change(self.simulation.bodies)
        self.panel.update_timeline_range(
            self.time_machine.get_total_frames(), self.time_machine.get_current_frame_index()
        )

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event is None:
            super().keyPressEvent(event)
            return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.is_running = not self.is_running
            if self.is_running:
                self.time_machine.resume()
            self._update_ui_state()
        elif event.key() == Qt.Key.Key_Escape:
            self.is_running = False
            self._update_ui_state()
            self.menu.toggle()
        super().keyPressEvent(event)

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        if event is None:
            return

        super().resizeEvent(event)
        self.lbl_fps.move(UI_MARGIN, UI_MARGIN)

        if self.menu.isVisible():
            self.menu.overlay.setGeometry(self.rect())
            self.menu.update_position()

    def eventFilter(self, obj: QObject | None, event: QEvent | None) -> bool:
        if obj == self.view.viewport() and event is not None:
            if event.type() == QEvent.Type.Paint:
                self._frame_count += 1
            elif event.type() == QEvent.Type.MouseMove and isinstance(event, QMouseEvent):
                mouse_event: QMouseEvent = event
                scene_pos = self.view.mapToScene(mouse_event.pos())
                self.lbl_coordinates.setText(
                    TEXT_COORDINATES_FORMAT.format(scene_pos.x(), scene_pos.y())
                )
                self.lbl_coordinates.adjustSize()

                window_pos = self.mapFromGlobal(mouse_event.globalPosition().toPoint())
                self.lbl_coordinates.move(
                    window_pos.x() + COORDINATE_LABEL_OFFSET,
                    window_pos.y() + COORDINATE_LABEL_OFFSET,
                )

        return super().eventFilter(obj, event)

    def _update_fps_display(self) -> None:
        self.lbl_fps.setText(TEXT_FPS_FORMAT.format(self._frame_count))
        self.lbl_fps.adjustSize()
        self._frame_count = 0

    def _update_ui_state(self) -> None:
        text = STATUS_TEXT_RUNNING if self.is_running else STATUS_TEXT_PAUSED
        style = STATUS_STYLE_RUNNING if self.is_running else STATUS_STYLE_PAUSED

        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(style)
        self.lbl_status.adjustSize()

    def save_session_report(self) -> None:
        self.session_report.save(
            final_body_count=len(self.simulation.bodies),
            final_gravity=self.simulation.physics_engine.gravitational_constant,
            final_time_scale=self.time_scale,
        )

    def closeEvent(self, event: QCloseEvent | None) -> None:
        self.save_session_report()
        super().closeEvent(event)
