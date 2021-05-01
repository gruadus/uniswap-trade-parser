import time


def test():
    from main import get_swaps, SECONDS_IN_DAY, FARM_TOKEN
    start = int(time.time()) - SECONDS_IN_DAY * 7
    result = get_swaps(start, FARM_TOKEN)
    assert len(result.elements) > 0
