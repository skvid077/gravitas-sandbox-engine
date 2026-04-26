"""Стили (QSS) интерфейса."""
from PyQt6.QtGui import QColor

DIMMER_COLOR: QColor = QColor(0, 0, 0, 150)

STATUS_STYLE_PAUSED: str = "color: orange; font-weight: bold; background: rgba(0,0,0,100); padding: 5px;"
STATUS_STYLE_RUNNING: str = "color: white; font-weight: bold; background: rgba(0,0,0,100); padding: 5px;"

MENU_STYLE_SHEET: str = """
    #PauseMenuPanel {
        background-color: rgba(25, 25, 35, 230);
        border: 1px solid rgba(255, 255, 255, 30);
        border-radius: 20px;
    }
"""

MANAGER_STYLE_SHEET: str = """
    QDialog { background-color: rgba(20, 22, 30, 240); border: 1px solid rgba(255, 255, 255, 20); border-radius: 12px; }
    QTableWidget { background-color: transparent; color: white; gridline-color: rgba(255, 255, 255, 10); font-size: 13px; border: none; }
    QHeaderView::section { background-color: rgba(40, 45, 60, 200); color: #bbb; padding: 6px; font-weight: bold; }
    QPushButton#DeleteBtn { background-color: rgba(220, 50, 50, 30); color: #ff8888; border: 1px solid rgba(220, 50, 50, 80); border-radius: 6px; }
    QPushButton#CloseBtn { background-color: rgba(255, 255, 255, 10); border: 1px solid rgba(255, 255, 255, 30); border-radius: 8px; color: white; }
"""

START_BTN_STYLE_SHEET: str = """
    QPushButton { background-color: rgba(0, 0, 0, 100); color: white; border: 1px solid rgba(255, 255, 255, 100); border-radius: 5px; font-size: 14px; }
    QPushButton:hover { background-color: rgba(255, 255, 255, 40); border: 1px solid white; }
"""

COORD_LABEL_STYLE: str = "color: #00FF00; background-color: rgba(0, 0, 0, 150); padding: 4px; border-radius: 4px;"
FPS_LABEL_STYLE: str = "color: #FFFF00; background-color: rgba(0, 0, 0, 150); padding: 4px; border-radius: 4px; font-weight: bold;"

STYLE_BTN_MENU: str = """
    QPushButton { background-color: rgba(45, 50, 65, 180); color: #E0E0E0; border: 1px solid rgba(120, 130, 160, 80); border-radius: 8px; padding: 8px 15px; }
    QPushButton:hover { background-color: rgba(65, 75, 95, 220); border: 1px solid rgba(150, 160, 200, 150); color: #FFFFFF; }
"""

STYLE_BTN_MENU_CONTINUE: str = """
    QPushButton { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2b5876, stop:1 #4e4376); color: #FFFFFF; border-radius: 8px; padding: 8px 15px; font-weight: bold; }
    QPushButton:hover { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b6886, stop:1 #5e5386); }
"""
