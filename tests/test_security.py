import jwt
from freezegun import freeze_time
from datetime import  timedelta

from utils.security import create_access_token, SECRET_KEY, ALGORITHM
import pytest

@freeze_time("2012-01-14 03:21:34")
@pytest.mark.parametrize(
    ('td', 'expected'),
    [
        (None, 1326512194),
        (timedelta(minutes=60), 1326514894),
    ],
)
def test_create_access_token(td: timedelta | None, expected: int) -> None:
    token = create_access_token({'a': 'hola', 'b': 'aaa'}, td)
    decoded_data = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
    assert decoded_data['a'] == 'hola'
    assert decoded_data['b'] == 'aaa'
    assert decoded_data['exp'] == expected
