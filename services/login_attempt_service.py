"""Controle persistente de tentativas de login por conta."""
import hashlib


LOGIN_WINDOW_SECONDS = 300
LOGIN_MAX_ATTEMPTS = 8


def account_attempt_key(identifier, user_id=None):
    """Gera chave estável por conta sem armazenar o identificador em texto puro."""
    if user_id is not None:
        return f"account:{int(user_id)}"
    normalized = (identifier or "").strip().lower()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"unknown:{digest}"


def login_is_blocked(connection, account_key):
    """Verifica se a conta atingiu o limite dentro da janela móvel de cinco minutos."""
    row = connection.execute(
        "SELECT attempts, window_started_at FROM login_attempts WHERE account_key = ?",
        (account_key,),
    ).fetchone()
    if not row:
        return False
    expired = connection.execute(
        "SELECT (? < UTC_TIMESTAMP() - INTERVAL 5 MINUTE) AS expired",
        (row["window_started_at"],),
    ).fetchone()
    if expired and expired["expired"]:
        connection.execute("DELETE FROM login_attempts WHERE account_key = ?", (account_key,))
        connection.commit()
        return False
    return int(row["attempts"]) >= LOGIN_MAX_ATTEMPTS


def register_failed_login(connection, account_key):
    """Registra falha e reinicia a janela quando os cinco minutos expirarem."""
    try:
        connection.execute("START TRANSACTION")
        connection.execute(
            """INSERT INTO login_attempts (account_key, attempts, window_started_at)
               VALUES (?, 1, UTC_TIMESTAMP())
               ON DUPLICATE KEY UPDATE
                 attempts = IF(window_started_at < UTC_TIMESTAMP() - INTERVAL 5 MINUTE, 1, attempts + 1),
                 window_started_at = IF(window_started_at < UTC_TIMESTAMP() - INTERVAL 5 MINUTE,
                                        UTC_TIMESTAMP(), window_started_at)""",
            (account_key,),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def clear_login_attempts(connection, account_key):
    """Remove o contador após autenticação bem-sucedida."""
    connection.execute("DELETE FROM login_attempts WHERE account_key = ?", (account_key,))
    connection.commit()
