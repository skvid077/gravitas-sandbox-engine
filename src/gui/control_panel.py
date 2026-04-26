from PyQt6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel, QSlider, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from config.constants import GRAVITY_CONSTANT

class ControlPanel(QDockWidget):
    # Сигналы для передачи изменений в главное ядро
    gravity_changed = pyqtSignal(float)
    time_scale_changed = pyqtSignal(float)
    clear_scene_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Панель управления", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable | QDockWidget.DockWidgetFeature.DockWidgetMovable)

        container = QWidget()
        layout = QVBoxLayout()

        # Слайдер гравитации (от 0.0x до 5.0x от базовой)
        self.lbl_g = QLabel(f"Гравитация: 1.0x")
        self.slider_g = QSlider(Qt.Orientation.Horizontal)
        self.slider_g.setRange(0, 50)  
        self.slider_g.setValue(10)     
        self.slider_g.valueChanged.connect(self._on_g_change)

        # Слайдер скорости симуляции (от 0.1x до 3.0x)
        self.lbl_time = QLabel("Скорость времени: 1.0x")
        self.slider_time = QSlider(Qt.Orientation.Horizontal)
        self.slider_time.setRange(1, 30) 
        self.slider_time.setValue(10)    
        self.slider_time.valueChanged.connect(self._on_time_change)

        # Кнопка очистки
        self.btn_clear = QPushButton("Очистить космос")
        self.btn_clear.clicked.connect(self.clear_scene_requested.emit)

        layout.addWidget(self.lbl_g)
        layout.addWidget(self.slider_g)
        layout.addSpacing(20)
        layout.addWidget(self.lbl_time)
        layout.addWidget(self.slider_time)
        layout.addSpacing(20)
        layout.addWidget(self.btn_clear)
        layout.addStretch()

        container.setLayout(layout)
        self.setWidget(container)

    def _on_g_change(self, val: int) -> None:
        multiplier = val / 10.0
        self.lbl_g.setText(f"Гравитация: {multiplier:.1f}x")
        # Отправляем новое абсолютное значение G
        self.gravity_changed.emit(GRAVITY_CONSTANT * multiplier)

    def _on_time_change(self, val: int) -> None:
        multiplier = val / 10.0
        self.lbl_time.setText(f"Скорость времени: {multiplier:.1f}x")
        self.time_scale_changed.emit(multiplier)
