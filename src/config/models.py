from typing import Callable, Any, List
from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
from PyQt6.QtGui import QBrush, QColor, QPen
from PyQt6.QtCore import Qt, QPointF

from config.schemas import BodyState

class PlanetItem(QGraphicsEllipseItem):
    """
    Визуальное представление планеты на сцене.
    Умеет отрисовывать себя, подбирать контрастный текст и 
    предотвращать наложения при перетаскивании мышкой.
    """
    def __init__(
        self, 
        body_state: BodyState, 
        edit_callback: Callable[['PlanetItem'], None], 
        planet_list_ref: List['PlanetItem']
    ) -> None:
        super().__init__()
        self._body_state: BodyState = body_state
        self._edit_callback: Callable[['PlanetItem'], None] = edit_callback
        self._planet_list: List['PlanetItem'] = planet_list_ref
        
        self._text_item: QGraphicsTextItem = QGraphicsTextItem(self)
        self._text_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        
        # Настройки взаимодействия: перетаскивание, выбор и отслеживание изменений геометрии
        self.setFlags(
            QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable | 
            QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable | 
            QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges
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
        """Синхронизирует графику с данными из BodyState."""
        r = self._body_state.radius
        self.setRect(-r, -r, r * 2.0, r * 2.0)
        self.setPos(self._body_state.position[0], self._body_state.position[1])
        
        self.setBrush(QBrush(QColor(self._body_state.color)))
        self.setPen(QPen(Qt.PenStyle.NoPen))
        
        self._update_text()

    def _update_text(self) -> None:
        """Обновляет название внутри планеты (без массы) и центрирует его."""
        self._text_item.setPlainText(self._body_state.name)
        
        # Подбор контрастного цвета текста
        color = QColor(self._body_state.color)
        brightness = (color.red() * 299 + color.green() * 587 + color.blue() * 114) / 1000
        text_color = Qt.GlobalColor.black if brightness > 140 else Qt.GlobalColor.white
        self._text_item.setDefaultTextColor(text_color)
        
        # Масштабирование текста под радиус планеты
        t_rect = self._text_item.boundingRect()
        if t_rect.width() > 0:
            target_width = self._body_state.radius * 1.5
            scale = min(target_width / t_rect.width(), 1.5)
            self._text_item.setScale(scale)
            
            # Центрируем текст внутри круга
            self._text_item.setPos(
                -t_rect.width() * scale / 2.0, 
                -t_rect.height() * scale / 2.0
            )

    def mouseDoubleClickEvent(self, event) -> None:
        """Открывает окно редактирования."""
        if self._edit_callback:
            self._edit_callback(self)
        super().mouseDoubleClickEvent(event)

    def itemChange(self, change: QGraphicsEllipseItem.GraphicsItemChange, value: Any) -> Any:
        """
        Предотвращает наложение планет друг на друга при перетаскивании.
        """
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange:
            target_pos: QPointF = value
            tx, ty = target_pos.x(), target_pos.y()
            r_self = self._body_state.radius
            
            # Проверяем расстояние до всех остальных планет
            for other in self._planet_list:
                if other is self:
                    continue
                
                dx = tx - other.pos().x()
                dy = ty - other.pos().y()
                min_dist = r_self + other.body_state.radius
                
                # Если расстояние меньше суммы радиусов — блокируем перемещение
                if (dx * dx + dy * dy) < (min_dist * min_dist):
                    return self.pos() # Возвращаем текущую (старую) позицию
            
            # Если столкновений нет, обновляем координаты в модели данных
            self._body_state.position = (tx, ty)
            
        return super().itemChange(change, value)
