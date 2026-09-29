"""Deterministic, realistic incident fixtures for the KARNA demo."""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class DemoIncident:
    """Complete source fixture for one synthetic operational incident."""

    title: str
    description: str
    symptoms: tuple[str, ...]
    category: str
    root_cause: str
    fix: str
    success: bool
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class DemoCorrection:
    """Engineer correction fixture linked to a seeded incident position."""

    incident_index: int
    previous_diagnosis: str
    corrected_diagnosis: str
    explanation: str


@dataclass(frozen=True, slots=True)
class DemoMetaMemory:
    """Reusable operational lesson fixture linked to a seeded incident position."""

    incident_index: int
    content: str


_START_TIME = datetime(2026, 1, 5, 9, 0, 0)


def _build_demo_incidents() -> tuple[DemoIncident, ...]:
    """Build 33 varied incidents with intentional fix-performance patterns."""
    incidents: list[DemoIncident] = []

    for index in range(10):
        restart_succeeded = index < 9
        incidents.append(
            DemoIncident(
                title=f"Checkout API latency spike from exhausted connection pool #{index + 1}",
                description=(
                    "Checkout API p95 latency exceeded 4 seconds while database "
                    "connection pool waiters increased and request timeouts appeared."
                ),
                symptoms=(
                    "API latency spike",
                    "connection pool exhausted",
                    "database timeout",
                ),
                category="Database",
                root_cause="Connection leak",
                fix="Restart connection pool",
                success=restart_succeeded,
                timestamp=_START_TIME + timedelta(hours=index),
            )
        )

    for index in range(8):
        scale_succeeded = index < 2
        incidents.append(
            DemoIncident(
                title=f"Orders API database saturation and latency #{index + 1}",
                description=(
                    "Orders API requests timed out during peak traffic. Database CPU "
                    "was elevated, but connection-pool saturation was not observed."
                ),
                symptoms=(
                    "API latency spike",
                    "database CPU high",
                    "request timeout",
                ),
                category="Database",
                root_cause="Inefficient query plan",
                fix="Scale database",
                success=scale_succeeded,
                timestamp=_START_TIME + timedelta(hours=10 + index),
            )
        )

    incidents.extend(
        (
            DemoIncident(
                title="Payments worker CrashLoopBackOff after certificate rotation",
                description="Payment workers restarted continuously after a mounted certificate path changed.",
                symptoms=("CrashLoopBackOff", "container restart", "certificate error"),
                category="Kubernetes",
                root_cause="Stale certificate mount path",
                fix="Update certificate mount configuration",
                success=True,
                timestamp=_START_TIME + timedelta(hours=18),
            ),
            DemoIncident(
                title="Inventory worker CrashLoopBackOff during startup",
                description="The worker crashed because its required configuration secret was missing.",
                symptoms=("CrashLoopBackOff", "missing secret", "startup failure"),
                category="Kubernetes",
                root_cause="Missing Kubernetes secret",
                fix="Restore required Kubernetes secret",
                success=True,
                timestamp=_START_TIME + timedelta(hours=19),
            ),
            DemoIncident(
                title="Reporting pod restart loop after image update",
                description="The container image used an incompatible startup command and repeatedly exited.",
                symptoms=("CrashLoopBackOff", "container restart", "exit code 127"),
                category="Kubernetes",
                root_cause="Invalid container command",
                fix="Roll back container image",
                success=False,
                timestamp=_START_TIME + timedelta(hours=20),
            ),
            DemoIncident(
                title="Catalog API DNS resolution failures",
                description="Catalog instances could not resolve the internal pricing service hostname.",
                symptoms=("DNS failure", "name resolution", "service unavailable"),
                category="Networking",
                root_cause="Stale CoreDNS cache",
                fix="Restart CoreDNS deployment",
                success=True,
                timestamp=_START_TIME + timedelta(hours=21),
            ),
            DemoIncident(
                title="Fulfillment service intermittent DNS timeout",
                description="Service discovery lookups timed out after a network policy blocked DNS egress.",
                symptoms=("DNS failure", "timeout", "name resolution"),
                category="Networking",
                root_cause="DNS egress blocked by network policy",
                fix="Allow DNS egress in network policy",
                success=True,
                timestamp=_START_TIME + timedelta(hours=22),
            ),
            DemoIncident(
                title="Notifications cannot resolve external webhook host",
                description="Outbound DNS requests failed because the resolver address was misconfigured.",
                symptoms=("DNS failure", "connection refused", "webhook delivery failed"),
                category="Networking",
                root_cause="Incorrect resolver configuration",
                fix="Correct resolver configuration",
                success=True,
                timestamp=_START_TIME + timedelta(hours=23),
            ),
            DemoIncident(
                title="Checkout deployment returns 502 after rollout",
                description="A new deployment referenced a non-existent environment variable and failed readiness checks.",
                symptoms=("502 errors", "readiness failure", "deployment failure"),
                category="Deployment",
                root_cause="Missing environment variable",
                fix="Restore deployment environment variable",
                success=True,
                timestamp=_START_TIME + timedelta(hours=24),
            ),
            DemoIncident(
                title="Search rollout serves stale API configuration",
                description="Pods retained the prior configuration version after a partial rollout.",
                symptoms=("stale configuration", "inconsistent response", "deployment"),
                category="Deployment",
                root_cause="Incomplete rollout",
                fix="Restart deployment rollout",
                success=True,
                timestamp=_START_TIME + timedelta(hours=25),
            ),
            DemoIncident(
                title="Billing release causes repeated migration failure",
                description="The release attempted an incompatible database migration during application startup.",
                symptoms=("deployment failure", "migration error", "startup failure"),
                category="Deployment",
                root_cause="Incompatible schema migration",
                fix="Roll back release and migration",
                success=True,
                timestamp=_START_TIME + timedelta(hours=26),
            ),
            DemoIncident(
                title="Public API p99 latency spike from cache miss storm",
                description="Cache eviction caused repeated expensive profile lookups and elevated API latency.",
                symptoms=("API latency spike", "cache miss", "high CPU"),
                category="API Performance",
                root_cause="Cache eviction storm",
                fix="Warm profile cache",
                success=True,
                timestamp=_START_TIME + timedelta(hours=27),
            ),
            DemoIncident(
                title="Analytics API slow responses during report generation",
                description="Large report queries bypassed pagination and exhausted application workers.",
                symptoms=("high latency", "worker saturation", "slow response"),
                category="API Performance",
                root_cause="Unbounded report query",
                fix="Add report query pagination",
                success=True,
                timestamp=_START_TIME + timedelta(hours=28),
            ),
            DemoIncident(
                title="Partner API timeout after retry configuration change",
                description="Aggressive retries amplified downstream failures and increased response time.",
                symptoms=("timeout", "retry storm", "API latency spike"),
                category="API Performance",
                root_cause="Retry amplification",
                fix="Reduce retry concurrency",
                success=True,
                timestamp=_START_TIME + timedelta(hours=29),
            ),
            DemoIncident(
                title="Admin portal login failures after token signing-key rotation",
                description="New tokens could not be verified because one API instance used an old signing key.",
                symptoms=("authentication failure", "invalid token", "401 responses"),
                category="Authentication",
                root_cause="Inconsistent token signing key",
                fix="Synchronize token signing keys",
                success=True,
                timestamp=_START_TIME + timedelta(hours=30),
            ),
            DemoIncident(
                title="Mobile users receive unauthorized responses after session expiry",
                description="The session refresh endpoint omitted the required audience claim.",
                symptoms=("authentication failure", "401 responses", "session expiry"),
                category="Authentication",
                root_cause="Missing token audience claim",
                fix="Restore token audience claim",
                success=True,
                timestamp=_START_TIME + timedelta(hours=31),
            ),
            DemoIncident(
                title="Service account authentication fails in production",
                description="The service account secret was rotated in the identity provider but not in the cluster.",
                symptoms=("authentication failure", "invalid credentials", "service unavailable"),
                category="Authentication",
                root_cause="Expired service account secret",
                fix="Rotate cluster service account secret",
                success=True,
                timestamp=_START_TIME + timedelta(hours=32),
            ),
        )
    )
    return tuple(incidents)


DEMO_INCIDENTS = _build_demo_incidents()

DEMO_CORRECTIONS: tuple[DemoCorrection, ...] = tuple(
    DemoCorrection(
        incident_index=index,
        previous_diagnosis="Database overload",
        corrected_diagnosis="Connection leak",
        explanation=(
            "Connection pool exhaustion caused API latency; database scaling did "
            "not address the leaked sessions."
        ),
    )
    for index in range(10)
)

DEMO_META_MEMORIES: tuple[DemoMetaMemory, ...] = tuple(
    DemoMetaMemory(
        incident_index=index,
        content=(
            "When API latency spikes and database utilization appears high, check "
            "for connection leaks before scaling the database."
        ),
    )
    for index in range(10)
)
