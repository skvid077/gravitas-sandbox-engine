from typing import Optional

from PyQt6.QtCore import QEvent, QTimer, Qt, QObject
from PyQt6.QtGui import QKeyEvent, QMouseEvent, QResizeEvent
from PyQt6.QtWidgets import QMainWindow, QLabel, QDialog

from gui.models import PlanetItem
from gui.pause_menu import PauseMenu
from gui.add_planet import AddPlanetDialog
from gui.space import SpaceScene, SpaceView
from gui.control_panel import ControlPanel

from config.schemas import SimulationScenario, BodyState
from core.simulation import Simulation
from core.time_machine import TimeMachine
from config.constants import (
    MAIN_WINDOW_TITLE,
    MAIN_WINDOW_WIDTH,
    MAIN_WINDOW_HEIGHT,
    DEFAULT_SCENARIO_NAME,
    STATUS_TEXT_PAUSED,
    STATUS_TEXT_RUNNING,
    STATUS_STYLE_PAUSED,
    STATUS_STYLE_RUNNING,
    PHYSICS_TICK_RATE,
    FPS_LABEL_STYLE,
    COORD_LABEL_STYLE
)


class MainWindow(QMainWindow):
    """
    Главное окно приложения.
    Связывает воедино физический движок (Simulation), графическую сцену (SpaceScene)
    и элементы пользовательского интерфейса (Панель управления, Меню паузы).
    """

    def __init__(self, scenario: Optional[SimulationScenario] = None) -> None:
        """
        Инициализация главного окна. 
        Поднимаем движок, настраиваем сцену и подвязываем к ней UI.
        Если передан сценарий, сразу грузим из него планеты.
        """
        super().__init__()
        self.setWindowTitle(MAIN_WINDOW_TITLE)
        self.resize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)
        
        initial_bodies = scenario.bodies if scenario else []
        self.simulation = Simulation(initial_bodies)
        self.scenario_name = scenario.name if scenario else DEFAULT_SCENARIO_NAME

        self.scene = SpaceScene()
        self.view = SpaceView(self.scene)
        self.setCentralWidget(self.view)
        
        self.is_running: bool = False
        self._frame_count: int = 0
        self.time_scale: float = 1.0
        
        # Машина времени (запоминаем последние 30 секунд при 60 FPS)
        self.time_machine = TimeMachine(max_seconds=30, fps=int(1000 / PHYSICS_TICK_RATE))
        
        # Строгая декларация атрибутов
        self.panel: ControlPanel
        self.menu: PauseMenu
        self.lbl_fps: QLabel
        self.fps_timer: QTimer
        self.lbl_coords: QLabel
        self.lbl_status: QLabel
        self.sim_timer: QTimer
        
        self._init_ui()
        self._render_initial_planets()

    def _init_ui(self) -> None:
        """
        Собирает весь интерфейс: боковую панель управления, 
        меню паузы и плавающие виджеты (FPS, координаты курсора, статус симуляции).
        """
        # --- Подключение боковой панели ---
        self.panel = ControlPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.panel)
        
        self.panel.gravity_changed.connect(self._set_gravity)
        self.panel.time_scale_changed.connect(self._set_time_scale)
        self.panel.clear_scene_requested.connect(self._clear_scene)

        # --- Подключение машины времени к слайдеру ---
        self.panel.timeline_pressed.connect(self._on_timeline_start)
        self.panel.timeline_changed.connect(self._on_timeline_scrub)
        self.panel.timeline_released.connect(self._on_timeline_end)

        # --- Меню паузы ---
        self.menu = PauseMenu(self, self.simulation.bodies, self.scenario_name)
        self.menu.planet_added.connect(self._on_planet_added)
        self.menu.planet_removed.connect(self._on_planet_removed)
        self.menu.planet_modified.connect(self._on_planet_modified)
        
        # --- UI Элементы поверх сцены ---
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
        viewport = self.view.viewport()
        if viewport is not None:
            viewport.installEventFilter(self)

        self.lbl_status = QLabel(STATUS_TEXT_PAUSED, self)
        self.lbl_status.setStyleSheet(STATUS_STYLE_PAUSED)
        self.lbl_status.move(20, 50)
        self.lbl_status.adjustSize()

        # --- Физический таймер ---
        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self._physics_step)
        self.sim_timer.start(PHYSICS_TICK_RATE)

        self.view.right_click_empty.connect(self._add_planet_on_click)

    # --- Методы управления машиной времени ---

    def _on_timeline_start(self) -> None:
        """
        Пользователь схватился за ползунок истории.
        Жестко ставим симуляцию и запись времени на паузу.
        """
        self.time_machine.pause()
        self.is_running = False
        self._update_ui_state()

    def _on_timeline_scrub(self, frame_index: int) -> None:
        """
        Перематываем время на конкретный кадр с ползунка.
        Сносим текущие тела и полностью восстанавливаем сцену из слепка.
        """
        snapshot = self.time_machine.jump_to(frame_index)
        
        if snapshot is not None:
            # Полностью очищаем сцену
            self.scene.clear_planets()
            self.simulation.bodies.clear()
            
            # Восстанавливаем состояние из слепка
            for body_dict in snapshot:
                body = BodyState(**body_dict)
                self.simulation.bodies.append(body)
                self._on_planet_added(body)
                
            viewport = self.view.viewport()
            if viewport is not None:
                viewport.update()

    def _on_timeline_end(self) -> None:
        """
        Пользователь отпустил ползунок перемотки.
        Отпускаем машину времени, но саму физику оставляем на паузе, чтобы дать осмотреться.
        """
        self.time_machine.resume()

    # --- Методы управления с панели ---
    
    def _set_gravity(self, new_g: float) -> None:
        """Прокидывает новое значение гравитации с ползунка в движок."""
        self.simulation.physics_engine.G = new_g

    def _set_time_scale(self, scale: float) -> None:
        """Меняет множитель скорости времени для симуляции."""
        self.time_scale = scale

    def _clear_scene(self) -> None:
        """Полностью зачищает космос. Удаляет и физические модели, и графику."""
        self.scene.clear_planets()
        self.simulation.bodies.clear()

    # --- Главный цикл физики ---
    
    def _physics_step(self) -> None:
        """
        Сердце симуляции. Дергается по таймеру каждый кадр.
        Сохраняет историю, считает новую физику и двигает UI.
        """
        if not self.is_running or self.menu.isVisible() or not self.simulation.bodies:
            return
            
        # 1. Сохраняем слепок ДО шага физики
        if not self.time_machine.is_paused:
            self.time_machine.save_snapshot(self.simulation.bodies)
            
        # 2. Делаем физический шаг
        dt = (PHYSICS_TICK_RATE / 1000.0) * self.time_scale
        self.simulation.step(dt)
        
        # 3. Двигаем ползунок панели управления вместе со временем
        if not self.time_machine.is_paused:
            self.panel.update_timeline_range(
                self.time_machine.get_total_frames(),
                self.time_machine.get_current_frame_index()
            )
        
        # 4. Обновляем координаты на сцене
        for i, state in enumerate(self.simulation.bodies):
            self.scene.update_body_by_index(i, state)

    # --- Взаимодействие со сценой и диалогами ---
    
    def _add_planet_on_click(self, x: float, y: float) -> None:
        """Спавнит новую дефолтную планету по клику мыши на пустом месте."""
        new_body = self.simulation.add_default_body(x, y)
        self._on_planet_added(new_body)

    def _open_edit_dialog(self, item: PlanetItem) -> None:
        """
        Открывает окно редактирования параметров планеты.
        На время работы с диалогом ставим мир на паузу.
        """
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

    def _on_planet_added(self, new_planet: BodyState) -> None:
        """Слот добавления. Отрисовывает планету и вешает на нее возможность редактирования."""
        self.scene.add_body(new_planet, self._open_edit_dialog)

    def _render_initial_planets(self) -> None:
        """Отрисовывает все планеты, которые были загружены из стартового JSON."""
        for planet in self.simulation.bodies:
            self._on_planet_added(planet)

    def _on_planet_removed(self, index: int) -> None:
        """Сносит конкретную планету со сцены по её индексу."""
        self.scene.remove_body_by_index(index)

    def _on_planet_modified(self, index: int) -> None:
        """Применяет обновленные параметры (цвет, размер) к визуалы планеты."""
        new_state = self.simulation.bodies[index]
        self.scene.update_body_by_index(index, new_state)

    # --- Системные события (Events) ---
    
    def keyPressEvent(self, event: Optional[QKeyEvent]) -> None:
        """
        Обработка горячих клавиш. 
        Enter — старт/пауза. Escape — меню.
        """
        if event is None:
            super().keyPressEvent(event)
            return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.is_running = not self.is_running
            self._update_ui_state()
        elif event.key() == Qt.Key.Key_Escape:
            self.is_running = False
            self._update_ui_state()
            self.menu.toggle()
        super().keyPressEvent(event)

    def resizeEvent(self, event: Optional[QResizeEvent]) -> None:
        """
        Дергается при изменении размеров окна.
        Следит за тем, чтобы плавающие элементы (типа оверлея паузы) перерисовывались по размеру окна.
        """
        if event is None:
            return

        super().resizeEvent(event)
        self.lbl_fps.move(20, 20)
        
        if self.menu.isVisible():
            self.menu.overlay.setGeometry(self.rect())
            self.menu._update_position()

    def eventFilter(self, obj: Optional[QObject], event: Optional[QEvent]) -> bool:
        """
        Низкоуровневый перехватчик событий. 
        Нужен для подсчета фактических отрисованных кадров (FPS) 
        и для отслеживания мыши, чтобы показывать координаты возле курсора.
        """
        if obj == self.view.viewport() and event is not None:
            if event.type() == QEvent.Type.Paint:
                self._frame_count += 1
            elif event.type() == QEvent.Type.MouseMove and isinstance(event, QMouseEvent):
                mouse_event: QMouseEvent = event
                scene_pos = self.view.mapToScene(mouse_event.pos())
                self.lbl_coords.setText(f"X: {scene_pos.x():.1f} | Y: {scene_pos.y():.1f}")
                self.lbl_coords.adjustSize()
                
                window_pos = self.mapFromGlobal(mouse_event.globalPosition().toPoint())
                self.lbl_coords.move(window_pos.x() + 15, window_pos.y() + 15)
                
        return super().eventFilter(obj, event)

    def _update_fps_display(self) -> None:
        """Раз в секунду обновляет плашку с FPS и сбрасывает счетчик."""
        self.lbl_fps.setText(f"FPS: {self._frame_count}")
        self.lbl_fps.adjustSize()
        self._frame_count = 0

    def _update_ui_state(self) -> None:
        """Переключает цвета и текст на плашке статуса (Пауза / Симуляция)."""
        text = STATUS_TEXT_RUNNING if self.is_running else STATUS_TEXT_PAUSED
        style = STATUS_STYLE_RUNNING if self.is_running else STATUS_STYLE_PAUSED
        
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(style)
        self.lbl_status.adjustSize()
