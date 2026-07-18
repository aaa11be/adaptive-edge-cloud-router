from edge_cloud_router.routing.router import select_endpoint


def test_always_local_strategy() -> None:
    assert select_endpoint("always_local") == "local"


def test_always_cloud_strategy() -> None:
    assert select_endpoint("always_cloud") == "cloud"