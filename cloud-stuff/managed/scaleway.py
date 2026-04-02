"""Scaleway Managed Database and Managed Redis."""

from typing import Any, Dict, Optional

import pulumi
import pulumiverse_scaleway as scaleway
from pulumi import ResourceOptions

from managed import ManagedDatabaseResult, ManagedRedisResult


def create_managed_database(
    config: Dict[str, Any],
    *,
    password: pulumi.Input[str],
    provider: scaleway.Provider,
    project_id: str,
    region: str,
    environment: str,
    private_network: Optional[scaleway.VpcPrivateNetwork] = None,
) -> ManagedDatabaseResult:
    """Provision a Scaleway Managed Database instance + application database."""

    instance_name = config.get("name", "nextcloud-db")
    engine = config.get("engine", "PostgreSQL-16")
    node_type = config.get("node_type", "DB-DEV-S")
    user_name = config.get("user_name", "nextcloud")
    db_name = config.get("db_name", "nextcloud")
    volume_type = config.get("volume_type", "lssd")

    db_kwargs: Dict[str, Any] = {
        "name": instance_name,
        "engine": engine,
        "node_type": node_type,
        "is_ha_cluster": config.get("is_ha_cluster", False),
        "disable_backup": config.get("disable_backup", False),
        "volume_type": volume_type,
        "user_name": user_name,
        "password": password,
        "tags": [f"env_{environment}", "managed_database"],
        "project_id": project_id,
        "region": region,
    }

    if volume_type != "lssd" and config.get("volume_size_in_gb"):
        db_kwargs["volume_size_in_gb"] = config["volume_size_in_gb"]

    if private_network:
        db_kwargs["private_network"] = (
            scaleway.DatabaseInstancePrivateNetworkArgs(
                pn_id=private_network.id,
                enable_ipam=True,
            )
        )

    db_instance = scaleway.DatabaseInstance(
        instance_name,
        opts=ResourceOptions(provider=provider),
        **db_kwargs,
    )

    scaleway.Database(
        db_name,
        name=db_name,
        instance_id=db_instance.id,
        opts=ResourceOptions(provider=provider),
    )

    return ManagedDatabaseResult(
        endpoint_ip=db_instance.endpoint_ip,
        endpoint_port=db_instance.endpoint_port,
        user_name=user_name,
        db_name=db_name,
        engine=engine,
    )


def create_managed_redis(
    config: Dict[str, Any],
    *,
    password: pulumi.Input[str],
    provider: scaleway.Provider,
    project_id: str,
    zone: str,
    environment: str,
    private_network: Optional[scaleway.VpcPrivateNetwork] = None,
) -> ManagedRedisResult:
    """Provision a Scaleway Managed Redis cluster."""

    cluster_name = config.get("name", "nextcloud-redis")
    version = config.get("version", "7.2.7")
    node_type = config.get("node_type", "RED1-MICRO")
    user_name = config.get("user_name", "nextcloud")
    cluster_size = config.get("cluster_size", 1)
    tls_enabled = config.get("tls_enabled", True)

    redis_kwargs: Dict[str, Any] = {
        "name": cluster_name,
        "version": version,
        "node_type": node_type,
        "cluster_size": cluster_size,
        "user_name": user_name,
        "password": password,
        "tls_enabled": tls_enabled,
        "tags": [f"env_{environment}", "managed_redis"],
        "project_id": project_id,
        "zone": zone,
    }

    if private_network:
        redis_kwargs["private_networks"] = [
            scaleway.RedisClusterPrivateNetworkArgs(id=private_network.id)
        ]
    else:
        redis_kwargs["acls"] = [
            scaleway.RedisClusterAclArgs(
                ip="0.0.0.0/0",
                description="Allow all (no private network)",
            )
        ]

    cluster = scaleway.RedisCluster(
        cluster_name,
        opts=ResourceOptions(provider=provider),
        **redis_kwargs,
    )

    return ManagedRedisResult(cluster=cluster)
