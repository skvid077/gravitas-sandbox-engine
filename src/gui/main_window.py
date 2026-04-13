import json
from typing import Optional, Any, List, Dict

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QResizeEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
)

from config.constants import *
from config.schemas import BodyState, SimulationScenario
from gui.planet_dialog import PlanetDialog
from gui.planet_item import PlanetItem
from gui.scene import SpaceScene
from gui.views import InfiniteView


class MainWindow(QMainWindow):
    """
    Главное окно приложения "Infinite Chunk Engine".
    Оркестрирует сцену, камеру (InfiniteView) и элементы пользовательского интерфейса.
    Управляет жизненным циклом сценария симуляции (создание, редактирование, экспорт).
    """

    def __init__(self, scenario: Optional[SimulationScenario] = None) -> None:
        """
        Инициализирует главное окно и графический движок.

        Args:
            scenario (Optional[SimulationScenario]): Загруженный сценарий симуляции. 
                Если None, создается пустой сценарий с именем "Custom".
        """
        super().__init__()
        
        # Инкапсулируем состояние и ссылки
        self._scenario: SimulationScenario = scenario or SimulationScenario(name="Custom", bodies=[])
        self._planet_items: List[PlanetItem] = []  # Хранит ссылки на графические объекты для просчета коллизий
        
        title: str = f"Infinite Chunk Engine - {self._scenario.name}"
        self.setWindowTitle(title)

        # Центрирование и размеры окна
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumSize(MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT)
        self.resize(screen.width() // SCREEN_RATIO_DIVISOR, screen.height() // SCREEN_RATIO_DIVISOR)

        # 1. Инициализация сцены и бесконечной камеры
        self._scene: SpaceScene = SpaceScene(self)
        self._scene.setSceneRect(-COUNT_CHUNKS, -COUNT_CHUNKS, 2 * COUNT_CHUNKS, 2 * COUNT_CHUNKS)
        
        self._view: InfiniteView = InfiniteView(self._scene)
        self.setCentralWidget(self._view)
        self._view.centerOn(VIEW_CENTER_X, VIEW_CENTER_Y)
        
        self._view.right_clicked.connect(self.open_planet_dialog_at_pos)

        # Первичная отрисовка тел из загруженного JSON
        if self._scenario.bodies:
            self._spawn_scenario_bodies()

        # 2. Инициализация UI-элементов поверх холста
        self._init_ui_buttons()

    def _init_ui_buttons(self) -> None:
        """Создает и настраивает плавающие кнопки интерфейса (Меню, Добавить, Экспорт)."""
        self._btn_toggle = QPushButton("🛠", self)
        self._btn_toggle.setFixedSize(BTN_TOGGLE_SIZE, BTN_TOGGLE_SIZE)
        self._btn_toggle.setStyleSheet(STYLE_BTN_TOGGLE_CLOSED)
        self._btn_toggle.clicked.connect(self.toggle_menu)

        self._btn_add_planet = QPushButton("🪐 Добавить планету", self)
        self._btn_add_planet.setFixedSize(BTN_MENU_WIDTH, BTN_MENU_HEIGHT)
        self._btn_add_planet.setStyleSheet(STYLE_BTN_MENU_PLANET)
        self._btn_add_planet.clicked.connect(self.open_planet_dialog_center)
        self._btn_add_planet.hide()

        self._btn_export = QPushButton("💾 Сохранить JSON", self)
        self._btn_export.setFixedSize(BTN_MENU_WIDTH, BTN_MENU_HEIGHT)
        self._btn_export.setStyleSheet(STYLE_BTN_MENU_EXPORT)
        self._btn_export.clicked.connect(self.export_to_json)
        self._btn_export.hide()

    def toggle_menu(self) -> None:
        """Переключает состояние бокового меню (открыто/закрыто) с изменением стилей."""
        if self._btn_add_planet.isVisible():
            self._btn_add_planet.hide()
            self._btn_export.hide()
            self._btn_toggle.setText("🛠")
            self._btn_toggle.setStyleSheet(STYLE_BTN_TOGGLE_CLOSED)
        else:
            self._btn_add_planet.show()
            self._btn_export.show()
            self._btn_toggle.setText("✖")
            self._btn_toggle.setStyleSheet(STYLE_BTN_TOGGLE_OPEN)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Обрабатывает изменение размеров окна, динамически пересчитывая позиции плавающих кнопок.
        """
        super().resizeEvent(event)
        
        tx: int = self.width() - self._btn_toggle.width() - UI_MARGIN
        self._btn_toggle.move(tx, UI_MARGIN)
        
        ax: int = self.width() - self._btn_add_planet.width() - UI_MARGIN
        ay: int = UI_MARGIN + self._btn_toggle.height() + UI_SPACING
        self._btn_add_planet.move(ax, ay)
        
        ex: int = self.width() - self._btn_export.width() - UI_MARGIN
        ey: int = ay + self._btn_add_planet.height() + UI_SPACING
        self._btn_export.move(ex, ey)

    def export_to_json(self) -> None:
        """
        Сериализует текущий сценарий с помощью Pydantic и сохраняет его в JSON файл.
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить сценарий", "", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                # В Pydantic v2 model_dump() возвращает чистый словарь
                data_dict: Dict[str, Any] = self._scenario.model_dump()
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data_dict, f, indent=JSON_INDENT, ensure_ascii=False)
                QMessageBox.information(self, "Успех", f"Сценарий '{self._scenario.name}' успешно сохранен!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка экспорта", f"Не удалось сохранить файл:\n{e}")

    def _spawn_scenario_bodies(self) -> None:
        """Итеративно спавнит все тела, присутствующие в Pydantic-модели сценария."""
        for body in self._scenario.bodies:
            self._spawn_single_body(body)

    def open_planet_dialog_center(self) -> None:
        """Открывает диалог добавления планеты точно по центру видимого экрана камеры."""
        center_pos: QPointF = self._view.mapToScene(self._view.viewport().rect().center())
        self._show_add_dialog(center_pos.x(), center_pos.y())

    def open_planet_dialog_at_pos(self, pos: QPointF) -> None:
        """Открывает диалог добавления планеты в заданных мировых координатах (по правому клику)."""
        self._show_add_dialog(pos.x(), pos.y())

    def _show_add_dialog(self, x: float, y: float) -> None:
        """
        Внутренний метод для вызова окна `PlanetDialog` в режиме создания нового тела.
        """
        dialog = PlanetDialog(self, default_x=x, default_y=y, all_bodies=self._scenario.bodies)
        if dialog.exec(): 
            new_body: Optional[BodyState] = dialog.final_body_state
            if new_body:
                self._scenario.bodies.append(new_body)
                self._spawn_single_body(new_body)

    def edit_planet_dialog(self, planet_item: PlanetItem) -> None:
        """
        Коллбек, вызываемый при двойном клике на планету на сцене. 
        Открывает диалог в режиме редактирования.
        
        Args:
            planet_item (PlanetItem): Объект графической сцены, запросивший редактирование.
        """
        dialog = PlanetDialog(
            self, 
            existing_body=planet_item.body_state, 
            all_bodies=self._scenario.bodies
        )
        if dialog.exec():
            new_state: Optional[BodyState] = dialog.final_body_state
            if new_state:
                # 1. Обновляем Pydantic состояние в глобальном сценарии
                idx: int = self._scenario.bodies.index(planet_item.body_state)
                self._scenario.bodies[idx] = new_state
                
                # 2. Обновляем состояние самого графического элемента
                # Благодаря декоратору @property.setter в PlanetItem, 
                # перерисовка визуальной части вызовется автоматически.
                planet_item.body_state = new_state

    def _spawn_single_body(self, body: BodyState) -> None:
        """
        Создает объект `PlanetItem`, передает ему необходимые зависимости 
        и добавляет на QGraphicsScene.
        """
        planet = PlanetItem(
            body_state=body, 
            edit_callback=self.edit_planet_dialog, 
            planet_list_ref=self._planet_items
        )
        self._planet_items.append(planet)
        self._scene.addItem(planet)
