import os
import json
from datetime import datetime
from pathlib import Path
from config import PROJECTS_FOLDER


def create_project_folder(project_name: str) -> Path:
    """Создаёт папку проекта и возвращает путь к ней."""
    safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')
    folder = PROJECTS_FOLDER / safe_name
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_project_log_path(project_name: str) -> Path:
    """Возвращает путь к лог-файлу проекта."""
    folder = create_project_folder(project_name)
    safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')
    return folder / f"{safe_name}.txt"


def log_to_project(project_name: str, section: str, content: str) -> None:
    """Добавляет запись в лог-файл проекта."""
    log_path = get_project_log_path(project_name)
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")

    entry = f"""
{'='*60}
[{section}] — {timestamp}
{'='*60}
{content}

"""
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(entry)


def copy_file_to_project(project_name: str, source_path: str) -> str:
    """Копирует файл в папку проекта. Возвращает новый путь."""
    import shutil
    folder = create_project_folder(project_name)
    filename = Path(source_path).name
    dest = folder / filename

    # Если файл с таким именем уже есть — добавляем timestamp
    if dest.exists():
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = folder / f"{stem}_{timestamp}{suffix}"

    shutil.copy2(source_path, dest)
    return str(dest)


def get_project_files(project_name: str) -> list:
    """Возвращает список файлов в папке проекта."""
    folder = create_project_folder(project_name)
    files = []
    for f in folder.iterdir():
        if f.is_file() and not f.name.endswith('.txt'):
            files.append({
                "name": f.name,
                "path": str(f),
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%d.%m.%Y")
            })
    return files


def save_project_meta(project_name: str, meta: dict) -> None:
    """Сохраняет метаданные проекта в JSON."""
    folder = create_project_folder(project_name)
    meta_path = folder / "meta.json"

    existing = {}
    if meta_path.exists():
        try:
            existing = json.loads(meta_path.read_text(encoding='utf-8'))
        except Exception:
            pass

    existing.update(meta)
    existing["last_updated"] = datetime.now().isoformat()
    meta_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding='utf-8')


def load_project_meta(project_name: str) -> dict:
    """Загружает метаданные проекта."""
    folder = create_project_folder(project_name)
    meta_path = folder / "meta.json"
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding='utf-8'))
    except Exception:
        return {}