from typing import Callable, List, Optional, Union
from threading import Thread
import json, requests, websocket
from aliot.aliot.utils import IOT_EVENT, Style
from itertools import chain

style_print = Style.style_print


class URLNotDefinedException(Exception):
    """Exception raised when a new ObjConnecte instance is created and __URL is not defined"""

class InvalidURLException(Exception):
    """Exception raised when a setting an invalid URL"""


_no_value = object()


class ObjConnecteAlive:
    __URL = 'wss://alivecode.ca/iotgateway/'
    __API_URL = 'https://alivecode.ca/api'

    # nb de request max par interval (en ms)
    __bottleneck_capacity = {"max_send": 30,
                             "interval": 500, "sleep_interval": 0.2}

    @classmethod
    def set_url(cls, url: str):
        cls.__URL = url
    
    @classmethod
    def set_api_url(cls, api_url: str):
        cls.__API_URL = api_url[:-1] if api_url.endswith('/') else api_url

    def __new__(cls, *args, **kwargs):
        if not cls.__URL:
            raise URLNotDefinedException(
                "You must define a URL before creating an ObjConnecte, call ObjConnecte.set_url(url) with your url before creating any instance of that class"
            )
        return super().__new__(cls)

    def __init__(self, object_id: str):
        if not isinstance(object_id, str):
            raise ValueError("the value of id_ must be a string")
        self.__id = object_id
        self.__protocols = {}
        self.__listeners = []
        self.__broadcast_listener: Optional[Callable[[dict], None]] = None
        self.__connected_to_alivecode = False
        self.__connected = False
        self.ws: websocket.WebSocketApp  = None
        self.__main_loop = None
        self.__repeats = 0
        self.__last_freeze = 0
        self.__listeners_set = 0

    @property
    def protocols(self):
        return self.__protocols.copy()

    @property
    def listeners(self):
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
        if not value:
            self.ws.close()

    def on_recv(self, action_id: int, log_reception: bool = True,):
        def inner(func):
            def wrapper(*args, **kwargs):
                if log_reception:
                    print(f"The protocol: {action_id!r} was called with the arguments: "
                          f"{args}")
                res = func(*args, **kwargs)
                self.__send_event(IOT_EVENT.SEND_ACTION_DONE, {
                    "actionId": action_id,
                    "value": res
                })

            self.__protocols[action_id] = wrapper
            return wrapper

        return inner

    def listen(self, fields: List[str]):
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

    def update_component(self, id: str,  value):
        self.__send_event(IOT_EVENT.UPDATE_COMPONENT, {
                       'id': id, 'value': value
                       })

    def broadcast(self, data: dict):
        self.__send_event(IOT_EVENT.SEND_BROADCAST, {
                       'data': data
                       })

    def update_doc(self,fields: dict):
        self.__send_event(IOT_EVENT.UPDATE_DOC, {
                       'fields': fields,
                       })

    def get_doc(self, field: Union[str, None] = None):
        if field:
            res = requests.post(f'{self.__API_URL}/iot/aliot/{IOT_EVENT.GET_FIELD.value[0]}', { 'id': self.__id, 'field': field})
            if res.status_code == 201:
                return json.loads(res.text) if res.text else None
            elif res.status_code == 403:
                style_print(f"&c[ERROR] while getting the field {field}, request was Forbidden due to permission errors or project missing.")
            elif res.status_code == 500:
                style_print(f"&c[ERROR] while getting the field {field}, something went wrong with the ALIVECode's servers, please try again.")
            else:
                style_print(f"&c[ERROR] while getting the field {field}, please try again. {res.json()}")
        else:
            res = requests.post(f'{self.__API_URL}/iot/aliot/{IOT_EVENT.GET_DOC.value[0]}', { 'id': self.__id})
            if res.status_code == 201:
                return json.loads(res.text) if res.text else None
            elif res.status_code == 403:
                style_print(f"&c[ERROR] while getting the document, request was Forbidden due to permission errors or project missing.")
            elif res.status_code == 500:
                style_print(f"&c[ERROR] while getting the document, something went wrong with the ALIVECode's servers, please try again.")
            else:
                style_print(f"&c[ERROR] while getting the document, please try again. {res.json()}")


    def send_route(self, routePath: str, data: dict):
        self.__send_event(IOT_EVENT.SEND_ROUTE, {
            'routePath': routePath,
            'data': data
        })

    def send_action(self, targetId: str, actionId: int, value=""):
        self.__send_event(IOT_EVENT.SEND_ACTION, {
            'targetId': targetId,
            'actionId': actionId,
            'value': value
        })

    def __send_event(self, event: IOT_EVENT, data: Union[dict, None]):

        """
        if self.__last_freeze and time.time() - self.__last_freeze > self.__bottleneck_capacity["interval"]:
            self.__repeats = 0
            self.__last_freeze = None
            style_print(f"&2[RESUMING]")


        if self.__repeats > self.__bottleneck_capacity["max_send"]:
            style_print(f"&6[WARNING] You are sending more than {self.__bottleneck_capacity['max_send']} requests in under {self.__bottleneck_capacity['interval']}ms. Sending of data slowed down.")
            
            if self.__last_freeze is None:
                self.__last_freeze = time.time()

            time.sleep(self.__bottleneck_capacity["sleep_interval"])

        """
        if self.__connected:
            self.ws.send(json.dumps({'event': event.value[0], 'data': data}, default=str))
            self.__repeats += 1

    def __execute_protocol(self, msg):
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
            style_print(
                f"&c[ERROR] the protocol with the id {msg_id!r} is not implemented")

            # magic of python
            style_print("&l[CLOSED]")
        else:
            protocol(msg["value"])

    def __execute_listen(self, fields: dict):
        for listener in self.listeners:
            fieldsToReturn = dict(filter(lambda el: el[0] in listener['fields'], fields.items()))
            if len(fieldsToReturn) > 0:
                listener["func"](fieldsToReturn)


    def __execute_broadcast(self, data: dict):
        if self.broadcast_listener:
            self.broadcast_listener(data)


    def __on_message(self, ws, message):
        msg = json.loads(message)

        event: IOT_EVENT = msg['event']
        data = msg['data']

        if event == IOT_EVENT.RECEIVE_ACTION.value[0]:
            if isinstance(data, list):
                for m in data:
                    self.__execute_protocol(m)
            else:
                self.__execute_protocol(data)
        elif event == IOT_EVENT.RECEIVE_LISTEN.value[0]:
            self.__execute_listen(data['fields'])
        elif event == IOT_EVENT.RECEIVE_BROADCAST.value[0]:
            self.__execute_broadcast(data['data'])
        elif event == IOT_EVENT.CONNECT_SUCCESS.value[0]:
            
            if len(self.__listeners) == 0:
                style_print("&a[CONNECTED]")
                self.connected_to_alivecode = True
            else:
                # Register listeners on ALIVEcode
                fields = sorted(set([field for l in self.listeners for field in l['fields']]))
                self.__send_event(IOT_EVENT.SUBSCRIBE_LISTENER, { 'fields': fields })
        elif event == IOT_EVENT.SUBSCRIBE_LISTENER_SUCCESS.value[0]:
            self.__listeners_set += 1
            if self.__listeners_set == len(self.__listeners):
                style_print("&a[CONNECTED]")
                self.connected_to_alivecode = True
        elif event == IOT_EVENT.ERROR.value[0]:
            style_print(f"&c[ERROR] {data}")
        elif event == IOT_EVENT.PING.value[0]:
            self.__send_event(IOT_EVENT.PONG, None)
        

    def __on_error(self, ws, error):
        style_print(f"&c[ERROR]{error!r}")
        if isinstance(error, ConnectionResetError):
            style_print("&eWARNING: if you didn't see the '&a[CONNECTED]'&e, "
                        "message verify that you are using the right key")

    def __on_close(self, ws):
        self.__connected_to_alivecode = False
        self.__connected = False
        style_print("&l[CLOSED]")

    def __on_open(self, ws):
        # Register IoTObject on ALIVEcode
        self.__connected = True
        self.__send_event(IOT_EVENT.CONNECT_OBJECT, {'id': self.__id})

        if self.__main_loop is None:
            self.ws.close()
            raise NotImplementedError("You must define a main loop")

        Thread(target=self.__main_loop, daemon=True).start()


    def begin(self, enable_trace: bool = False):
        style_print("&9[CONNECTING]...")
        websocket.enableTrace(enable_trace)
        self.ws = websocket.WebSocketApp(self.__URL,
                                         on_open=self.__on_open,
                                         on_message=self.__on_message,
                                         on_error=self.__on_error,
                                         on_close=self.__on_close)
        self.ws.run_forever()

    def __repr__(self):
        return f"connection_key: {self.__id}"
