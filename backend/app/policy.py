"""Единая точка проверки прав: любой вызов инструмента проходит через assert_allowed."""

PERMISSIONS: dict[str, set[str]] = {
    "intern": {"create_absence"},
    "mentor": {"create_absence", "view_team_progress"},
}


class PermissionDenied(Exception):
    pass


def is_allowed(role: str, tool: str) -> bool:
    return tool in PERMISSIONS.get(role, set())


def assert_allowed(role: str, tool: str) -> None:
    if not is_allowed(role, tool):
        raise PermissionDenied(f"Роль «{role}» не может выполнить «{tool}»")
