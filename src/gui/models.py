from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QBrush, QColor, QPen
from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsSceneMouseEvent, QGraphicsTextItem

from config.constants import (
    LUMA_B_WEIGHT,
    LUMA_DENOMINATOR,
    LUMA_G_WEIGHT,
    LUMA_R_WEIGHT,
    PLANET_TEXT_MAX_SCALE,
    PLANET_TEXT_WIDTH_FACTOR,
    TEXT_COLOR_LUMA_THRESHOLD,
)
from config.models import BodyState


class PlanetItem(QGraphicsEllipseItem):
    def __init__(
        self,
        body_state: BodyState,
        edit_callback: Callable[["PlanetItem"], None],
        planet_list_ref: list["PlanetItem"],
    ) -> None:
        super().__init__()
        self._body_state: BodyState = body_state
        self._edit_callback: Callable[["PlanetItem"], None] = edit_callback
        self._planet_list: list["PlanetItem"] = planet_list_ref
        self._syncing_position = False

        self._text_item: QGraphicsTextItem = QGraphicsTextItem(self)
        self._text_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setFlags(
            QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.update_visuals()

    @property
    def body_state(self) -> BodyState:
        return self._body_state

    @body_state.setter
    def body_state(self, new_state: BodyState) -> None:
        self._body_state = new_state
        self.update_visuals()

    def update_visuals(self) -> None:
        r = self._body_state.radius
        self.setRect(-r, -r, r * 2.0, r * 2.0)
        self._syncing_position = True
        try:
            self.setPos(self._body_state.position[0], self._body_state.position[1])
        finally:
            self._syncing_position = False

        self.setBrush(QBrush(QColor(self._body_state.color)))
        self.setPen(QPen(Qt.PenStyle.NoPen))

        self._update_text()

    def _update_text(self) -> None:
        self._text_item.setPlainText(self._body_state.name)
        color = QColor(self._body_state.color)
        brightness = (
            color.red() * LUMA_R_WEIGHT
            + color.green() * LUMA_G_WEIGHT
            + color.blue() * LUMA_B_WEIGHT
        ) / LUMA_DENOMINATOR
        text_color = (
            Qt.GlobalColor.black if brightness > TEXT_COLOR_LUMA_THRESHOLD else Qt.GlobalColor.white
        )
        self._text_item.setDefaultTextColor(text_color)
        t_rect = self._text_item.boundingRect()
        if t_rect.width() > 0:
            target_width = self._body_state.radius * PLANET_TEXT_WIDTH_FACTOR
            scale = min(target_width / t_rect.width(), PLANET_TEXT_MAX_SCALE)
            self._text_item.setScale(scale)
            self._text_item.setPos(-t_rect.width() * scale / 2.0, -t_rect.height() * scale / 2.0)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        if event is None:
            return
        self._edit_callback(self)
        super().mouseDoubleClickEvent(event)

    def itemChange(self, change: QGraphicsEllipseItem.GraphicsItemChange, value: Any) -> Any:
        if (
            change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange
            and isinstance(value, QPointF)
            and not self._syncing_position
        ):
            target_pos: QPointF = value
            tx, ty = target_pos.x(), target_pos.y()
            r_self = self._body_state.radius
            for other in self._planet_list:
                if other is self:
                    continue

                dx = tx - other.pos().x()
                dy = ty - other.pos().y()
                min_dist = r_self + other.body_state.radius
                if (dx * dx + dy * dy) < (min_dist * min_dist):
                    return self.pos()
            self._body_state.position = (tx, ty)

        return super().itemChange(change, value)


class PlanetItemLookup:
    def __init__(self, items: list[PlanetItem]) -> None:
        self._items_by_body_id = {id(item.body_state): item for item in items}

    def find(self, body: BodyState) -> PlanetItem | None:
        return self._items_by_body_id.get(id(body))
