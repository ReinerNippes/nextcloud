"""Optional managed services (database, Redis).

Currently only Scaleway offers these.  The interface is simple enough that
adding AWS RDS / ElastiCache or others later is straightforward.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

import pulumi


@dataclass
class ManagedDatabaseResult:
    """Standardised return from managed database creation."""
    endpoint_ip: pulumi.Output[str]
    endpoint_port: pulumi.Output[int]
    user_name: str
    db_name: str
    engine: str        # e.g. "PostgreSQL-16"


@dataclass
class ManagedRedisResult:
    """Standardised return from managed Redis creation."""
    cluster: Any       # provider-specific resource (for exports)
