"""

"""
import json
from abc import ABC, abstractmethod
from threading import Thread
from typing import Optional, Callable

from websocket import WebSocketApp

from aliot._cli.utils import print_success, print_err, print_warning, print_info
from aliot._config.config import get_config
from aliot.iot.constants import IOT_EVENT


class AliotObj:
    def __init__(self, name: str):
        self.__name = name
        self.__ws: Optional[WebSocketApp] = None
        self.__encoder = DefaultEncoder()
        self.__decoder = DefaultDecoder()
        self.__config = get_config()
        self.__protocols = {}
        self.__listeners = []
        self.__broadcast_listener: Optional[Callable[[dict], None]] = None
        self.__connected_to_alivecode = False
        self.__connected = False
        self.__main_loop = None
        self.__repeats = 0
        self.__last_freeze = 0
        self.__listeners_set = 0

    # ################################# Public methods ################################# #

    def run(self):
        self.__ws.run_forever()

    # ################################# Properties methods ################################# #

    @property
    def name(self):
        return self.__name

    @property
    def encoder(self):
        return self.__encoder

    @encoder.setter
    def encoder(self, encoder: "Encoder"):
        self.__encoder = encoder

    @property
    def decoder(self):
        return self.__decoder

    @decoder.setter
    def decoder(self, decoder: "Decoder"):
        self.__decoder = decoder

    @property
    def object_id(self):
        return self.__get_config_value("obj_id")

    @property
    def protocols(self):
        """ Returns a copy of the protocols dict """
        return self.__protocols.copy()

    @property
    def listeners(self):
        """ Returns a copy of the listeners list """
        return self.__listeners.copy()

    @property
    def broadcast_listener(self):
        return self.__broadcast_listener

    @property
    def connected_to_alivecode(self):
        return self.__connected_to_alivecode

    @connected_to_alivecode.setter
    def connected_to_alivecode(self, value: bool):
        self.__connected_to_alivecode = value
        if not value and self.__connected:
            self.__ws.close()

    # ################################# Private methods ################################# #

    def __get_config_value(self, key):
        return self.__config.get(self.__name, key)

    def __send_event(self, event: IOT_EVENT, data: Optional[dict]):
        if self.__connected:
            self.__ws.send(self.encoder.encode({'event': event.value[0], 'data': data}))
            self.__repeats += 1

    def __execute_listen(self, fields: dict):
        for listener in self.listeners:
            fieldsToReturn = dict(filter(lambda el: el[0] in listener['fields'], fields.items()))
            if len(fieldsToReturn) > 0:
                listener["func"](fieldsToReturn)

    def __execute_broadcast(self, data: dict):
        if self.broadcast_listener:
            self.broadcast_listener(data)

    def __execute_protocol(self, msg: dict | list):
        if isinstance(msg, list):
            for m in msg:
                self.__execute_protocol(m)
        print(msg)
        must_have_keys = "id", "value"
        if not all(key in msg for key in must_have_keys):
            print("the message received does not have a valid structure")
            return

        msg_id = msg["id"]
        protocol = self.protocols.get(msg_id)

        if protocol is None:
            if self.connected_to_alivecode:
                self.connected_to_alivecode = False
            print_err(f"The protocol with the id {msg_id!r} is not implemented")

            # magic of python
            print_info("CLOSED")
        else:
            protocol(msg["value"])

    def __on_message(self, ws, message):
        msg = self.decoder.decode(message)

        event: str = msg['event']
        data = msg['data']

        match IOT_EVENT.__members__.get(event):
            case IOT_EVENT.CONNECT_SUCCESS:
                if len(self.__listeners) == 0:
                    print_success("CONNECTED")
                    self.connected_to_alivecode = True
                else:
                    # Register listeners on ALIVEcode
                    fields = sorted(set([field for l in self.listeners for field in l['fields']]))
                    self.__send_event(IOT_EVENT.SUBSCRIBE_LISTENER, {'fields': fields})

            case IOT_EVENT.RECEIVE_ACTION:
                self.__execute_protocol(data)

            case IOT_EVENT.RECEIVE_LISTEN:
                self.__execute_listen(data['fields'])

            case IOT_EVENT.RECEIVE_BROADCAST:
                self.__execute_broadcast(data['data'])

            case IOT_EVENT.SUBSCRIBE_LISTENER_SUCCESS:
                self.__listeners_set += 1
                if self.__listeners_set == len(self.__listeners):
                    print_success("CONNECTED")
                    self.connected_to_alivecode = True

            case IOT_EVENT.ERROR:
                print_err(data)

            case IOT_EVENT.PING:
                self.__send_event(IOT_EVENT.PONG, None)

            case None:
                pass

    def __on_error(self, ws, error):
        print_err(f"{error!r}")
        if isinstance(error, ConnectionResetError):
            print_warning("If you didn't see the 'CONNECTED', "
                          "message verify that you are using the right key")

    def __on_close(self, ws):
        self.__connected_to_alivecode = False
        self.__connected = False
        print_info("CLOSED")

    def __on_open(self, ws):
        # Register IoTObject on ALIVEcode
        self.__connected = True
        self.__send_event(IOT_EVENT.CONNECT_OBJECT, {'id': self.object_id})

        if self.__main_loop is None:
            self.__ws.close()
            raise NotImplementedError("You must define a main loop")

        Thread(target=self.__main_loop, daemon=True).start()

    def __setup_ws(self):
        url = self.__get_config_value("ws_url")
        self.__ws = WebSocketApp(url,
                                 on_open=self.__on_open,
                                 on_message=self.__on_message,
                                 on_error=self.__on_error,
                                 on_close=self.__on_close
                                 )


class Encoder(ABC):
    @abstractmethod
    def encode(self, value) -> str:
        """ Encode value to a string before sending it to server """
        ...


class Decoder(ABC):
    @abstractmethod
    def decode(self, value: str):
        """ Decode value from the string sent by the server """
        ...


class DefaultEncoder(Encoder):
    def __init__(self):
        pass

    def encode(self, value) -> str:
        return json.dumps(value, default=str)


class DefaultDecoder(Decoder):
    def __init__(self):
        pass

    def decode(self, value: str):
        return json.loads(value)
