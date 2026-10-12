def test_basic_addition():
    assert 100 + 200 == 300


def test_average():
    values = [100, 200, 300]
    average = sum(values) / len(values)

    assert average == 200