from __future__ import annotations

import json
import warnings
from functools import wraps
from threading import Thread
from typing import TYPE_CHECKING
from time import ctime, sleep

import requests

from aliot.exceptions.should_not_call_error import ShouldNotCallError

if TYPE_CHECKING:
    from encoder import Encoder
    from decoder import Decoder

from typing import Optional, Callable

from websocket import WebSocketApp
import websocket

from aliot.core._cli.utils import (
    print_success,
    print_err,
    print_warning,
    print_info,
    print_log,
    print_fail,
)
from aliot.core._config.config import get_config
from aliot.constants import ALIVE_IOT_EVENT
from aliot.decoder import DefaultDecoder
from aliot.encoder import DefaultEncoder

_no_value = object()


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
        self.__stopped = False
        self.__on_start: Optional[tuple[Callable, tuple, dict]] = None
        self.__on_end: Optional[tuple[Callable, tuple, dict]] = None
        self.__repeats = 0
        self.__last_freeze = 0
        self.__listeners_set = 0
        self.__api_url: str = self.__get_config_value("api_url")
        self.__ws_url: str = self.__get_config_value("ws_url")
        self.__log = False

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
    def auth_token(self):
        return self.__get_config_value("auth_token")

    @property
    def protocols(self):
        """Returns a copy of the protocols dict"""
        return self.__protocols.copy()

    @property
    def listeners(self):
        """Returns a copy of the listeners list"""
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

    def run(self, *, enable_trace: bool = False, log: bool = False, retry = True, retry_time = None):
        self.__log = log
        self.__setup_ws(enable_trace)
        
        first_retry = True
        self.retry_connection_amount = 0

        # Retry connection in a loop
        while retry and not self.__stopped:
            waitTime = retry_time or (5 * 2 ** self.retry_connection_amount)
            
            print_info(f"Retrying connection in {waitTime} seconds. Current time : {ctime()}")
            
            if first_retry:
                first_retry = False
                print_info("Please note that you can disable connect retry with retry=False when calling run(). You can also change the retry time to a fix amount by passing retry_time=<SECONDS> .")
            
            sleep(waitTime)
            self.__setup_ws(enable_trace)
            
            # Constraint retry amount for exponential wait time
            self.retry_connection_amount += 1
            if self.retry_connection_amount > 7:
                self.retry_connection_amount = 7

    def stop(self):
        if self.__connected and self.__ws:
            self.__stopped = True
            self.__ws.close()

    def update_component(self, id: str, value):
        self.__send_event(ALIVE_IOT_EVENT.UPDATE_COMPONENT, {"id": id, "value": value})

    def send_broadcast(self, data: dict):
        self.__send_event(ALIVE_IOT_EVENT.SEND_BROADCAST, {"data": data})

    def update_doc(self, fields: dict):
        self.__send_event(
            ALIVE_IOT_EVENT.UPDATE_DOC,
            {
                "fields": fields,
            },
        )

    def get_doc(self, field: Optional[str] = None):

        if field:
            res = requests.post(
                f"{self.__api_url}/iot/aliot/{ALIVE_IOT_EVENT.GET_FIELD.value}",
                {"id": self.object_id, "field": field},
            )
            status = res.status_code
            if status == 201:
                return json.loads(res.text) if res.text else None
            elif status == 403:
                print_err(
                    f"While getting the field {field}, "
                    f"request was Forbidden due to permission errors or project missing."
                )
            elif status == 500:
                print_err(
                    f"While getting the field {field}, "
                    f"something went wrong with the ALIVEcode's servers, please try again."
                )
            else:
                print_err(
                    f"While getting the field {field}, please try again. {res.json()!r}"
                )
        else:
            res = requests.post(
                f"{self.__api_url}/iot/aliot/{ALIVE_IOT_EVENT.GET_DOC.value}",
                {"id": self.object_id},
            )
            status = res.status_code
            if status == 201:
                return json.loads(res.text) if res.text else None
            elif status == 403:
                print_err(
                    f"While getting the document, request was Forbidden due "
                    f"to permission errors or project missing."
                )
            elif status == 500:
                print_err(
                    f"While getting the document, something went wrong with the ALIVEcode's servers, "
                    f"please try again."
                )
            else:
                print_err(f"While getting the document, please try again. {res.json()}")

    def send_route(self, route_path: str, data: dict):
        self.__send_event(
            ALIVE_IOT_EVENT.SEND_ROUTE, {"routePath": route_path, "data": data}
        )

    def send_action(self, target_id: str, action_id: str, data: dict | None = None):
        if data == None:
            data = {}
        self.__send_event(
            ALIVE_IOT_EVENT.SEND_ACTION,
            {"targetId": target_id, "actionId": action_id, "value": data},
        )

    # ################################# Decorators methods ################################# #

    def on_start(
        self, callback=None, *, args: list = _no_value, kwargs: dict = _no_value
    ):
        if kwargs is _no_value:
            kwargs = {}
        if args is _no_value:
            args = ()

        def inner(f):
            if self.__on_start is not None:
                raise ValueError(
                    f"A function is already assigned to that role: {self.__on_start[0].__name__}"
                )

            self.__on_start = (f, args, kwargs)

            @wraps(f)
            def innest():
                print_err(
                    f"You should not call the function {f.__name__!r} yourself. "
                    f"Aliot will take care of it and will "
                    f"automatically call {f.__name__!r} when your object is connected to the website.",
                    ShouldNotCallError.__name__,
                )
                exit(-1)

            return innest

        if callback is not None:
            return inner(callback)

        return inner

    def on_end(
        self, callback=None, *, args: list = _no_value, kwargs: dict = _no_value
    ):
        if kwargs is _no_value:
            kwargs = {}
        if args is _no_value:
            args = ()

        def inner(f):
            if self.__on_end is not None:
                raise ValueError(
                    f"A function is already assigned to that role: {self.__on_end[0].__name__}"
                )
            self.__on_end = (f, args, kwargs)

            @wraps(f)
            def innest():
                print_err(
                    f"You should not call the function {f.__name__!r} yourself. "
                    f"Aliot will take care of it and will "
                    f"automatically call {f.__name__!r} when your object is disconnected to the website.",
                    ShouldNotCallError.__name__,
                )
                exit(-1)

            return innest

        if callback is not None:
            return inner(callback)

        return inner

    """ DEPRECATED METHOD """

    def on_recv(self, action_id: str, callback=None, log_reception: bool = True):
        def inner(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if log_reception:
                    print(
                        f"The protocol: {action_id!r} was called with the arguments: "
                        f"{args}"
                    )
                res = func(*args, **kwargs)
                self.__send_event(
                    ALIVE_IOT_EVENT.SEND_ACTION_DONE,
                    {"actionId": action_id, "value": res},
                )

            self.__protocols[action_id] = wrapper
            return wrapper

        if callback is not None:
            return inner(callback)

        return inner

    def on_action_recv(
        self, action_id: str, callback=None, log_reception: bool = True
    ):
        def inner(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if log_reception:
                    print(
                        f"The protocol: {action_id!r} was called with the arguments: "
                        f"{args}"
                    )
                res = func(*args, **kwargs)
                self.__send_event(
                    ALIVE_IOT_EVENT.SEND_ACTION_DONE,
                    {"actionId": action_id, "value": res},
                )

            self.__protocols[action_id] = wrapper
            return wrapper

        if callback is not None:
            return inner(callback)

        return inner

    """ DEPRECATED METHOD """

    def listen(self, fields: list[str], callback=None):
        def inner(func):
            @wraps(func)
            def wrapper(fields: dict):
                result = func(fields)

            self.__listeners.append({"func": wrapper, "fields": fields})
            return wrapper

        if callback is not None:
            return inner(callback)

        return inner

    def listen_doc(self, fields: list[str], callback=None):
        def inner(func):
            @wraps(func)
            def wrapper(fields: dict):
                result = func(fields)

            self.__listeners.append({"func": wrapper, "fields": fields})
            return wrapper

        if callback is not None:
            return inner(callback)

        return inner

    def listen_broadcast(self, callback=None):
        def inner(func):
            @wraps(func)
            def wrapper(fields: dict):
                result = func(fields)

            self.__broadcast_listener = wrapper
            return wrapper

        if callback is not None:
            return inner(callback)

        return inner

    def main_loop(self, repetitions=None, *, callback=None):
        warnings.warn(
            "main_loop() is deprecated and will be removed in a later version. "
            "You should use on_start() instead",
            DeprecationWarning,
        )
        print_warning(
            "main_loop() is deprecated and will be removed in a later version. "
            "You should use on_start() instead"
        )

        def inner(main_loop_func):
            @wraps(main_loop_func)
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

            self.__on_start = wrapper
            return wrapper

        if callback is not None:
            return inner(callback)

        return inner

    # ################################# Private methods ################################# #

    def __log_info(self, info):
        if self.__log:
            print_log(info, color="grey70")

    def __get_config_value(self, key):
        return self.__config.get(
            self.__name, key, fallback=None
        ) or self.__config.defaults().get(key)

    def __send_event(self, event: ALIVE_IOT_EVENT, data: Optional[dict]):
        if self.__connected:
            data_sent = {"event": event.value, "data": data}
            data_encoded = self.encoder.encode(data_sent)
            self.__log_info(f"[Encoding] {data_sent!r}")
            self.__log_info(f"[Sending] {data_encoded!r}")
            self.__ws.send(data_encoded)
            self.__repeats += 1

    def __execute_listen(self, fields: dict):
        for listener in self.listeners:
            fields_to_return = {
                field: value
                for field, value in fields.items()
                if field in listener["fields"]
            }
            if len(fields_to_return) > 0:
                listener["func"](fields_to_return)

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
            print_err(f"The protocol with the id {msg_id!r} is not implemented")
        else:
            protocol(msg["value"])

    def __connect_success(self):
        if len(self.__listeners) == 0:
            print_success(f"Object {self.name!r}", success_name="Connected")
            self.connected_to_alivecode = True

            self.__on_start and Thread(
                target=self.__on_start[0],
                args=self.__on_start[1],
                kwargs=self.__on_start[2],
                daemon=True,
            ).start()

        else:
            # Register listeners on ALIVEcode
            fields = sorted(
                set([field for l in self.listeners for field in l["fields"]])
            )
            self.__send_event(ALIVE_IOT_EVENT.SUBSCRIBE_LISTENER, {"fields": fields})

    def __subscribe_listener_success(self):
        print_success(success_name="Connected")
        self.connected_to_alivecode = True
        self.__on_start and Thread(
            target=self.__on_start[0],
            args=self.__on_start[1],
            kwargs=self.__on_start[2],
            daemon=True,
        ).start()

    def __handle_error(self, data, terminate: bool = False):
        print_err(data)
        if terminate:
            self.connected_to_alivecode = False
            print_fail(failure_name="Connection closed due to an error")

    # ################################# Websocket methods ################################# #

    def __on_message(self, ws, message):
        msg = self.decoder.decode(message)

        event: str = msg["event"]
        data = msg["data"]

        if event == ALIVE_IOT_EVENT.CONNECT_SUCCESS.value:
            self.__connect_success()

        elif event == ALIVE_IOT_EVENT.RECEIVE_ACTION.value:
            self.__execute_protocol(data)

        elif event == ALIVE_IOT_EVENT.RECEIVE_LISTEN.value:
            self.__execute_listen(data["fields"])

        elif event == ALIVE_IOT_EVENT.RECEIVE_BROADCAST.value:
            self.__execute_broadcast(data["data"])

        elif event == ALIVE_IOT_EVENT.SUBSCRIBE_LISTENER_SUCCESS.value:
            self.__subscribe_listener_success()

        elif event == ALIVE_IOT_EVENT.ERROR.value:
            if data == "Forbidden. Invalid credentials.":
                self.__handle_error(data, True)
            elif "is not registered" in data:
                self.__handle_error(data, True)
            else:
                self.__handle_error(data)

        elif event == ALIVE_IOT_EVENT.PING.value:
            self.__send_event(ALIVE_IOT_EVENT.PONG, None)

    def __on_error(self, ws: WebSocketApp, error):
        print_err(f"{error!r}")
        
        if isinstance(error, KeyboardInterrupt):
            self.__stopped = True
        
        if isinstance(error, ConnectionResetError):
            print_warning(
                "If you didn't see the 'Connected', "
                "message verify that you are using the right key"
            )

    def __on_close(self, ws: WebSocketApp, status_code, msg):
        self.__connected = False
        self.__connected_to_alivecode = False
        self.__on_end and self.__on_end[0](*self.__on_end[1], **self.__on_end[2])

        if status_code is not None or msg is not None:
            if status_code is not None:
                print_fail(failure_name="Status code : %s" % status_code)
            if msg is not None:
                print_fail(failure_name="Message : %s" % msg)
            print_fail(failure_name="Connection closed")
        
        else:
            print_info(info_name="Connection closed")


    def __on_open(self, ws):
        # Register IoTObject on ALIVEcode
        self.__connected = True
        self.retry_connection_amount = 0
        token = self.auth_token
        if token is None:
            self.__handle_error(
                "IoTObjects now require an AuthToken to securely connect to ALIVEiot. Please make sure to register an AuthToken on your IoTObject on ALIVEcode from your IoT Dashboard and add in your config.ini: auth_token = <your_auth_token>",
                terminate=True,
            )
        else:
            self.__send_event(
                ALIVE_IOT_EVENT.CONNECT_OBJECT,
                {"id": self.object_id, "token": self.auth_token},
            )
        # if self.__main_loop is None:
        #     self.__ws.close()
        #     raise NotImplementedError("You must define a main loop")
        # Thread(target=self.__main_loop, daemon=True).start()

    def __setup_ws(self, enable_trace: bool = False):
        print_info("...", info_name="Connecting")
        websocket.enableTrace(enable_trace)
        self.__ws = WebSocketApp(
            self.__ws_url,
            on_open=self.__on_open,
            on_message=self.__on_message,
            on_error=self.__on_error,
            on_close=self.__on_close,
        )
        self.__ws.run_forever()
