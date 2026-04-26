import sys
import os
import traceback
from typing import Optional, Type
from types import TracebackType

from PyQt6.QtWidgets import QApplication

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gui.start_screen import StartScreen

def global_exception_handler(
    exc_type: Type[BaseException], 
    exc_value: BaseException, 
    exc_traceback: Optional[TracebackType]
) -> None:
    """
    Глобальный обработчик необработанных исключений.
    Позволяет записать лог критической ошибки перед завершением приложения.
    """
    print("=== КРИТИЧЕСКАЯ ОШИБКА ===", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
    print("==========================", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    """
    Точка входа в приложение Gravitas Sandbox.
    Инициализирует QApplication, настраивает стиль и запускает стартовое окно.
    """
    # Перехват всех ошибок, которые не были обработаны в блоках try-except
    sys.excepthook = global_exception_handler

    app: QApplication = QApplication(sys.argv)
    
    # Fusion — кроссплатформенный стиль, который выглядит одинаково на всех ОС
    app.setStyle("Fusion")
    
    start_window: StartScreen = StartScreen()
    start_window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
