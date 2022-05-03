import json
from abc import ABC, abstractmethod
from typing import Any


class Decoder(ABC):
    @abstractmethod
    def decode(self, value: str) -> Any:
        """ Decode value from the string sent by the server """
        ...


class DefaultDecoder(Decoder):
    def __init__(self):
        pass

    def decode(self, value: str):
        return json.loads(value)
