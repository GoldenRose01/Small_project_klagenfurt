"""Visibility policy for reports."""

from collections.abc import Iterable
from .models import Report


def visible_reports(user_groups: Iterable[str], reports: list[Report]) -> list[Report]:
    """Return reports visible to a user with the given group memberships.

    Starting baseline: returns all reports without applying group filtering.
    """
    return list(reports)
