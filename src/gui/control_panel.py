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
    gravity_changed = pyqtSignal(float)
    time_scale_changed = pyqtSignal(float)
    clear_scene_requested = pyqtSignal()
    
    # Сигналы машины времени
    timeline_changed = pyqtSignal(int)
    timeline_pressed = pyqtSignal()
    timeline_released = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(PANEL_TITLE, parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable | QDockWidget.DockWidgetFeature.DockWidgetMovable)

        self.lbl_g: QLabel
        self.slider_g: QSlider
        self.lbl_time: QLabel
        self.slider_time: QSlider
        self.lbl_timeline: QLabel
        self.slider_timeline: QSlider
        self.btn_clear: QPushButton

        self._init_ui()

    def _init_ui(self) -> None:
        container = QWidget()
        layout = QVBoxLayout()

        default_g_mult = SLIDER_G_DEFAULT / SLIDER_DIVIDER
        self.lbl_g = QLabel(TEXT_GRAVITY_LBL.format(default_g_mult))
        self.slider_g = QSlider(Qt.Orientation.Horizontal)
        self.slider_g.setRange(SLIDER_G_MIN, SLIDER_G_MAX)  
        self.slider_g.setValue(SLIDER_G_DEFAULT)     
        self.slider_g.valueChanged.connect(self._on_g_change)

        default_time_mult = SLIDER_TIME_DEFAULT / SLIDER_DIVIDER
        self.lbl_time = QLabel(TEXT_TIME_LBL.format(default_time_mult))
        self.slider_time = QSlider(Qt.Orientation.Horizontal)
        self.slider_time.setRange(SLIDER_TIME_MIN, SLIDER_TIME_MAX) 
        self.slider_time.setValue(SLIDER_TIME_DEFAULT)    
        self.slider_time.valueChanged.connect(self._on_time_change)

        # --- Шкала времени ---
        self.lbl_timeline = QLabel("Машина времени: 0 / 0")
        self.slider_timeline = QSlider(Qt.Orientation.Horizontal)
        self.slider_timeline.setRange(0, 0)
        self.slider_timeline.setValue(0)
        
        self.slider_timeline.sliderPressed.connect(self.timeline_pressed.emit)
        self.slider_timeline.sliderReleased.connect(self.timeline_released.emit)
        self.slider_timeline.valueChanged.connect(self._on_timeline_change)

        self.btn_clear = QPushButton(TEXT_BTN_CLEAR)
        self.btn_clear.clicked.connect(self.clear_scene_requested.emit)

        layout.addWidget(self.lbl_g)
        layout.addWidget(self.slider_g)
        layout.addSpacing(LAYOUT_SPACING)
        layout.addWidget(self.lbl_time)
        layout.addWidget(self.slider_time)
        layout.addSpacing(LAYOUT_SPACING)
        
        layout.addWidget(self.lbl_timeline)
        layout.addWidget(self.slider_timeline)
        layout.addSpacing(LAYOUT_SPACING)
        
        layout.addWidget(self.btn_clear)
        layout.addStretch()

        container.setLayout(layout)
        self.setWidget(container)

    def _on_g_change(self, val: int) -> None:
        multiplier = val / SLIDER_DIVIDER
        self.lbl_g.setText(TEXT_GRAVITY_LBL.format(multiplier))
        self.gravity_changed.emit(GRAVITY_CONSTANT * multiplier)

    def _on_time_change(self, val: int) -> None:
        multiplier = val / SLIDER_DIVIDER
        self.lbl_time.setText(TEXT_TIME_LBL.format(multiplier))
        self.time_scale_changed.emit(multiplier)

    def _on_timeline_change(self, val: int) -> None:
        max_val = self.slider_timeline.maximum()
        self.lbl_timeline.setText(f"Машина времени: {val} / {max_val}")
        self.timeline_changed.emit(val)

    def update_timeline_range(self, max_frames: int, current_frame: int) -> None:
        """Тихо обновляет границы и позицию ползунка, пока симуляция идет сама."""
        self.slider_timeline.blockSignals(True)
        self.slider_timeline.setRange(0, max_frames)
        self.slider_timeline.setValue(current_frame)
        self.lbl_timeline.setText(f"Машина времени: {current_frame} / {max_frames}")
        self.slider_timeline.blockSignals(False)
