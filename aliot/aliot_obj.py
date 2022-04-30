from __future__ import annotations

import json
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from encoder import Encoder
    from decoder import Decoder

from threading import Thread
from typing import Optional, Callable

from websocket import WebSocketApp

from aliot.core._cli.utils import print_success, print_err, print_warning, print_info
from aliot.core._config.config import get_config
from aliot.constants import ALIVE_IOT_EVENT
from aliot.decoder import DefaultDecoder
from aliot.encoder import DefaultEncoder


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
        self.__api_url: str = self.__get_config_value("api_url")
        self.__ws_url: str = self.__get_config_value("ws_url")

    # ################################# Properties ################################# #

    @property
    def name(self):
        return self.__name

    @property
    def encoder(self) -> Encoder:
        return self.__encoder

    @encoder.setter
    def encoder(self, encoder: Encoder):
        self.__encoder = encoder

    @property
    def decoder(self) -> Decoder:
        return self.__decoder

    @decoder.setter
    def decoder(self, decoder: Decoder):
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

    # ################################# Public methods ################################# #

    def run(self):
        self.__setup_ws()
        self.__ws.run_forever()

    def on_recv(self, action_id: int, log_reception: bool = True, ):
        def inner(func):
            def wrapper(*args, **kwargs):
                if log_reception:
                    print(f"The protocol: {action_id!r} was called with the arguments: "
                          f"{args}")
                res = func(*args, **kwargs)
                self.__send_event(ALIVE_IOT_EVENT.SEND_ACTION_DONE, {
                    "actionId": action_id,
                    "value": res
                })

            self.__protocols[action_id] = wrapper
            return wrapper

        return inner

    def listen(self, fields: list[str]):
        def inner(func):
            def wrapper(fields: dict):
                result = func(fields)

            self.__listeners.append({
                'func': wrapper,
                'fields': fields
            })
            return wrapper

        return inner

    def listen_broadcast(self):
        def inner(func):
            def wrapper(fields: dict):
                result = func(fields)

            self.__broadcast_listener = wrapper
            return wrapper

        return inner

    def main_loop(self, repetitions=None):
        def inner(main_loop_func):
            def wrapper():
                while not self.connected_to_alivecode:
                    pass
                if repetitions is not None:
                    for _ in range(repetitions):
                        if not self.connected_to_alivecode:
                            break
                        main_loop_func()
                else:
                    while self.connected_to_alivecode:
                        main_loop_func()

            self.__main_loop = wrapper
            return wrapper

        return inner

    def update_component(self, id: str, value):
        self.__send_event(ALIVE_IOT_EVENT.UPDATE_COMPONENT, {
            'id': id, 'value': value
        })

    def broadcast(self, data: dict):
        self.__send_event(ALIVE_IOT_EVENT.SEND_BROADCAST, {
            'data': data
        })

    def update_doc(self, fields: dict):
        self.__send_event(ALIVE_IOT_EVENT.UPDATE_DOC, {
            'fields': fields,
        })

    def get_doc(self, field: Optional[str] = None):
        if field:
            res = requests.post(f'{self.__api_url}/iot/aliot/{ALIVE_IOT_EVENT.GET_FIELD.value[0]}',
                                {'id': self.object_id, 'field': field})
            match res.status_code:
                case 201:
                    return json.loads(res.text) if res.text else None
                case 403:
                    print_err(
                        f"While getting the field {field}, "
                        f"request was Forbidden due to permission errors or project missing.")
                case 500:
                    print_err(
                        f"While getting the field {field}, "
                        f"something went wrong with the ALIVEcode's servers, please try again.")
                case _:
                    print_err(f"While getting the field {field}, please try again. {res.json()!r}")
        else:
            res = requests.post(f'{self.__api_url}/iot/aliot/{ALIVE_IOT_EVENT.GET_DOC.value[0]}',
                                {'id': self.object_id})
            match res.status_code:
                case 201:
                    return json.loads(res.text) if res.text else None
                case 403:
                    print_err(
                        f"While getting the document, request was Forbidden due "
                        f"to permission errors or project missing.")
                case 500:
                    print_err(
                        f"While getting the document, something went wrong with the ALIVEcode's servers, "
                        f"please try again.")
                case _:
                    print_err(f"&c[ERROR] while getting the document, please try again. {res.json()}")

    def send_route(self, routePath: str, data: dict):
        self.__send_event(ALIVE_IOT_EVENT.SEND_ROUTE, {
            'routePath': routePath,
            'data': data
        })

    def send_action(self, targetId: str, actionId: int, value=""):
        self.__send_event(ALIVE_IOT_EVENT.SEND_ACTION, {
            'targetId': targetId,
            'actionId': actionId,
            'value': value
        })

    # ################################# Private methods ################################# #

    def __get_config_value(self, key):
        return self.__config.get(self.__name, key, fallback=None) or self.__config.defaults().get(key)

    def __send_event(self, event: ALIVE_IOT_EVENT, data: Optional[dict]):
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
            print_info("Connection CLOSED")
        else:
            protocol(msg["value"])

    # ################################# Websocket methods ################################# #

    def __on_message(self, ws, message):
        msg = self.decoder.decode(message)

        event: str = msg['event']
        data = msg['data']

        match ALIVE_IOT_EVENT.__members__.get(event):
            case ALIVE_IOT_EVENT.CONNECT_SUCCESS:
                if len(self.__listeners) == 0:
                    print_success("CONNECTED")
                    self.connected_to_alivecode = True
                else:
                    # Register listeners on ALIVEcode
                    fields = sorted(set([field for l in self.listeners for field in l['fields']]))
                    self.__send_event(ALIVE_IOT_EVENT.SUBSCRIBE_LISTENER, {'fields': fields})

            case ALIVE_IOT_EVENT.RECEIVE_ACTION:
                self.__execute_protocol(data)

            case ALIVE_IOT_EVENT.RECEIVE_LISTEN:
                self.__execute_listen(data['fields'])

            case ALIVE_IOT_EVENT.RECEIVE_BROADCAST:
                self.__execute_broadcast(data['data'])

            case ALIVE_IOT_EVENT.SUBSCRIBE_LISTENER_SUCCESS:
                self.__listeners_set += 1
                if self.__listeners_set == len(self.__listeners):
                    print_success("CONNECTED")
                    self.connected_to_alivecode = True

            case ALIVE_IOT_EVENT.ERROR:
                print_err(f"{event=}  {data=}")

            case ALIVE_IOT_EVENT.PING:
                self.__send_event(ALIVE_IOT_EVENT.PONG, None)

            case None:
                pass

    def __on_error(self, ws, error):
        print_err(f"{error!r}")
        if isinstance(error, ConnectionResetError):
            print_warning("If you didn't see the 'CONNECTED', "
                          "message verify that you are using the right key")

    def __on_close(self, ws, *_):
        self.__connected_to_alivecode = False
        self.__connected = False
        print_info("Connection CLOSED")

    def __on_open(self, ws):
        # Register IoTObject on ALIVEcode
        self.__connected = True
        self.__send_event(ALIVE_IOT_EVENT.CONNECT_OBJECT, {'id': self.object_id})

        if self.__main_loop is None:
            self.__ws.close()
            raise NotImplementedError("You must define a main loop")

        Thread(target=self.__main_loop, daemon=True).start()

    def __setup_ws(self):
        self.__ws = WebSocketApp(self.__ws_url,
                                 on_open=self.__on_open,
                                 on_message=self.__on_message,
                                 on_error=self.__on_error,
                                 on_close=self.__on_close
                                 )
