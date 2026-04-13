import time
from typing import Any

from PyQt6.QtCore import Qt, QPointF, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QWheelEvent, QMouseEvent, QPaintEvent
from PyQt6.QtWidgets import QGraphicsView, QLabel, QGraphicsScene

from config.constants import *
from gui.planet_item import PlanetItem 


# Локальные константы для UI камеры (можно перенести в constants.py)
FPS_UPDATE_INTERVAL_SEC: float = 1.0
FPS_LABEL_MARGIN: int = 10
COORD_LABEL_OFFSET_X: int = 15
COORD_LABEL_OFFSET_Y: int = 15


class InfiniteView(QGraphicsView):
    """
    Кастомный виджет камеры для бесконечного перемещения по сцене.
    
    Поддерживает:
    - Панорамирование (перемещение) левой кнопкой мыши.
    - Зум колесиком мыши относительно позиции курсора.
    - Динамическое отображение мировых координат и счетчика FPS.
    - Отправку сигнала right_clicked для спавна объектов.
    """
    
    # Сигнал, испускаемый при клике правой кнопкой (передает мировые координаты)
    right_clicked = pyqtSignal(QPointF)

    def __init__(self, scene: QGraphicsScene) -> None:
        """
        Инициализирует вьюпорт камеры.

        Args:
            scene (QGraphicsScene): Сцена, которую будет отображать данная камера.
        """
        super().__init__(scene)
        
        # Инкапсуляция внутреннего состояния
        self._frames: int = 0
        self._last_fps_time: float = time.time()
        self._is_panning: bool = False
        self._last_mouse_pos: QPointF = QPointF()
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Настраивает визуальные параметры вьюпорта и оверлеи (FPS, координаты)."""
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.viewport().setMouseTracking(True) 
        self.setMouseTracking(True)

        # Ярлык координат курсора
        self._coord_label: QLabel = QLabel(self)
        self._coord_label.setStyleSheet(COORD_LABEL_STYLE)
        self._coord_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._coord_label.hide()

        # Ярлык счетчика FPS
        self._fps_label: QLabel = QLabel("FPS: --", self)
        self._fps_label.setStyleSheet(FPS_LABEL_STYLE)
        self._fps_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._fps_label.move(FPS_LABEL_MARGIN, FPS_LABEL_MARGIN)
        self._fps_label.show()

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Переопределенный метод отрисовки.
        Вызывается каждый раз, когда Qt обновляет кадр.
        """
        super().paintEvent(event)
        self._update_fps_counter()

    def _update_fps_counter(self) -> None:
        """Внутренний метод для подсчета и обновления метрики кадров в секунду (FPS)."""
        self._frames += 1
        current_time: float = time.time()
        elapsed: float = current_time - self._last_fps_time
        
        if elapsed >= FPS_UPDATE_INTERVAL_SEC:
            fps: float = self._frames / elapsed
            self._fps_label.setText(f"FPS: {int(fps)}")
            self._fps_label.adjustSize()
            
            self._frames = 0
            self._last_fps_time = current_time

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Обрабатывает прокрутку колеса мыши для масштабирования (зума).
        Также управляет видимостью текста (LOD) в зависимости от текущего масштаба.
        """
        if event.angleDelta().y() > 0:
            self.scale(ZOOM_FACTOR, ZOOM_FACTOR)
        else:
            self.scale(1.0 / ZOOM_FACTOR, 1.0 / ZOOM_FACTOR)

        current_zoom: float = self.transform().m11()
        show_text: bool = current_zoom > TEXT_VISIBLE_ZOOM_THRESHOLD 
        
        # Обновляем видимость текста.
        # Так как звезды рисуются в background, items() вернет только планеты и их текст,
        # что делает этот цикл достаточно быстрым.
        for item in self.scene().items():
            if isinstance(item, PlanetItem):
                item.text_item.setVisible(show_text)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Обрабатывает нажатия мыши:
        ЛКМ по планете -> захват объекта (отдается базовому классу).
        ЛКМ по пустоте -> начало панорамирования камеры.
        ПКМ -> испускание сигнала для добавления новой планеты.
        """
        # 1. Проверяем, кликнули ли мы по планете
        clicked_items = self.items(event.position().toPoint())
        is_planet: bool = any(isinstance(item, PlanetItem) for item in clicked_items)

        if is_planet:
            super().mousePressEvent(event)
            return

        # 2. Панорамирование
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_panning = True
            self._last_mouse_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            
        # 3. Добавление объекта
        elif event.button() == Qt.MouseButton.RightButton:
            scene_pos: QPointF = self.mapToScene(event.position().toPoint())
            self.right_clicked.emit(scene_pos)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Обрабатывает движение мыши. 
        Обновляет ярлык мировых координат и смещает камеру, если активно панорамирование.
        """
        current_pos_point: QPoint = event.position().toPoint()
        
        # Обновление оверлея координат
        scene_pos: QPointF = self.mapToScene(current_pos_point)
        self._coord_label.setText(f"x: {int(scene_pos.x())}\ny: {int(scene_pos.y())}")
        self._coord_label.adjustSize()
        self._coord_label.move(
            current_pos_point + QPoint(COORD_LABEL_OFFSET_X, COORD_LABEL_OFFSET_Y)
        )
        self._coord_label.show()

        # Движение камеры
        if self._is_panning:
            delta: QPointF = event.position() - self._last_mouse_pos
            self._last_mouse_pos = event.position()
            
            # Смещаем ползунки скроллбаров (которые скрыты) для перемещения вида
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            h_bar.setValue(h_bar.value() - int(delta.x()))
            v_bar.setValue(v_bar.value() - int(delta.y()))
            
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Сбрасывает флаг панорамирования при отпускании левой кнопки мыши."""
        if event.button() == Qt.MouseButton.LeftButton and self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            
        super().mouseReleaseEvent(event)
    
    def leaveEvent(self, event: Any) -> None:
        """Скрывает оверлей координат, если курсор покинул окно приложения."""
        self._coord_label.hide()
        super().leaveEvent(event)
