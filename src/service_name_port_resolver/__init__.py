"""Resolve IANA service names to canonical port numbers and protocols.

This package exposes a single public function, :func:`resolve`, plus the
:class:`Service` record it returns. All lookups are backed by the operating
system's service database (``/etc/services`` on POSIX, the equivalent on
Windows) via :func:`socket.getservbyname` and :func:`socket.getservbyport`.
"""

from .core import Service, Resolver, resolve

__all__ = ["Service", "Resolver", "resolve"]
