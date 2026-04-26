from typing import Optional

from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QLabel, QSlider, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal

from config.constants import (
    GRAVITY_CONSTANT,
    PANEL_TITLE,
    TEXT_GRAVITY_LBL,
    TEXT_TIME_LBL,
    TEXT_BTN_CLEAR,
    SLIDER_G_MIN,
    SLIDER_G_MAX,
    SLIDER_G_DEFAULT,
    SLIDER_TIME_MIN,
    SLIDER_TIME_MAX,
    SLIDER_TIME_DEFAULT,
    SLIDER_DIVIDER,
    LAYOUT_SPACING
)


class ControlPanel(QDockWidget):
    """
    Боковая панель управления симуляцией.
    Позволяет динамически изменять гравитационную постоянную,
    скорость течения времени и экстренно очищать сцену.
    """
    
    # Сигналы для передачи изменений в главное ядро
    gravity_changed = pyqtSignal(float)
    time_scale_changed = pyqtSignal(float)
    clear_scene_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Инициализирует панель управления.

        Args:
            parent (Optional[QWidget], optional): Родительское окно (MainWindow). По умолчанию None.
        """
        super().__init__(PANEL_TITLE, parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable | QDockWidget.DockWidgetFeature.DockWidgetMovable)

        # Строгая типизация UI-элементов для mypy
        self.lbl_g: QLabel
        self.slider_g: QSlider
        self.lbl_time: QLabel
        self.slider_time: QSlider
        self.btn_clear: QPushButton

        self._init_ui()

    def _init_ui(self) -> None:
        """Создает и настраивает внутренние виджеты и компоновку панели."""
        container = QWidget()
        layout = QVBoxLayout()

        # --- Слайдер гравитации ---
        default_g_mult = SLIDER_G_DEFAULT / SLIDER_DIVIDER
        self.lbl_g = QLabel(TEXT_GRAVITY_LBL.format(default_g_mult))
        
        self.slider_g = QSlider(Qt.Orientation.Horizontal)
        self.slider_g.setRange(SLIDER_G_MIN, SLIDER_G_MAX)  
        self.slider_g.setValue(SLIDER_G_DEFAULT)     
        self.slider_g.valueChanged.connect(self._on_g_change)

        # --- Слайдер скорости симуляции ---
        default_time_mult = SLIDER_TIME_DEFAULT / SLIDER_DIVIDER
        self.lbl_time = QLabel(TEXT_TIME_LBL.format(default_time_mult))
        
        self.slider_time = QSlider(Qt.Orientation.Horizontal)
        self.slider_time.setRange(SLIDER_TIME_MIN, SLIDER_TIME_MAX) 
        self.slider_time.setValue(SLIDER_TIME_DEFAULT)    
        self.slider_time.valueChanged.connect(self._on_time_change)

        # --- Кнопка очистки ---
        self.btn_clear = QPushButton(TEXT_BTN_CLEAR)
        self.btn_clear.clicked.connect(self.clear_scene_requested.emit)

        # --- Сборка компоновки ---
        layout.addWidget(self.lbl_g)
        layout.addWidget(self.slider_g)
        layout.addSpacing(LAYOUT_SPACING)
        layout.addWidget(self.lbl_time)
        layout.addWidget(self.slider_time)
        layout.addSpacing(LAYOUT_SPACING)
        layout.addWidget(self.btn_clear)
        layout.addStretch()

        container.setLayout(layout)
        self.setWidget(container)

    def _on_g_change(self, val: int) -> None:
        """
        Слот изменения гравитации. Форматирует текст лейбла и отправляет сигнал.
        
        Args:
            val (int): Текущее (сырое) значение слайдера.
        """
        multiplier = val / SLIDER_DIVIDER
        self.lbl_g.setText(TEXT_GRAVITY_LBL.format(multiplier))
        
        # Отправляем новое абсолютное значение G
        self.gravity_changed.emit(GRAVITY_CONSTANT * multiplier)

    def _on_time_change(self, val: int) -> None:
        """
        Слот изменения скорости времени. Форматирует текст лейбла и отправляет сигнал.
        
        Args:
            val (int): Текущее (сырое) значение слайдера.
        """
        multiplier = val / SLIDER_DIVIDER
        self.lbl_time.setText(TEXT_TIME_LBL.format(multiplier))
        self.time_scale_changed.emit(multiplier)
