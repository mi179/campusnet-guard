"""Account-level authentication helpers shared by CLI, menu, and GUI flows."""

from __future__ import annotations

from cyber_lobster.config import AccountConfig


def password_available(account: AccountConfig) -> bool:
    return bool(account.password)


def credentials_from_account(account: AccountConfig):
    """Build portal credentials from an account.

    The import stays lazy so tests and lightweight commands can mock or avoid
    the network module until authentication is actually requested.
    """
    from cyber_lobster.network_login import PortalCredentials

    return PortalCredentials(
        user_id=account.user_id,
        password=account.password,
        service=account.service,
        query_string=account.query_string,
    )


def login_account(
    account: AccountConfig,
    *,
    max_session_attempts: int = 1,
    request_retries: int = 2,
):
    from cyber_lobster.network_login import login_with_session_retry

    return login_with_session_retry(
        credentials_from_account(account),
        host=account.host,
        max_session_attempts=max_session_attempts,
        request_retries=request_retries,
    )


def login_plain(
    user_id: str,
    password: str,
    service: str,
    host: str,
    *,
    max_session_attempts: int = 1,
    request_retries: int = 2,
):
    from cyber_lobster.network_login import PortalCredentials, login_with_session_retry

    creds = PortalCredentials(user_id=user_id, password=password, service=service)
    return login_with_session_retry(
        creds,
        host=host,
        max_session_attempts=max_session_attempts,
        request_retries=request_retries,
    )


def logout_host(host: str):
    from cyber_lobster.network_login import logout

    return logout(host=host)


def parse_response(body: str) -> dict:
    from cyber_lobster.network_login import parse_login_response

    return parse_login_response(body)


def response_message(body: str) -> str:
    resp = parse_response(body)
    return str(resp.get("message", "") or resp.get("result", ""))


def error_text(result, limit: int = 100) -> str:
    return str(result.error or result.body[:limit]).replace("\n", " ")
