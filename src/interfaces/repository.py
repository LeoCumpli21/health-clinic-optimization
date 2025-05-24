from abc import ABC, abstractmethod
from typing import Any


class Repository(ABC):
    @abstractmethod
    def get_data(self, filters: Any) -> Any:
        """
        Retrieve data from the repository.
        :return: Data from the repository.
        """
        pass
