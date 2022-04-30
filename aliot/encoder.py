import json
from abc import ABC, abstractmethod


class Encoder(ABC):
    @abstractmethod
    def encode(self, value) -> str:
        """ Encode value to a string before sending it to server """
        ...


class DefaultEncoder(Encoder):
    def __init__(self):
        pass

    def encode(self, value) -> str:
        return json.dumps(value, default=str)
