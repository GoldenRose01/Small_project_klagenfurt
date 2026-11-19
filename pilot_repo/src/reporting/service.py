"""Public entry point for listing visible reports for a user."""

from .models import Report, User
from .policy import visible_reports


def list_user_reports(user: User, reports: list[Report]) -> list[Report]:
    """Return the reports visible to `user` in their original order."""
    return visible_reports(user.get("groups", []), reports)
