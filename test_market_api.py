from market_api import MarketReader


def test_answer():
    api = MarketReader()
    api.get_prime_items()

    with open(os.path.relpath('resources/primes.txt')) as f:
        assert f.readline() == "&\n"

    assert len(api.prime_items) > 100
    assert type(api.prime_items[0]['item_name']) is str


if __name__ == "__main__":
    test_answer()