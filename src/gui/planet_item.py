from typing import Callable, Any, List
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QBrush, QColor, QPen
from PyQt6.QtWidgets import (
    QGraphicsEllipseItem, 
    QGraphicsSceneMouseEvent, 
    QGraphicsTextItem
)

from config.constants import *
from config.schemas import BodyState


class PlanetItem(QGraphicsEllipseItem):
    """
    Графическое представление космического тела на сцене симуляции.

    Отвечает за отрисовку геометрии, адаптивное форматирование текста (имя, масса)
    и обработку коллизий в реальном времени при взаимодействии пользователя.
    """

    def __init__(
        self, 
        body_state: BodyState, 
        edit_callback: Callable[['PlanetItem'], None],
        planet_list_ref: List['PlanetItem']
    ) -> None:
        """
        Инициализация графического элемента планеты.

        Args:
            body_state (BodyState): Модель с физическими параметрами планеты.
            edit_callback (Callable): Функция, вызываемая при двойном клике для редактирования.
            planet_list_ref (List[PlanetItem]): Ссылка на список всех планет для оптимизированного просчета коллизий.
        """
        super().__init__()
        
        # Инкапсуляция внутреннего состояния
        self._body_state: BodyState = body_state
        self._edit_callback: Callable[['PlanetItem'], None] = edit_callback
        self._planet_list: List['PlanetItem'] = planet_list_ref
        
        self._text_item: QGraphicsTextItem = QGraphicsTextItem(self)
        self._text_item.setDefaultTextColor(Qt.GlobalColor.white)
        self._text_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        
        font = self._text_item.font()
        font.setBold(True)
        self._text_item.setFont(font)
        
        self.setZValue(PLANET_Z_VALUE)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.update_visuals()

    @property
    def body_state(self) -> BodyState:
        """
        BodyState: Геттер для получения текущего физического состояния планеты.
        """
        return self._body_state

    @body_state.setter
    def body_state(self, new_state: BodyState) -> None:
        """Сеттер для обновления состояния с автоматической перерисовкой графики."""
        self._body_state = new_state
        self.update_visuals()

    @staticmethod
    def calculate_luminance(color: QColor) -> float:
        """
        Вычисляет воспринимаемую яркость цвета по формуле YIQ.
        
        Args:
            color (QColor): Объект цвета Qt.
            
        Returns:
            float: Значение яркости от 0.0 до 255.0.
        """
        return (
            color.red() * LUMA_R_WEIGHT + 
            color.green() * LUMA_G_WEIGHT + 
            color.blue() * LUMA_B_WEIGHT
        ) / LUMA_DENOMINATOR

    def update_visuals(self) -> None:
        """Обновляет геометрию, позицию и заливку элемента на основе состояния."""
        radius: float = self._body_state.radius
        self.setRect(-radius, -radius, radius * 2.0, radius * 2.0)
        self.setPos(self._body_state.position[0], self._body_state.position[1])
        
        self.setBrush(QBrush(QColor(self._body_state.color)))
        self.setPen(QPen(Qt.PenStyle.NoPen))
        
        self._update_text()

    def _update_text(self) -> None:
        """
        Обновляет текстовую метку планеты, подбирая контрастный цвет 
        и масштабируя текст под размер радиуса.
        """
        info: str = (
            f"[{self._body_state.name}]\n"
            f"m:{int(self._body_state.mass)} r:{int(self._body_state.radius)}\n"
            f"p:({int(self._body_state.position[0])}; {int(self._body_state.position[1])})\n"
            f"v:({int(self._body_state.velocity[0])}; {int(self._body_state.velocity[1])})"
        )
        self._text_item.setPlainText(info)
        
        # Подбор контрастного цвета
        bg_color = QColor(self._body_state.color)
        luminance: float = self.calculate_luminance(bg_color)
        
        if luminance > LUMA_THRESHOLD:
            self._text_item.setDefaultTextColor(Qt.GlobalColor.black)
        else:
            self._text_item.setDefaultTextColor(Qt.GlobalColor.white)
        
        # Масштабирование текста
        self._text_item.setScale(TEXT_DEFAULT_SCALE)
        text_rect = self._text_item.boundingRect()
        
        if text_rect.width() == 0 or text_rect.height() == 0:
            return

        available_size: float = self._body_state.radius * TEXT_FIT_MULTIPLIER
        scale_x: float = available_size / text_rect.width()
        scale_y: float = available_size / text_rect.height()
        
        final_scale: float = min(scale_x, scale_y)
        self._text_item.setScale(final_scale)
        
        # Центрирование
        scaled_width: float = text_rect.width() * final_scale
        scaled_height: float = text_rect.height() * final_scale
        self._text_item.setPos(-scaled_width / 2.0, -scaled_height / 2.0)

    def itemChange(self, change: QGraphicsEllipseItem.GraphicsItemChange, value: Any) -> Any:
        """
        Перехватывает изменения элемента. Просчитывает коллизии (пересечения) 
        в реальном времени при перетаскивании объекта пользователем.
        """
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange:
            target_pos: QPointF = value
            target_x: float = target_pos.x()
            target_y: float = target_pos.y()
            current_radius: float = self._body_state.radius
            
            # ОПТИМИЗАЦИЯ: Перебираем только планеты, а не все элементы сцены
            for other_planet in self._planet_list:
                if other_planet is self:
                    continue
                
                dx: float = target_x - other_planet.x()
                dy: float = target_y - other_planet.y()
                min_distance: float = current_radius + other_planet.body_state.radius
                
                # Сравнение квадратов расстояний
                if (dx * dx + dy * dy) < (min_distance * min_distance):
                    return self.pos() # Блокируем перемещение
            
            # Обновляем координаты ТОЛЬКО если коллизий нет
            # Текст здесь не перерисовываем ради производительности
            self._body_state.position = (target_x, target_y)
            
        return super().itemChange(change, value)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Обрабатывает нажатие мыши для корректного захвата объекта."""
        if event.button() == Qt.MouseButton.LeftButton:
            event.accept() 
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Вызывает коллбек редактирования при двойном клике левой кнопкой мыши."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._edit_callback(self)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
