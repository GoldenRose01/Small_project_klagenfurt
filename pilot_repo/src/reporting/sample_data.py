"""Synthetic sample data illustrating report and user structures."""

from .models import Report, User

SAMPLE_USERS: list[User] = [
    {"id": "u1", "groups": ["alpha"]},
    {"id": "u2", "groups": ["alpha", "beta"]},
]

SAMPLE_REPORTS: list[Report] = [
    {"id": "r1", "group": "alpha", "title": "Alpha Q1 Summary"},
    {"id": "r2", "group": "beta", "title": "Beta Audit"},
]
