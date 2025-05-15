from abc import ABC, abstractmethod


class Repository(ABC):
    @abstractmethod
    def get_data(self):
        """
        Retrieve data from the repository.
        :return: Data from the repository.
        """
        pass
