import pytest
from src.skills.base import BaseSkill


def test_base_skill_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        BaseSkill()


def test_base_skill_subclass_instantiation():
    class DummySkill(BaseSkill):
        async def execute(self, *args, **kwargs):
            return "executed"

    skill = DummySkill()
    assert isinstance(skill, BaseSkill)
