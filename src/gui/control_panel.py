from typing import Any, cast

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDockWidget, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget

from config.constants import (
    GRAVITY_CONSTANT,
    LAYOUT_SPACING,
    PANEL_TITLE,
    SLIDER_DIVIDER,
    SLIDER_G_DEFAULT,
    SLIDER_G_MAX,
    SLIDER_G_MIN,
    SLIDER_TIME_DEFAULT,
    SLIDER_TIME_MAX,
    SLIDER_TIME_MIN,
    TEXT_BTN_CLEAR,
    TEXT_GRAVITY_LBL,
    TEXT_TIME_LBL,
    TEXT_TIMELINE_FORMAT,
)


class ControlPanel(QDockWidget):
    gravity_changed = pyqtSignal(float)
    time_scale_changed = pyqtSignal(float)
    clear_scene_requested = pyqtSignal()
    timeline_changed = pyqtSignal(int)
    timeline_pressed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(PANEL_TITLE, parent)
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )

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
        cast(Any, self.slider_g.valueChanged).connect(self._on_g_change)

        default_time_mult = SLIDER_TIME_DEFAULT / SLIDER_DIVIDER
        self.lbl_time = QLabel(TEXT_TIME_LBL.format(default_time_mult))
        self.slider_time = QSlider(Qt.Orientation.Horizontal)
        self.slider_time.setRange(SLIDER_TIME_MIN, SLIDER_TIME_MAX)
        self.slider_time.setValue(SLIDER_TIME_DEFAULT)
        cast(Any, self.slider_time.valueChanged).connect(self._on_time_change)
        self.lbl_timeline = QLabel(TEXT_TIMELINE_FORMAT.format(0, 0))
        self.slider_timeline = QSlider(Qt.Orientation.Horizontal)
        self.slider_timeline.setRange(0, 0)
        self.slider_timeline.setValue(0)

        cast(Any, self.slider_timeline.sliderPressed).connect(cast(Any, self.timeline_pressed).emit)
        cast(Any, self.slider_timeline.valueChanged).connect(self._on_timeline_change)

        self.btn_clear = QPushButton(TEXT_BTN_CLEAR)
        cast(Any, self.btn_clear.clicked).connect(cast(Any, self.clear_scene_requested).emit)

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
        cast(Any, self.gravity_changed).emit(GRAVITY_CONSTANT * multiplier)

    def _on_time_change(self, val: int) -> None:
        multiplier = val / SLIDER_DIVIDER
        self.lbl_time.setText(TEXT_TIME_LBL.format(multiplier))
        cast(Any, self.time_scale_changed).emit(multiplier)

    def _on_timeline_change(self, val: int) -> None:
        max_val = self.slider_timeline.maximum()
        self.lbl_timeline.setText(TEXT_TIMELINE_FORMAT.format(val, max_val))
        cast(Any, self.timeline_changed).emit(val)

    def update_timeline_range(self, max_frames: int, current_frame: int) -> None:
        self.slider_timeline.blockSignals(True)
        self.slider_timeline.setRange(0, max_frames)
        self.slider_timeline.setValue(current_frame)
        self.lbl_timeline.setText(TEXT_TIMELINE_FORMAT.format(current_frame, max_frames))
        self.slider_timeline.blockSignals(False)
