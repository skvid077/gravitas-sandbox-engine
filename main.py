import sys
import os
import traceback
from typing import Type

from PyQt6.QtWidgets import QApplication

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gui.start_screen import StartScreen

def global_exception_handler(exc_type: Type[BaseException], exc_value: BaseException, exc_traceback: getattr) -> None:
    """
    Глобальный обработчик неперехваченных исключений.
    Предотвращает "тихое" падение Qt-приложения, выводя полный стек вызовов в консоль.
    Особенно полезно для отладки слотов и сигналов.
    """
    print("=== КРИТИЧЕСКАЯ ОШИБКА ===", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
    print("==========================", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    """
    Точка входа в приложение Infinite Chunk Engine.
    Инициализирует QApplication, применяет системный стиль и запускает стартовое окно.
    """
    # Перехват непредвиденных ошибок (защита от краевых случаев)
    sys.excepthook = global_exception_handler

    # Создание основного объекта приложения
    app: QApplication = QApplication(sys.argv)
    
    # Установка кроссплатформенного стиля "Fusion" 
    # Гарантирует одинаково красивое отображение UI на Linux, Windows и macOS
    app.setStyle("Fusion")
    
    # Инициализация и показ меню
    start_window: StartScreen = StartScreen()
    start_window.show()
    
    # Запуск главного цикла обработки событий (Event Loop)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
