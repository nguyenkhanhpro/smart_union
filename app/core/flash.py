"""Thông báo một lần (flash message) lưu trong session."""
from fastapi import Request


def flash(request: Request, message: str, category: str = "success") -> None:
    request.session.setdefault("_flash", []).append({"message": message, "category": category})


def pop_flash(request: Request) -> list[dict]:
    return request.session.pop("_flash", [])
