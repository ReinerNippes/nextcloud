"""Nextcloud Wizard — unified multi-provider infrastructure provisioning.

Reads the Pulumi stack config to determine which compute and DNS providers
to use, then delegates to the appropriate plugin modules.
"""

from pathlib import Path
from typing import Optional

import pulumi
import yaml

from cloud_init import make_user_data
from compute import ComputeProvider, ServerResult
from dns import DnsProvider, NullDnsProvider

# --- Configuration -----------------------------------------------------------

config = pulumi.Config()

compute_provider_name = config.require("computeProvider")  # hetzner | scaleway
dns_provider_name = config.get("dnsProvider") or "none"     # hetzner | scaleway | cloudflare | none
ssh_pub_key = config.require("sshPubKey")
zone_name = config.get("zoneName")
environment = config.get("environment") or pulumi.get_stack()
network_config = config.get_object("network")

# --- Instantiate compute provider --------------------------------------------


def _create_compute() -> ComputeProvider:
    if compute_provider_name == "hetzner":
        from compute.hetzner import HetznerCompute
        hetzner_cfg = pulumi.Config("hetzner")
        return HetznerCompute(
            token=hetzner_cfg.require("token"),
            ssh_key_name=hetzner_cfg.require("sshKeyName"),
            location=hetzner_cfg.get("location") or "fsn1",
        )
    elif compute_provider_name == "scaleway":
        from compute.scaleway import ScalewayCompute
        scw_cfg = pulumi.Config("scaleway")
        return ScalewayCompute(
            access_key=scw_cfg.require("accessKey"),
            secret_key=scw_cfg.require("secretKey"),
            project_id=scw_cfg.require("projectId"),
            region=scw_cfg.get("region") or "fr-par",
            zone=scw_cfg.get("zone") or "fr-par-1",
        )
    else:
        raise ValueError(f"Unknown compute provider: {compute_provider_name}")


# --- Instantiate DNS provider ------------------------------------------------


def _create_dns(compute: ComputeProvider) -> DnsProvider:
    if not zone_name or dns_provider_name == "none":
        return NullDnsProvider()

    if dns_provider_name == "hetzner":
        from dns.hetzner import HetznerDns
        hetzner_dns_cfg = pulumi.Config("hetznerDns")
        return HetznerDns(
            token=hetzner_dns_cfg.require("token"),
            zone_name=zone_name,
            zone_id_override=hetzner_dns_cfg.get("zoneId"),
        )
    elif dns_provider_name == "scaleway":
        from dns.scaleway import ScalewayDns
        from compute.scaleway import ScalewayCompute
        if not isinstance(compute, ScalewayCompute):
            raise ValueError("Scaleway DNS requires Scaleway compute (needs the provider)")
        return ScalewayDns(zone_name=zone_name, provider=compute.provider)

    elif dns_provider_name == "cloudflare":
        from dns.cloudflare import CloudflareDns
        cf_cfg = pulumi.Config("cloudflare")
        return CloudflareDns(
            api_token=cf_cfg.require("apiToken"),
            zone_name=zone_name,
            zone_id_override=cf_cfg.get("zoneId"),
        )
    else:
        raise ValueError(f"Unknown DNS provider: {dns_provider_name}")


# --- Build infrastructure ----------------------------------------------------

compute = _create_compute()
dns = _create_dns(compute)

user_data = make_user_data(ssh_pub_key)

# Servers
default_image = config.get("image") or "debian-13"
default_server_specs = [
    {"name": "nextcloud", "server_type": "cx32"},
]
server_specs = config.get_object("servers") or default_server_specs

# Apply default image to servers that don't specify one
for spec in server_specs:
    spec.setdefault("image", default_image)

servers = compute.create_servers(
    server_specs,
    ssh_pub_key=ssh_pub_key,
    user_data=user_data,
    environment=environment,
    zone_name=zone_name,
    network_config=network_config,
)

# DNS records for public servers
for spec in server_specs:
    name = spec["name"]
    result = servers.get(name)
    if result and result.public_ip:
        zone_suffix = f".{zone_name}" if zone_name else ""
        def normalize_additional_fqdn(value: str) -> str:
            if zone_name and not (value.endswith(zone_suffix) or value.count(".") >= 2):
                return f"{value}{zone_suffix}"
            return value

        dns_aliases = spec.get("dns_aliases", [])
        if isinstance(dns_aliases, str):
            dns_aliases = [dns_aliases]

        additional_fqdn_values = []
        for k, v in spec.items():
            if k.startswith("additional_fqdn_") and isinstance(v, str) and v:
                additional_fqdn_values.append(normalize_additional_fqdn(v))
        raw_additional_fqdns = spec.get("additional_fqdns", {})
        if isinstance(raw_additional_fqdns, dict):
            for v in raw_additional_fqdns.values():
                if isinstance(v, str) and v:
                    additional_fqdn_values.append(normalize_additional_fqdn(v))

        all_aliases = []
        seen_aliases = set()
        for alias in [*dns_aliases, *additional_fqdn_values]:
            if alias and alias not in seen_aliases:
                seen_aliases.add(alias)
                all_aliases.append(alias)

        record_name = name
        if zone_name and name.endswith(f".{zone_name}"):
            record_name = name[: -len(f".{zone_name}")]
        dns.create_record(f"{name}-a", record_name, "A", result.public_ip)

        # DNS aliases
        for alias in all_aliases:
            alias_name = alias
            if zone_name and alias.endswith(f".{zone_name}"):
                alias_name = alias[: -len(f".{zone_name}")]
            dns.create_record(f"{name}-alias-{alias_name}-a", alias_name, "A", result.public_ip)

# --- Managed services (Scaleway only, for now) --------------------------------

managed_db = None
managed_redis = None
db_config = config.get_object("managedDatabase")
redis_config = config.get_object("managedRedis")

if db_config or redis_config:
    from compute.scaleway import ScalewayCompute
    if not isinstance(compute, ScalewayCompute):
        pulumi.log.warn("Managed services are currently only supported with Scaleway compute")
    else:
        if db_config:
            from managed.scaleway import create_managed_database
            db_password = config.require_secret("dbPassword")
            managed_db = create_managed_database(
                db_config,
                password=db_password,
                provider=compute.provider,
                project_id=compute.project_id,
                region=compute.region,
                environment=environment,
                private_network=None,  # TODO: wire up private network from compute
            )

        if redis_config:
            from managed.scaleway import create_managed_redis
            redis_password = config.require_secret("redisPassword")
            managed_redis = create_managed_redis(
                redis_config,
                password=redis_password,
                provider=compute.provider,
                project_id=compute.project_id,
                zone=compute.zone,
                environment=environment,
                private_network=None,  # TODO: wire up private network from compute
            )

# --- Exports -----------------------------------------------------------------

for name, result in servers.items():
    if result.public_ip:
        pulumi.export(f"{name}_ipv4", result.public_ip)

if managed_db:
    pulumi.export("database_endpoint_ip", managed_db.endpoint_ip)
    pulumi.export("database_endpoint_port", managed_db.endpoint_port)

if managed_redis:
    pulumi.export("redis_cluster_id", managed_redis.cluster.id)

pulumi.export("environment", environment)
pulumi.export("compute_provider", compute_provider_name)
pulumi.export("dns_provider", dns_provider_name)

# --- Generate Ansible group_vars for managed services ------------------------

GROUP_VARS_DIR = Path(__file__).resolve().parent.parent.parent / "group_vars" / "all"


def _write_managed_vars(args):
    """Write managed service credentials to group_vars/all/managed_services.yml."""
    vals = dict(zip(args[0::2], args[1::2]))
    managed = {}

    if "db_host" in vals:
        engine = vals.get("db_engine", "PostgreSQL-16")
        db_type = "pgsql" if engine.lower().startswith("postgre") else "mysql"
        managed["nextcloud_db"] = {
            "type": db_type,
            "host": vals["db_host"],
            "port": str(vals["db_port"]),
            "name": vals["db_name"],
            "user": vals["db_user"],
            "password": vals["db_password"],
            "admin_user": vals["db_user"],
            "admin_password": vals["db_password"],
        }

    if "redis_host" in vals:
        managed["redis_tcp"] = {
            "address": vals["redis_host"],
            "port": str(vals["redis_port"]),
        }
        managed["passwords"] = {"redis": vals["redis_password"]}

    if not managed:
        return

    header = (
        "---\n"
        "# Auto-generated by Pulumi (cloud-stuff/nextcloud-wizard)\n"
        "# Do not edit — will be overwritten on next 'pulumi up'\n\n"
    )
    GROUP_VARS_DIR.mkdir(parents=True, exist_ok=True)
    outfile = GROUP_VARS_DIR / "managed_services.yml"
    outfile.write_text(header + yaml.dump(managed, default_flow_style=False))
    pulumi.log.info(f"Wrote managed service vars to {outfile}")


output_pairs: list = []

if managed_db:
    output_pairs += [
        "db_host", managed_db.endpoint_ip,
        "db_port", managed_db.endpoint_port,
        "db_name", managed_db.db_name,
        "db_user", managed_db.user_name,
        "db_engine", managed_db.engine,
        "db_password", db_password,
    ]

if managed_redis:
    cluster = managed_redis.cluster
    output_pairs += [
        "redis_host", cluster.public_network.apply(
            lambda pn: pn.ips[0] if pn and pn.ips else ""),
        "redis_port", cluster.public_network.apply(
            lambda pn: str(pn.port) if pn and pn.port else "6379"),
        "redis_password", redis_password,
    ]

if output_pairs:
    pulumi.Output.all(*output_pairs).apply(_write_managed_vars)
