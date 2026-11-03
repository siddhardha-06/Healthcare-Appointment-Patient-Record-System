"""Tiny in-process publish/subscribe bus.

Services publish events ("appointment.booked", "audit", ...) and other services subscribe,
so a service never has to import a service that is merged later (SAD 3.3 dependencies).
Handlers run synchronously in the publisher's transaction.
"""
from collections import defaultdict
from typing import Callable

_handlers: dict[str, list[Callable]] = defaultdict(list)


def subscribe(event: str):
    def register(fn: Callable):
        if fn not in _handlers[event]:
            _handlers[event].append(fn)
        return fn
    return register


def publish(event: str, **data) -> None:
    for fn in list(_handlers.get(event, [])):
        fn(**data)


def audit(db, user, action: str, record_type: str, record_id=None, ip: str | None = None, detail: str = "") -> None:
    """Shortcut for audit events (HAP-SR-007). The Audit Log service stores them."""
    publish("audit", db=db, user=user, action=action, record_type=record_type,
            record_id=record_id, ip=ip, detail=detail)
