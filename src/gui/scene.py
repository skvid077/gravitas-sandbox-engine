import random
from typing import Optional, List

from PyQt6.QtCore import QPointF, Qt, QRectF, QObject
from PyQt6.QtGui import QBrush, QColor, QPainter
from PyQt6.QtWidgets import QGraphicsScene

from config.constants import *


class SpaceScene(QGraphicsScene):
    """
    Сцена графического движка для отображения бесконечного космоса.

    Реализует процедурную генерацию звездного неба на основе чанков.
    Использует оптимизации Level of Detail (LOD) и отсечение невидимых 
    областей (Frustum Culling) для поддержания высокого FPS.
    """

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """
        Инициализирует графическую сцену и кэширует тяжелые объекты.

        Args:
            parent (Optional[QObject]): Родительский объект Qt.
        """
        super().__init__(parent)
        self.setBackgroundBrush(QColor(SPACE_COLOR))
        
        # ОПТИМИЗАЦИЯ: Парсинг HEX-строк в объекты QColor занимает время.
        # Делаем это один раз при инициализации сцены, чтобы не нагружать 
        # процессор в методе drawBackground (который вызывается каждый кадр).
        self._cached_star_colors: List[QColor] = [QColor(hex_code) for hex_code in STAR_PALETTE]

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """
        Переопределенный метод отрисовки фона. 
        Рисует процедурные звезды только в видимой области экрана.

        Args:
            painter (QPainter): Инструмент для отрисовки примитивов.
            rect (QRectF): Видимая прямоугольная область камеры (Viewport).
        """
        super().drawBackground(painter, rect)
        
        # 1. Level of Detail (LOD): Не рисуем звезды, если камера отдалена слишком сильно
        if max(rect.width(), rect.height()) > STARS_LOD_THRESHOLD:
            return

        # 2. Вычисление индексов видимых чанков (Frustum Culling)
        x_start: int = int(rect.left() // CHUNK_SIZE)
        x_end: int = int(rect.right() // CHUNK_SIZE)
        y_start: int = int(rect.top() // CHUNK_SIZE)
        y_end: int = int(rect.bottom() // CHUNK_SIZE)

        # 3. Защита от зависаний при экстремальном отдалении камеры
        if (x_end - x_start) * (y_end - y_start) > MAX_VISIBLE_CHUNKS:
            return

        # Отключаем обводку звезд для прироста скорости рендера
        painter.setPen(Qt.PenStyle.NoPen)

        # 4. Процедурная генерация
        for cx in range(x_start, x_end + 1):
            for cy in range(y_start, y_end + 1):
                # Детерминированный сид: звезды в одном чанке всегда генерируются одинаково
                chunk_seed: int = (cx * HASH_SEED_X) ^ (cy * HASH_SEED_Y)
                rng = random.Random(chunk_seed)

                num_stars: int = rng.randint(MIN_STARS_PER_CHUNK, MAX_STARS_PER_CHUNK)

                for _ in range(num_stars):
                    px: float = rng.uniform(cx * CHUNK_SIZE, (cx + 1) * CHUNK_SIZE)
                    py: float = rng.uniform(cy * CHUNK_SIZE, (cy + 1) * CHUNK_SIZE)

                    # Берем готовый QColor из кэша и клонируем его для изменения альфа-канала
                    base_color: QColor = rng.choice(self._cached_star_colors)
                    color = QColor(base_color) 
                    
                    alpha: int = int(rng.uniform(OPACITY_MIN, OPACITY_MAX) * COLOR_ALPHA_MAX)
                    color.setAlpha(alpha)

                    size: float = rng.uniform(SIZE_STAR_MIN, SIZE_STAR_MAX)
                    half_size: float = size / 2.0  # Микрооптимизация: делим только один раз

                    painter.setBrush(QBrush(color))
                    painter.drawEllipse(QPointF(px, py), half_size, half_size)
