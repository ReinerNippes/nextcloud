"""Abstract DNS provider interface."""

from abc import ABC, abstractmethod
from typing import Optional

import pulumi


class DnsProvider(ABC):
    """Interface that all DNS providers must implement."""

    @abstractmethod
    def create_record(
        self,
        resource_name: str,
        record_name: str,
        record_type: str,
        value: pulumi.Input[str],
        ttl: int = 60,
    ) -> None:
        """Create a DNS record.

        Args:
            resource_name: Pulumi resource name (unique identifier).
            record_name: DNS record name (e.g. "nextcloud" for nextcloud.example.com).
            record_type: Record type (A, AAAA, CNAME, ...).
            value: Record value (e.g. an IP address).
            ttl: Time-to-live in seconds.
        """


class NullDnsProvider(DnsProvider):
    """No-op DNS provider — used when no DNS is configured."""

    def create_record(self, resource_name, record_name, record_type, value, ttl=60):
        pass
