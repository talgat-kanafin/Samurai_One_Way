import json
from pathlib import Path

TOOLS_FILE = Path(__file__).parent.parent / "data" / "tools.json"


def load_tools() -> list:
    if not TOOLS_FILE.exists():
        return []
    try:
        return json.loads(TOOLS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_tools(tools: list) -> None:
    TOOLS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOOLS_FILE.write_text(
        json.dumps(tools, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def add_tool(name: str, url: str, profile: str = "", account_label: str = "", prompt: str = "") -> dict:
    tools = load_tools()
    tool = {
        "id": __import__("uuid").uuid4().__str__(),
        "name": name,
        "url": url,
        "profile": profile,
        "account_label": account_label,
        "prompt": prompt
    }
    tools.append(tool)
    save_tools(tools)
    return tool


def delete_tool(tool_id: str) -> None:
    tools = load_tools()
    tools = [t for t in tools if t["id"] != tool_id]
    save_tools(tools)


def update_tool(tool_id: str, **kwargs) -> None:
    tools = load_tools()
    for tool in tools:
        if tool["id"] == tool_id:
            tool.update(kwargs)
    save_tools(tools)


def get_chrome_profiles() -> list:
    """Возвращает список профилей Chrome на этом ПК."""
    import os
    profiles = []
    chrome_base = Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "User Data"
    if not chrome_base.exists():
        return profiles

    for item in chrome_base.iterdir():
        if item.is_dir() and (item.name == "Default" or item.name.startswith("Profile")):
            prefs_file = item / "Preferences"
            label = item.name
            if prefs_file.exists():
                try:
                    prefs = json.loads(prefs_file.read_text(encoding="utf-8", errors="ignore"))
                    account = prefs.get("account_info", [{}])
                    if account and isinstance(account, list):
                        email = account[0].get("email", "")
                        if email:
                            label = f"{item.name} ({email})"
                except Exception:
                    pass
            profiles.append({"dir": item.name, "label": label})

    return profiles


def open_tool(url: str, profile: str = "") -> None:
    """Открывает URL в Chrome с указанным профилем."""
    import subprocess
    import os

    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
    ]

    chrome_exe = None
    for p in chrome_paths:
        if Path(p).exists():
            chrome_exe = str(p)
            break

    if not chrome_exe:
        import webbrowser
        webbrowser.open(url)
        return

    cmd = [chrome_exe]
    if profile:
        cmd += [f"--profile-directory={profile}"]
    cmd.append(url)

    subprocess.Popen(cmd)