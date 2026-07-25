import hashlib
import os
import uuid
from typing import Optional, Tuple
from core.database import create_user, get_user, user_exists


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations=260000
    ).hex()


def register_user(login: str, password: str) -> Tuple[bool, str]:
    if user_exists():
        return False, "Пользователь уже существует"
    if len(login.strip()) < 3:
        return False, "Логин должен быть не менее 3 символов"
    if len(password) < 6:
        return False, "Пароль должен быть не менее 6 символов"

    salt = os.urandom(16).hex()
    password_hash = f"{salt}:{_hash_password(password, salt)}"
    user_id = str(uuid.uuid4())

    ok = create_user(login.strip(), password_hash, user_id)
    if ok:
        return True, user_id
    return False, "Ошибка при создании пользователя"


def verify_user(login: str, password: str) -> Tuple[bool, Optional[str]]:
    row = get_user(login.strip())
    if not row:
        return False, None

    stored = row["password_hash"]
    salt, hashed = stored.split(":", 1)
    attempt = _hash_password(password, salt)

    if attempt == hashed:
        return True, row["id"]
    return False, None


def needs_registration() -> bool:
    return not user_exists()