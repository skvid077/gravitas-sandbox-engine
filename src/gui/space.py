import random
import math
from typing import Dict, List, Tuple, Callable, Optional

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QWidget
from PyQt6.QtGui import QPainter, QColor, QWheelEvent, QMouseEvent
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject

from config.schemas import BodyState
from gui.models import PlanetItem

from config.constants import (
    CHUNK_SIZE,
    HASH_SEED_X,
    HASH_SEED_Y,
    SPACE_COLOR,
    MIN_STARS_PER_CHUNK,
    MAX_STARS_PER_CHUNK,
    SIZE_STAR_MIN,
    SIZE_STAR_MAX,
    OPACITY_MIN,
    OPACITY_MAX,
    STAR_PALETTE,
    STARS_LOD_THRESHOLD,
    MIN_COORD,
    MAX_COORD,
    ZOOM_IN_FACTOR,
    ZOOM_MAX_SCALE,
    ZOOM_MIN_SCALE
)


class SpaceScene(QGraphicsScene):
    """
    Графическая сцена, отвечающая за управление и отрисовку всех объектов в космосе.
    Включает в себя бесконечную генерацию звездного фона (чанками) и управление планетами.
    """

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """
        Инициализирует космическую сцену.

        Args:
            parent (Optional[QObject], optional): Родительский виджет. По умолчанию None.
        """
        super().__init__(parent)
        self.setBackgroundBrush(QColor(SPACE_COLOR))
        self.setSceneRect(MIN_COORD, MIN_COORD, MAX_COORD * 2, MAX_COORD * 2)
        
        # Строгая типизация кэша звездного неба (X, Y, Радиус, Цвет)
        self._chunk_cache: Dict[Tuple[int, int], List[Tuple[float, float, float, QColor]]] = {}
        # Строгий список графических элементов планет
        self._planet_items: List[PlanetItem] = []

    def drawBackground(self, painter: QPainter | None, rect: QRectF) -> None:
        """
        Отрисовывает звездный фон. Использует систему чанков для оптимизации:
        звезды генерируются только в пределах видимой области (viewport).

        Args:
            painter (QPainter | None): Инструмент отрисовки PyQt.
            rect (QRectF): Область, требующая перерисовки.
        """
        if painter is None:
            return

        painter.fillRect(rect, QColor(SPACE_COLOR))
        
        views = self.views()
        if not views:
            return
        
        view = views[0]
        viewport = view.viewport()
        if viewport is None:
            return

        visible_rect = view.mapToScene(viewport.rect()).boundingRect()

        # Отключаем звезды при сильном отдалении для экономии FPS
        if visible_rect.width() > STARS_LOD_THRESHOLD:
            return

        p = CHUNK_SIZE * 2
        start_cx = math.floor((visible_rect.left() - p) / CHUNK_SIZE)
        end_cx = math.floor((visible_rect.right() + p) / CHUNK_SIZE)
        start_cy = math.floor((visible_rect.top() - p) / CHUNK_SIZE)
        end_cy = math.floor((visible_rect.bottom() + p) / CHUNK_SIZE)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        for cx in range(start_cx, end_cx + 1):
            for cy in range(start_cy, end_cy + 1):
                self._draw_chunk(painter, cx, cy)
    
    def remove_body_by_index(self, index: int) -> None:
        """
        Удаляет графический объект планеты со сцены по её индексу.

        Args:
            index (int): Индекс планеты в массиве симуляции.
        """
        if 0 <= index < len(self._planet_items):
            item = self._planet_items.pop(index)
            self.removeItem(item)
    
    def clear_planets(self) -> None:
        """
        Гарантированно удаляет все планеты со сцены и очищает внутренний массив.
        """
        for item in self._planet_items:
            self.removeItem(item)
        self._planet_items.clear()

    def _draw_chunk(self, painter: QPainter, cx: int, cy: int) -> None:
        """
        Рисует один сектор (чанк) звездного неба. Если чанк отрисовывается впервые,
        его звезды генерируются с помощью фиксированного seed и кэшируются.

        Args:
            painter (QPainter): Инструмент отрисовки.
            cx (int): X-координата чанка.
            cy (int): Y-координата чанка.
        """
        key = (cx, cy)
        if key not in self._chunk_cache:
            random.seed(cx * HASH_SEED_X + cy * HASH_SEED_Y)
            stars: List[Tuple[float, float, float, QColor]] = []
            for _ in range(random.randint(MIN_STARS_PER_CHUNK, MAX_STARS_PER_CHUNK)):
                x = cx * CHUNK_SIZE + random.uniform(0, CHUNK_SIZE)
                y = cy * CHUNK_SIZE + random.uniform(0, CHUNK_SIZE)
                r = random.uniform(SIZE_STAR_MIN, SIZE_STAR_MAX)
                c = QColor(random.choice(STAR_PALETTE))
                c.setAlphaF(random.uniform(OPACITY_MIN, OPACITY_MAX))
                stars.append((x, y, r, c))
            self._chunk_cache[key] = stars
        
        for x, y, r, c in self._chunk_cache[key]:
            painter.setBrush(c)
            painter.drawEllipse(QPointF(x, y), r, r)

    def add_body(self, body_state: BodyState, edit_callback: Callable[[PlanetItem], None]) -> PlanetItem:
        """
        Создает графический объект (PlanetItem) на основе физического состояния и добавляет его на сцену.

        Args:
            body_state (BodyState): Физические параметры новой планеты.
            edit_callback (Callable[[PlanetItem], None]): Функция, вызываемая при двойном клике по планете.

        Returns:
            PlanetItem: Созданный графический элемент.
        """
        item = PlanetItem(body_state, edit_callback, self._planet_items)
        self.addItem(item)
        self._planet_items.append(item)
        return item

    def update_body_by_index(self, index: int, new_state: BodyState) -> None:
        """
        Обновляет ссылку на данные и перерисовывает существующую планету.

        Args:
            index (int): Индекс обновляемой планеты.
            new_state (BodyState): Новое физическое состояние после шага симуляции.
        """
        if 0 <= index < len(self._planet_items):
            self._planet_items[index].body_state = new_state


class SpaceView(QGraphicsView):
    """
    Камера (Viewport) для наблюдения за космической сценой.
    Реализует навигацию: перетаскивание мышью, плавный зум и создание планет по клику.
    """
    
    right_click_empty = pyqtSignal(float, float)

    def __init__(self, scene: SpaceScene, parent: Optional[QWidget] = None) -> None:
        """
        Инициализирует окно просмотра (камеру).

        Args:
            scene (SpaceScene): Сцена космоса, которую нужно отображать.
            parent (Optional[QWidget], optional): Родительский виджет. По умолчанию None.
        """
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        # Убираем постоянный ScrollHandDrag, чтобы вернуть дефолтный курсор
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.ArrowCursor) 
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        """
        Обрабатывает нажатие кнопок мыши. Включает режим перетаскивания карты
        только если пользователь кликнул по пустому космосу.
        """
        if event is None:
            super().mousePressEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if not item:  # Если кликнули не по планете
                self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        """Обрабатывает отпускание кнопки мыши, выключая режим перетаскивания."""
        super().mouseReleaseEvent(event)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def wheelEvent(self, event: QWheelEvent | None) -> None:
        """
        Обрабатывает прокрутку колесика мыши для плавного зума.
        Защищает от отдаления или приближения за пределы лимитов.
        """
        if event is None:
            return

        zoom_out_factor: float = 1 / ZOOM_IN_FACTOR
        
        old_scale: float = self.transform().m11()
        factor: float = ZOOM_IN_FACTOR if event.angleDelta().y() > 0 else zoom_out_factor
            
        new_scale: float = old_scale * factor
        
        # Защита от 'улетания' в бесконечно малый или большой масштаб
        if new_scale < ZOOM_MIN_SCALE or new_scale > ZOOM_MAX_SCALE:
            return

        self.scale(factor, factor)
