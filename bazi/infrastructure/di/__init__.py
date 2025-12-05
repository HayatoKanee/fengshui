"""
Dependency Injection Container.

Simple DI container for wiring up domain services with infrastructure adapters.
"""
from .container import Container, get_container, reset_container

__all__ = [
    "Container",
    "get_container",
    "reset_container",
]
