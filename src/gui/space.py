import random
import math
from typing import Dict, List, Tuple

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPainter, QColor, QWheelEvent, QMouseEvent
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal

from gui.models import PlanetItem

from src.config.constants import (
    CHUNK_SIZE, HASH_SEED_X, HASH_SEED_Y, SPACE_COLOR, 
    MIN_STARS_PER_CHUNK, MAX_STARS_PER_CHUNK, SIZE_STAR_MIN, SIZE_STAR_MAX,
    OPACITY_MIN, OPACITY_MAX, STAR_PALETTE, STARS_LOD_THRESHOLD, MAX_VISIBLE_CHUNKS,
    MIN_COORD, MAX_COORD
)

class SpaceScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QColor(SPACE_COLOR))
        self.setSceneRect(MIN_COORD, MIN_COORD, MAX_COORD * 2, MAX_COORD * 2)
        self._chunk_cache = {}
        self._planet_items = []

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """Отрисовка фона. Мы игнорируем входящий rect для стабильности чанков."""
        # Всегда заливаем фон, чтобы не было 'шлейфов' при перемещении
        painter.fillRect(rect, QColor(SPACE_COLOR))
        
        # Получаем доступ к вьюпорту, чтобы знать РЕАЛЬНУЮ видимую область
        if not self.views():
            return
        
        view = self.views()[0]
        # Рассчитываем видимую область сцены в данный момент
        visible_rect = view.mapToScene(view.viewport().rect()).boundingRect()

        # Если зум слишком мелкий (видна огромная область), отключаем звезды для FPS
        if visible_rect.width() > STARS_LOD_THRESHOLD:
            return

        # Паддинг в 2 чанка гарантирует, что за краем экрана всегда есть готовые звезды
        p = CHUNK_SIZE * 2
        start_cx = math.floor((visible_rect.left() - p) / CHUNK_SIZE)
        end_cx = math.floor((visible_rect.right() + p) / CHUNK_SIZE)
        start_cy = math.floor((visible_rect.top() - p) / CHUNK_SIZE)
        end_cy = math.floor((visible_rect.bottom() + p) / CHUNK_SIZE)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        # Рисуем чанки, основываясь на видимости всего экрана + запас
        for cx in range(start_cx, end_cx + 1):
            for cy in range(start_cy, end_cy + 1):
                self._draw_chunk(painter, cx, cy)
    
    def remove_body_by_index(self, index: int) -> None:
        """Удаляет графический объект планеты со сцены."""
        if hasattr(self, 'planet_items') and 0 <= index < len(self.planet_items):
            item = self.planet_items.pop(index)
            self.removeItem(item)
    
    def clear_planets(self) -> None:
        """Гарантированно удаляет все графические объекты планет со сцены.""" # Убедись, что импорт есть
        
        # Удаляем сами элементы с экрана
        for item in self.items():
            if isinstance(item, PlanetItem):
                self.removeItem(item)
                
        # Если у тебя есть внутренние списки, очищаем их на всякий случай
        if hasattr(self, '_planet_items'):
            self._planet_items.clear()
        elif hasattr(self, 'planet_items'):
            self.planet_items.clear()

    def _draw_chunk(self, painter: QPainter, cx: int, cy: int):
        key = (cx, cy)
        if key not in self._chunk_cache:
            random.seed(cx * HASH_SEED_X + cy * HASH_SEED_Y)
            stars = []
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

    def add_body(self, body_state, edit_callback):
        item = PlanetItem(body_state, edit_callback, self._planet_items)
        self.addItem(item)
        self._planet_items.append(item)
        return item
    
    def update_body_by_index(self, index: int, new_state):
        """Обновляет ссылку на данные и перерисовывает планету."""
        if 0 <= index < len(self._planet_items):
            # Используем сеттер, который мы написали в PlanetItem
            self._planet_items[index].body_state = new_state

class SpaceView(QGraphicsView):
    right_click_empty = pyqtSignal(float, float)
    def __init__(self, scene: SpaceScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        # Убираем постоянный ScrollHandDrag, чтобы вернуть дефолтный курсор
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.ArrowCursor) 
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        self.min_scale = 0.005
        self.max_scale = 50.0

    def mousePressEvent(self, event: QMouseEvent):
        # Включаем режим перетаскивания только при нажатии на пустую область
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if not item: # Если кликнули не по планете
                self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        # Возвращаем дефолтный курсор после отпускания кнопки
        super().mouseReleaseEvent(event)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def wheelEvent(self, event: QWheelEvent):
        """Плавный зум (коэффициент 1.05 вместо 1.1 или 1.25)."""
        # Смягчаем шаг зума
        zoom_in_factor = 1.05 
        zoom_out_factor = 1 / zoom_in_factor
        
        old_scale = self.transform().m11()
        factor = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor
            
        new_scale = old_scale * factor
        # Защита от 'улетания' в бесконечно малый или большой масштаб
        if new_scale < self.min_scale or new_scale > self.max_scale:
            return

        self.scale(factor, factor)
