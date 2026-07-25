import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from core.database import init_db
from ui.auth_window import AuthWindow


def main():
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("Самурай")
    app.setStyle("Fusion")

    window = AuthWindow()
    window.show()

    # Запускаем слежение за папкой синхронизации
    from sync.watcher import SyncWatcher
    watcher = SyncWatcher()
    watcher.start()

    exit_code = app.exec()
    watcher.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()