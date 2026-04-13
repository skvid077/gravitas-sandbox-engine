from typing import Callable, Any, List
from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
from PyQt6.QtGui import QBrush, QColor, QPen
from PyQt6.QtCore import Qt, QPointF

from config.constants import *
from config.schemas import BodyState


class PlanetItem(QGraphicsEllipseItem):
    """
    Графическое представление планеты (физического тела) на сцене симуляции.

    Класс отвечает за отрисовку, адаптивное масштабирование текста,
    подбор контрастного цвета надписи и обработку коллизий в реальном времени.
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
            body_state (BodyState): Pydantic-модель с физическими параметрами.
            edit_callback (Callable): Функция обратного вызова для редактирования (нажатие/двойной клик).
            planet_list_ref (List[PlanetItem]): Ссылка на список всех планет для просчета коллизий.
        """
        super().__init__()
        # Инкапсуляция внутренних переменных (PEP8: single underscore)
        self._body_state: BodyState = body_state
        self._edit_callback: Callable[['PlanetItem'], None] = edit_callback
        self._planet_list: List['PlanetItem'] = planet_list_ref
        
        self._text_item: QGraphicsTextItem = QGraphicsTextItem(self)
        self._text_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        
        self.setZValue(PLANET_Z_VALUE)
        self.setFlags(
            QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable | 
            QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable | 
            QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.update_visuals()

    @property
    def body_state(self) -> BodyState:
        """
        BodyState: Геттер для получения текущего физического состояния планеты.
        Демонстрирует применение property для инкапсуляции.
        """
        return self._body_state

    @body_state.setter
    def body_state(self, new_state: BodyState) -> None:
        """Сеттер для обновления состояния с автоматической перерисовкой."""
        self._body_state = new_state
        self.update_visuals()

    @staticmethod
    def calculate_luminance(color: QColor) -> float:
        """
        Вычисляет воспринимаемую яркость цвета по формуле YIQ.
        Вынесено в staticmethod, так как логика независима от состояния экземпляра.

        Args:
            color (QColor): Цвет для анализа.

        Returns:
            float: Значение яркости от 0.0 до 255.0.
        """
        return (
            color.red() * LUMA_R_WEIGHT + 
            color.green() * LUMA_G_WEIGHT + 
            color.blue() * LUMA_B_WEIGHT
        ) / LUMA_DENOMINATOR

    def update_visuals(self) -> None:
        """Обновляет геометрию, позицию и заливку графического элемента."""
        radius: float = self._body_state.radius
        self.setRect(-radius, -radius, radius * 2.0, radius * 2.0)
        self.setPos(self._body_state.position[0], self._body_state.position[1])
        
        self.setBrush(QBrush(QColor(self._body_state.color)))
        self.setPen(QPen(Qt.PenStyle.NoPen))
        
        self._update_label_appearance()

    def _update_label_appearance(self) -> None:
        """
        Внутренний метод: Адаптирует цвет и размер текста, 
        чтобы он контрастировал с фоном и помещался внутри планеты.
        """
        background_color = QColor(self._body_state.color)
        luminance: float = self.calculate_luminance(background_color)
        
        text_color = Qt.GlobalColor.black if luminance > LUMA_THRESHOLD else Qt.GlobalColor.white
        self._text_item.setDefaultTextColor(text_color)
        
        self._text_item.setPlainText(f"{self._body_state.name}\nM:{int(self._body_state.mass)}")
        self._text_item.setScale(TEXT_DEFAULT_SCALE)
        
        text_rect = self._text_item.boundingRect()
        
        # Краевой случай: защита от деления на ноль при пустом тексте
        if text_rect.width() == 0 or text_rect.height() == 0:
            return
            
        available_space: float = self._body_state.radius * TEXT_FIT_MULTIPLIER
        final_scale: float = min(
            available_space / text_rect.width(), 
            available_space / text_rect.height()
        )
        
        self._text_item.setScale(final_scale)
        self._text_item.setPos(
            -text_rect.width() * final_scale / 2.0, 
            -text_rect.height() * final_scale / 2.0
        )

    def itemChange(self, change: QGraphicsEllipseItem.GraphicsItemChange, value: Any) -> Any:
        """
        Перехватывает изменения состояния элемента. 
        Обеспечивает физику твердых тел (предотвращение наложений) при перетаскивании.

        Args:
            change (GraphicsItemChange): Тип происходящего изменения.
            value (Any): Новое значение (например, координаты QPointF).

        Returns:
            Any: Разрешенное значение для применения движком Qt.
        """
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange:
            target_pos: QPointF = value
            target_x: float = target_pos.x()
            target_y: float = target_pos.y()
            current_radius: float = self._body_state.radius
            
            for other_planet in self._planet_list:
                if other_planet is self: 
                    continue
                    
                dx: float = target_x - other_planet.x()
                dy: float = target_y - other_planet.y()
                min_distance: float = current_radius + other_planet.body_state.radius
                
                # Оптимизация: умножение работает быстрее возведения в степень (dx**2)
                if (dx * dx + dy * dy) < (min_distance * min_distance):
                    return self.pos()
                    
            # Обновляем состояние модели при успешном перемещении
            self._body_state.position = (target_x, target_y)
            
        return super().itemChange(change, value)
