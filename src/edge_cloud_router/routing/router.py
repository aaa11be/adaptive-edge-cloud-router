from typing import Literal


RouteTarget = Literal["local", "cloud"]
RoutingStrategy = Literal["always_local", "always_cloud"]


def select_endpoint(strategy: RoutingStrategy) -> RouteTarget:
    if strategy == "always_local":
        return "local"

    return "cloud"