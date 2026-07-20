from __future__ import annotations

from edge_cloud_router.routing.latency_estimator import (
    LatencyEstimator,
)
from edge_cloud_router.routing.router import (
    CLOUD_QUALITY_SCORE,
    LOCAL_QUALITY_SCORE,
)
from edge_cloud_router.schemas import (
    EndpointName,
    RoutingContext,
)


DEFAULT_MINIMUM_OBSERVATIONS = 1


def select_exploration_endpoint(
    *,
    context: RoutingContext,
    estimator: LatencyEstimator,
    minimum_observations: int = (
        DEFAULT_MINIMUM_OBSERVATIONS
    ),
) -> EndpointName | None:
    """Select an eligible endpoint that lacks observations.

    Return None when no exploration is needed.
    """

    if minimum_observations <= 0:
        raise ValueError(
            "minimum_observations must be greater than 0"
        )

    eligible_endpoints = _get_eligible_endpoints(context)

    under_observed_endpoints = [
        endpoint
        for endpoint in eligible_endpoints
        if estimator.get_observation_count(endpoint)
        < minimum_observations
    ]

    if not under_observed_endpoints:
        return None

    return min(
        under_observed_endpoints,
        key=lambda endpoint: (
            estimator.get_observation_count(endpoint),
            0 if endpoint == "local" else 1,
        ),
    )


def _get_eligible_endpoints(
    context: RoutingContext,
) -> tuple[EndpointName, ...]:
    """Return endpoints allowed by hard routing constraints."""

    if context.privacy_required:
        return ("local",)

    if not context.cloud_available:
        return ("local",)

    local_meets_quality = (
        LOCAL_QUALITY_SCORE
        >= context.minimum_quality_score
    )
    cloud_meets_quality = (
        CLOUD_QUALITY_SCORE
        >= context.minimum_quality_score
    )

    if local_meets_quality and cloud_meets_quality:
        return (
            "local",
            "cloud",
        )

    if local_meets_quality:
        return ("local",)

    if cloud_meets_quality:
        return ("cloud",)

    # This matches the existing router's fallback:
    # when neither endpoint satisfies the requested quality,
    # choose the higher-quality cloud endpoint.
    return ("cloud",)