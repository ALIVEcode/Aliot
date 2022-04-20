"""

"""
import json
from abc import ABC, abstractmethod
from threading import Thread
from typing import Optional

from websocket import WebSocketApp

from aliot._cli.utils import print_success, print_err, print_warning, print_info
from aliot._config.config import get_config
from aliot.iot.constants import IOT_EVENT


class AliotObj:
    def __init__(self, name: str):
        self.protocols = None
        self.name = name
        self.encoder = DefaultEncoder()
        self.decoder = DefaultDecoder()
        self.config = get_config()
        self.ws: Optional[WebSocketApp] = None

    def __get_config_value(self, key):
        return self.config.get(self.name, key)

    def set_encoder(self, encoder):
        self.encoder = encoder

    def set_decoder(self, decoder):
        self.decoder = decoder

    def run(self):
        self.ws.run_forever()

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
        msg = json.loads(message)

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
        self.__send_event(IOT_EVENT.CONNECT_OBJECT, {'id': self.__id})

        if self.__main_loop is None:
            self.ws.close()
            raise NotImplementedError("You must define a main loop")

        Thread(target=self.__main_loop, daemon=True).start()

    def __setup_ws(self):
        url = self.__get_config_value("ws_url")
        self.ws = WebSocketApp(url,
                               on_open=self.__on_open,
                               on_message=self.__on_message,
                               on_error=self.__on_error,
                               on_close=self.__on_close
                               )


class Encoder(ABC):
    @abstractmethod
    def encode(self, value):
        """ Encode value before sending to server """
        ...


class Decoder(ABC):
    @abstractmethod
    def decode(self, value):
        """ Decode value after receiving from server """
        ...


class DefaultEncoder(Encoder):
    def __init__(self):
        pass

    def encode(self, value):
        return value


class DefaultDecoder(Decoder):
    def __init__(self):
        pass

    def decode(self, value):
        return value
