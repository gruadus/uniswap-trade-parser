import time


def test():
    from main import get_swaps, SECONDS_IN_DAY
    start = int(time.time()) - SECONDS_IN_DAY * 1
    result = get_swaps(start, '0xa0246c9032bc3a600820415ae600c6388619a14d', 0,
                       '0x1571eD0bed4D987fe2b498DdBaE7DFA19519F651')
    assert len(result.elements) > 0
