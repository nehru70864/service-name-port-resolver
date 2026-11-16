import socket
import unittest

from service_name_port_resolver import Resolver, Service, resolve


class TestServiceRecord(unittest.TestCase):
    def test_valid_record(self):
        svc = Service(name="http", port=80, protocol="tcp")
        self.assertEqual(svc.port, 80)
        self.assertEqual(svc.protocol, "tcp")

    def test_port_out_of_range(self):
        with self.assertRaises(ValueError):
            Service(name="x", port=70000, protocol="tcp")

    def test_bad_protocol(self):
        with self.assertRaises(ValueError):
            Service(name="x", port=1, protocol="sctp")


class TestResolverByName(unittest.TestCase):
    def setUp(self):
        self.resolver = Resolver()

    def test_http_tcp(self):
        svc = self.resolver.by_name("http", "tcp")
        self.assertEqual(svc.port, 80)
        self.assertEqual(svc.protocol, "tcp")
        self.assertEqual(svc.name, "http")

    def test_case_insensitive(self):
        svc = self.resolver.by_name("HTTP")
        self.assertEqual(svc.name, "http")
        self.assertEqual(svc.port, 80)

    def test_whitespace_is_trimmed(self):
        svc = self.resolver.by_name("  http  ")
        self.assertEqual(svc.port, 80)

    def test_default_protocol_is_tcp(self):
        svc = self.resolver.by_name("http")
        self.assertEqual(svc.protocol, "tcp")

    def test_unknown_name_raises_keyerror(self):
        with self.assertRaises(KeyError):
            self.resolver.by_name("definitely-not-a-service")

    def test_empty_name_rejected(self):
        with self.assertRaises(ValueError):
            self.resolver.by_name("   ")

    def test_bad_protocol_rejected(self):
        with self.assertRaises(ValueError):
            self.resolver.by_name("http", "sctp")


class TestResolverByPort(unittest.TestCase):
    def setUp(self):
        self.resolver = Resolver()

    def test_port_80_tcp(self):
        svc = self.resolver.by_port(80, "tcp")
        self.assertEqual(svc.port, 80)
        self.assertEqual(svc.protocol, "tcp")
        self.assertEqual(svc.name, "http")

    def test_negative_port_rejected(self):
        with self.assertRaises(ValueError):
            self.resolver.by_port(-1)

    def test_too_large_port_rejected(self):
        with self.assertRaises(ValueError):
            self.resolver.by_port(70000)

    def test_bool_port_rejected(self):
        with self.assertRaises(TypeError):
            self.resolver.by_port(True)  # type: ignore[arg-type]

    def test_unassigned_port_raises_keyerror(self):
        # 64999 is in the unassigned range and should not be in any services
        # file shipped with common Linux distributions.
        with self.assertRaises(KeyError):
            self.resolver.by_port(64999, "tcp")


class TestResolverConstruction(unittest.TestCase):
    def test_bad_default_protocol(self):
        with self.assertRaises(ValueError):
            Resolver(default_protocol="icmp")

    def test_default_protocol_used(self):
        resolver = Resolver(default_protocol="udp")
        svc = resolver.by_name("domain")
        self.assertEqual(svc.protocol, "udp")


class TestResolveFunction(unittest.TestCase):
    def test_resolve_by_name(self):
        svc = resolve("http")
        self.assertEqual(svc.port, 80)

    def test_resolve_by_port(self):
        svc = resolve(80)
        self.assertEqual(svc.name, "http")

    def test_resolve_rejects_bool(self):
        with self.assertRaises(TypeError):
            resolve(True)  # type: ignore[arg-type]

    def test_resolve_rejects_other_types(self):
        with self.assertRaises(TypeError):
            resolve(1.5)  # type: ignore[arg-type]


class TestAgainstSocket(unittest.TestCase):
    """Sanity check: our wrapper agrees with the raw socket API."""

    def test_agrees_with_getservbyname(self):
        expected = socket.getservbyname("ssh", "tcp")
        self.assertEqual(resolve("ssh", "tcp").port, expected)


if __name__ == "__main__":
    unittest.main()
