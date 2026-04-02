"""Hetzner DNS provider — uses the Hetzner Cloud API via pulumi_hcloud."""

import pulumi
import pulumi_hcloud as hcloud

from dns import DnsProvider


class HetznerDns(DnsProvider):
    """Hetzner DNS via Hetzner Cloud API (pulumi_hcloud)."""

    def __init__(self, token: str, zone_name: str, zone_id_override: str | None = None):
        self._zone_name = zone_name
        self._provider = hcloud.Provider(
            "hetzner-dns",
            token=token,
        )
        if zone_id_override:
            self._zone_id = zone_id_override
        else:
            zone = hcloud.get_zone(
                name=zone_name,
                opts=pulumi.InvokeOptions(provider=self._provider),
            )
            self._zone_id = str(zone.id)

    @property
    def zone_name(self) -> str:
        return self._zone_name

    def create_record(self, resource_name, record_name, record_type, value, ttl=60):
        hcloud.ZoneRrset(
            resource_name,
            zone=self._zone_id,
            name=record_name,
            type=record_type,
            ttl=ttl,
            records=[hcloud.ZoneRrsetRecordArgs(value=value)],
            opts=pulumi.ResourceOptions(provider=self._provider),
        )
