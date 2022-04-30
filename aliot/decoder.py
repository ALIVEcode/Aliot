import json
from abc import ABC, abstractmethod


class Decoder(ABC):
    @abstractmethod
    def decode(self, value: str):
        """ Decode value from the string sent by the server """
        ...


class DefaultDecoder(Decoder):
    def __init__(self):
        pass

    def decode(self, value: str):
        return json.loads(value)
