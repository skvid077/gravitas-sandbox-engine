import os
import sys
import traceback
from types import TracebackType

from PyQt6.QtWidgets import QApplication


class Application:
    @staticmethod
    def handle_exception(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        print("=== КРИТИЧЕСКАЯ ОШИБКА ===", file=sys.stderr)
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        print("==========================", file=sys.stderr)
        sys.exit(1)

    def run(self) -> int:
        source_path = os.path.join(os.path.dirname(__file__), "src")
        sys.path.insert(0, source_path)
        from gui.start_screen import StartScreen

        sys.excepthook = self.handle_exception
        app = QApplication(sys.argv)
        app.setStyle("Fusion")

        start_window = StartScreen()
        start_window.show()
        return app.exec()


if __name__ == "__main__":
    sys.exit(Application().run())
