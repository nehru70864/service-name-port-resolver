# service-name-port-resolver

Resolves IANA service names to their canonical port numbers and protocols
using the operating system's built-in services database.

```python
from service_name_port_resolver import resolve, Resolver

# Look up by name (defaults to TCP).
http = resolve("http")
assert http.port == 80
assert http.protocol == "tcp"

# Look up by port.
dns = resolve(53, "udp")
assert dns.name == "domain"
assert dns.protocol == "udp"

# Construct a resolver with a non-default protocol.
r = Resolver(default_protocol="udp")
ntp = r.by_name("ntp")
assert ntp.port == 123
```

## Why this exists

Python's standard library exposes the services database only through the
low-level `socket.getservbyname` and `socket.getservbyport` functions. Those
return bare integers or strings and raise `OSError` for every failure mode,
which makes callers write the same try/except boilerplate over and over and
leaves them guessing about the protocol argument. This library wraps those
calls in a small, typed surface: a frozen `Service` record and a `Resolver`
class that validates its inputs and raises `KeyError` for unknown entries
rather than a generic `OSError`.

The trade-off is that we do not ship our own copy of `/etc/services`. That
would make lookups reproducible across machines, but it would also mean the
answers could disagree with what the running system actually binds when it
resolves a service name. We chose to defer to the system database so a
lookup here matches a lookup made by `getaddrinfo` or `socket.bind` on the
same machine.

## The awkward edge

The services database is not guaranteed to contain any particular entry.
Minimal container images, in particular, sometimes ship a stripped-down
`/etc/services` that omits well-known names. `resolve("http")` succeeds on a
typical Linux desktop but may raise `KeyError` inside a slim container. If
you need a guaranteed answer for a well-known port, hard-code the number;
use this library when you want the answer the host would give.

## API

- `resolve(name_or_port, protocol=None) -> Service` — convenience wrapper
  around a module-level `Resolver` with TCP as the default protocol. Pass a
  `str` for a name lookup or an `int` for a port lookup.
- `Resolver(default_protocol="tcp")` — a resolver whose default protocol can
  be overridden. Methods:
  - `by_name(name, protocol=None) -> Service`
  - `by_port(port, protocol=None) -> Service`
- `Service` — a frozen dataclass with `name: str`, `port: int`, and
  `protocol: str` (`"tcp"` or `"udp"`).

Unknown names and ports raise `KeyError`. Invalid protocols, empty names,
and out-of-range ports raise `ValueError`. Passing a `bool` where a port is
expected raises `TypeError` (since `bool` is a subclass of `int`).

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

## Limitations

Values are coerced to floats, so very large integers lose precision. If you need
exact integer aggregates over a window, this is the wrong tool.

