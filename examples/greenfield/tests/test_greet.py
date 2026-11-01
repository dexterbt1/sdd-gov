# @spec:0001-REQ-01
# @spec:0001-REQ-02
from src.greet import greet


def test_greet():
    assert greet("Ada") == "Hello, Ada!"
