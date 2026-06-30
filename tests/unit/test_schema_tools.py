from src.utils.schema_tools import get_schema


def test_get_schema():
    assert get_schema("any_name") == {}
