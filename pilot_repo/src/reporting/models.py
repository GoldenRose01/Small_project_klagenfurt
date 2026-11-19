"""Data structures for users and reports (Python standard library only)."""

from typing import TypedDict


class Report(TypedDict):
    id: str
    group: str
    title: str


class User(TypedDict):
    id: str
    groups: list[str]
