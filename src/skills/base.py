from abc import ABC, abstractmethod
from typing import Any


class BaseSkill(ABC):
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        pass
