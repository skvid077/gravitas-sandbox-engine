import sys
import os
import traceback
from typing import Type

from PyQt6.QtWidgets import QApplication

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gui.start_screen import StartScreen

def global_exception_handler(exc_type: Type[BaseException], exc_value: BaseException, exc_traceback: getattr) -> None:
    print("=== КРИТИЧЕСКАЯ ОШИБКА ===", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
    print("==========================", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    sys.excepthook = global_exception_handler

    app: QApplication = QApplication(sys.argv)
    
    app.setStyle("Fusion")
    
    start_window: StartScreen = StartScreen()
    start_window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
