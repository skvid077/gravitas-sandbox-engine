from collections.abc import Callable

from PyQt6.QtCore import QObject, QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QLinearGradient, QMouseEvent, QPainter, QWheelEvent
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QWidget

from config.constants import (
    MAX_COORD,
    MIN_COORD,
    SPACE_COLOR,
    SPACE_GRADIENT_END,
    SPACE_GRADIENT_MIDDLE,
    SPACE_GRADIENT_START,
    ZOOM_IN_FACTOR,
    ZOOM_MAX_SCALE,
    ZOOM_MIN_SCALE,
)
from config.models import BodyState
from gui.models import PlanetItem, PlanetItemLookup


class SpaceScene(QGraphicsScene):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.setBackgroundBrush(QColor(SPACE_COLOR))
        self.setSceneRect(MIN_COORD, MIN_COORD, MAX_COORD * 2, MAX_COORD * 2)
        self._planet_items: list[PlanetItem] = []

    def drawBackground(self, painter: QPainter | None, rect: QRectF) -> None:
        if painter is None:
            return

        views = self.views()
        if not views:
            painter.fillRect(rect, QColor(SPACE_COLOR))
            return

        viewport = views[0].viewport()
        if viewport is None:
            painter.fillRect(rect, QColor(SPACE_COLOR))
            return

        visible_rect = views[0].mapToScene(viewport.rect()).boundingRect()
        gradient = QLinearGradient(
            QPointF(visible_rect.center().x(), visible_rect.top()),
            QPointF(visible_rect.center().x(), visible_rect.bottom()),
        )
        gradient.setColorAt(0.0, QColor(SPACE_GRADIENT_START))
        gradient.setColorAt(0.56, QColor(SPACE_GRADIENT_MIDDLE))
        gradient.setColorAt(1.0, QColor(SPACE_GRADIENT_END))
        painter.fillRect(rect, gradient)

    def remove_body_by_index(self, index: int) -> None:
        if 0 <= index < len(self._planet_items):
            item = self._planet_items.pop(index)
            self.removeItem(item)

    def clear_planets(self) -> None:
        for item in self._planet_items:
            self.removeItem(item)
        self._planet_items.clear()

    def sync_bodies(
        self,
        bodies: list[BodyState],
        edit_callback: Callable[[PlanetItem], None],
    ) -> None:
        live_body_ids = {id(body) for body in bodies}
        for item in self._planet_items.copy():
            if id(item.body_state) not in live_body_ids:
                self.removeItem(item)
                self._planet_items.remove(item)

        items_by_body_id = PlanetItemLookup(self._planet_items)
        for body in bodies:
            matched_item = items_by_body_id.find(body)
            if matched_item is None:
                self.add_body(body, edit_callback)
            else:
                matched_item.body_state = body

    def add_body(
        self, body_state: BodyState, edit_callback: Callable[[PlanetItem], None]
    ) -> PlanetItem:
        item = PlanetItem(body_state, edit_callback, self._planet_items)
        self.addItem(item)
        self._planet_items.append(item)
        return item

    def update_body_by_index(self, index: int, new_state: BodyState) -> None:
        if 0 <= index < len(self._planet_items):
            self._planet_items[index].body_state = new_state


class SpaceView(QGraphicsView):
    right_click_empty = pyqtSignal(float, float)

    def __init__(self, scene: SpaceScene, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.ArrowCursor)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            super().mousePressEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if not item:  # Если кликнули не по планете
                self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        super().mouseReleaseEvent(event)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def wheelEvent(self, event: QWheelEvent | None) -> None:
        if event is None:
            return

        zoom_out_factor: float = 1 / ZOOM_IN_FACTOR

        old_scale: float = self.transform().m11()
        factor: float = ZOOM_IN_FACTOR if event.angleDelta().y() > 0 else zoom_out_factor

        new_scale: float = old_scale * factor
        if new_scale < ZOOM_MIN_SCALE or new_scale > ZOOM_MAX_SCALE:
            return

        self.scale(factor, factor)
