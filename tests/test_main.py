def suma(a:int, b:int) -> int:
    return a+b

def test_suma() -> None:
    res = suma(1,2)
    assert res == 3