"""Cloudflare DNS provider — uses pulumi-cloudflare resources."""

from typing import Optional

import pulumi
import pulumi_cloudflare as cloudflare
from pulumi import ResourceOptions

from dns import DnsProvider


class CloudflareDns(DnsProvider):
    """Cloudflare DNS."""

    def __init__(self, api_token: str, zone_name: str, zone_id_override: Optional[str] = None):
        self._provider = cloudflare.Provider(
            "cloudflare",
            api_token=api_token,
        )
        self._zone_name = zone_name

        if zone_id_override:
            self._zone_id = zone_id_override
        else:
            zone = cloudflare.get_zone(name=zone_name)
            self._zone_id = zone.zone_id

    @property
    def zone_name(self) -> str:
        return self._zone_name

    def create_record(self, resource_name, record_name, record_type, value, ttl=60):
        cloudflare.Record(
            resource_name,
            zone_id=self._zone_id,
            name=record_name,
            type=record_type,
            content=value,
            ttl=ttl,
            opts=ResourceOptions(provider=self._provider),
        )
