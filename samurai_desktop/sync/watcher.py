import json
import os
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import SYNC_FOLDER
from core.database import save_idea_entry
from core.models import IdeaEntry, ProjectType, EntryColor


THEME_MAP = {
    "Идея: прога":        ProjectType.SOFTWARE,
    "Идея: производство": ProjectType.PRODUCTION,
    "Исследование":       ProjectType.RESEARCH,
}


class IncomingHandler(FileSystemEventHandler):
    def __init__(self, on_new_entry=None):
        super().__init__()
        self.on_new_entry = on_new_entry  # callback для обновления UI

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() == ".json":
            self._process_file(path)

    def _process_file(self, path: Path):
        try:
            # Небольшая пауза чтобы файл успел записаться полностью
            import time
            time.sleep(0.3)

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            theme_str = data.get("theme", "")
            description = data.get("description", "")

            if not theme_str or not description:
                print(f"[watcher] Пропуск {path.name}: нет темы или описания")
                return

            project_type = THEME_MAP.get(theme_str)
            if not project_type:
                print(f"[watcher] Неизвестная тема: {theme_str}")
                return

            entry = IdeaEntry(
                project_id=None,
                theme=project_type,
                description=description,
                color=EntryColor.RED,
                phase=0,
            )
            save_idea_entry(entry)
            print(f"[watcher] Сохранена запись: {theme_str}")

            # Перемещаем в архив
            archive = SYNC_FOLDER / "archive"
            archive.mkdir(exist_ok=True)
            path.rename(archive / path.name)

            # Уведомляем UI
            if self.on_new_entry:
                self.on_new_entry(entry)

        except Exception as e:
            print(f"[watcher] Ошибка обработки {path}: {e}")


class SyncWatcher:
    def __init__(self, on_new_entry=None):
        self.observer = Observer()
        self.handler = IncomingHandler(on_new_entry=on_new_entry)

    def start(self):
        SYNC_FOLDER.mkdir(parents=True, exist_ok=True)
        self.observer.schedule(self.handler, str(SYNC_FOLDER), recursive=False)
        self.observer.start()
        print(f"[watcher] Слежу за папкой: {SYNC_FOLDER}")

    def stop(self):
        self.observer.stop()
        self.observer.join()