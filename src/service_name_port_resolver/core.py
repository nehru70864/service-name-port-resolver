"""Core resolution logic for IANA service names.

The standard library's ``socket.getservbyname`` and ``socket.getservbyport``
are the only portable, dependency-free sources for this data. We wrap them
rather than re-parsing ``/etc/services`` ourselves so that the answers match
what the running system would actually use when binding a socket.
"""

from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Optional

__all__ = ["Service", "Resolver", "resolve"]


@dataclass(frozen=True)
class Service:
    """A resolved service entry.

    Attributes:
        name: The canonical IANA service name, lowercased.
        port: The port number in the range 0-65535.
        protocol: Either ``"tcp"`` or ``"udp"``.
    """

    name: str
    port: int
    protocol: str

    def __post_init__(self) -> None:
        if not 0 <= self.port <= 65535:
            raise ValueError(f"port out of range: {self.port}")
        if self.protocol not in ("tcp", "udp"):
            raise ValueError(f"unsupported protocol: {self.protocol!r}")


class Resolver:
    """Resolves service names and ports using the system service database.

    The resolver is deliberately stateless apart from the protocol default so
    that instances are cheap and safe to share across threads. The underlying
    ``socket`` lookups are pure reads of an OS-level table.
    """

    def __init__(self, default_protocol: str = "tcp") -> None:
        if default_protocol not in ("tcp", "udp"):
            raise ValueError(
                f"default_protocol must be 'tcp' or 'udp', got {default_protocol!r}"
            )
        self.default_protocol = default_protocol

    def by_name(self, name: str, protocol: Optional[str] = None) -> Service:
        """Look up a service by its IANA name.

        ``name`` is matched case-insensitively because ``/etc/services`` is
        conventionally lowercase but callers frequently pass ``"HTTP"``.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("service name must be a non-empty string")
        proto = self._normalize_protocol(protocol)
        key = name.strip().lower()
        try:
            port = socket.getservbyname(key, proto)
        except OSError as exc:
            raise KeyError(f"unknown service {name!r} for protocol {proto!r}") from exc
        return Service(name=key, port=port, protocol=proto)

    def by_port(self, port: int, protocol: Optional[str] = None) -> Service:
        """Look up a service by port number.

        ``getservbyport`` requires the port in network byte order, which is
        why we call ``socket.htons`` rather than passing the integer directly.
        """
        if isinstance(port, bool) or not isinstance(port, int):
            raise TypeError(f"port must be an int, got {type(port).__name__}")
        if not 0 <= port <= 65535:
            raise ValueError(f"port out of range: {port}")
        proto = self._normalize_protocol(protocol)
        try:
            name = socket.getservbyport(port, proto)
        except OSError as exc:
            raise KeyError(f"no service on port {port} for protocol {proto!r}") from exc
        return Service(name=name.lower(), port=port, protocol=proto)

    def _normalize_protocol(self, protocol: Optional[str]) -> str:
        if protocol is None:
            return self.default_protocol
        normalized = protocol.strip().lower()
        if normalized not in ("tcp", "udp"):
            raise ValueError(f"protocol must be 'tcp' or 'udp', got {protocol!r}")
        return normalized


def resolve(name_or_port, protocol: Optional[str] = None) -> Service:
    """Resolve a service name or port number to a :class:`Service`.

    This is a thin convenience wrapper around a module-level
    :class:`Resolver` using the default TCP protocol. Pass an ``int`` to look
    up by port, or a ``str`` to look up by name.
    """
    resolver = _DEFAULT_RESOLVER
    if isinstance(name_or_port, bool):
        raise TypeError("expected a service name or port, got bool")
    if isinstance(name_or_port, int):
        return resolver.by_port(name_or_port, protocol)
    if isinstance(name_or_port, str):
        return resolver.by_name(name_or_port, protocol)
    raise TypeError(
        f"expected str or int, got {type(name_or_port).__name__}"
    )


_DEFAULT_RESOLVER = Resolver()
