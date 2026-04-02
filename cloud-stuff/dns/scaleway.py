"""Scaleway DNS provider — uses native Scaleway DomainRecord resources."""

from typing import Optional

import pulumi
import pulumiverse_scaleway as scaleway
from pulumi import ResourceOptions

from dns import DnsProvider


class ScalewayDns(DnsProvider):
    """Scaleway Domains DNS."""

    def __init__(self, zone_name: str, provider: scaleway.Provider):
        self._zone_name = zone_name
        self._provider = provider

    @property
    def zone_name(self) -> str:
        return self._zone_name

    def create_record(self, resource_name, record_name, record_type, value, ttl=60):
        scaleway.DomainRecord(
            resource_name,
            dns_zone=self._zone_name,
            name=record_name,
            type=record_type,
            data=value,
            ttl=ttl,
            opts=ResourceOptions(provider=self._provider),
        )
