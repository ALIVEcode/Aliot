from enum import Enum


class Style:
    styles = {
        "0": "\033[30m",                # BLACK
        "1": "\033[38;2;0;0;128m",      # DARK_BLUE
        "2": "\033[38;2;0;100;0m",      # DARK_GREEN
        "3": "\033[38;2;0;128;128m",    # DARK_CYAN
        "4": "\033[38;2;200;0;0m",      # DARK_RED
        "5": "\033[38;2;128;0;128m",    # DARK_PURPLE
        "6": "\033[1;33m",              # GOLD
        "7": "\033[0;37m",              # LIGHT_GRAY
        "8": "\033[38;2;25;25;25m",     # DARK_GRAY
        "9": "\033[1;34m",              # BLUE
        "a": "\033[0;32m",              # GREEN
        "b": "\033[1;36m",              # CYAN
        "c": "\033[1;31m",              # RED
        "d": "\033[1;35m",              # LIGHT_PURPLE
        "e": "\033[38;2;255;255;0m",    # YELLOW
        "f": "\033[38;2;255;255;255m",  # WHITE

        "r": '\033[0m',    # RESET
        "l": '\033[1m',    # BOLD
        "n": '\033[4m',    # UNDERLINE
        "o": '\033[3m',    # ITALIC
        "&": "&",          # &
    }
    WARNING = "&e"
    ERROR = "&c"
    OK = "&a"
    PENDING = "&9"

    @staticmethod
    def stylize(msg: str, reset_style=True) -> str:
        msg += "&r" if reset_style else ""
        for pattern, style in Style.styles.items():
            msg = msg.replace("&" + pattern, style)
        return msg

    @staticmethod
    def style_print(*args, sep=' ', end='\n', file=None, reset_style=True):
        args = [Style.stylize(arg, reset_style) if isinstance(arg, str) else arg for arg in args]
        print(*args, sep=sep, end=end, file=file)

class IOT_EVENT(Enum):
  #---------- Connection events ----------#

  #* Connect as watcher (web view) #
  CONNECT_WATCHER = 'connect_watcher',
  #* Connect as IoTObject (arduino, raspberrpi, etc.) #
  CONNECT_OBJECT = 'connect_object',
  #* Connect IoTObject to a project #
  CONNECT_PROJECT = 'connect_project',
  #* Connect IoTObject to a project #
  DISCONNECT_PROJECT = 'disconnect_project',
  #* Connect object as watcher #
  CONNECT_SUCCESS = 'connect_success',
  #* PING #
  PING = 'ping',
  #* PONG #
  PONG = 'pong',

  #---------- Document Events ----------#

  #* Update project document #
  UPDATE_DOC = 'update_doc',
  #* Receive updated doc #
  RECEIVE_DOC = 'receive_doc',
  #* Subscribe a listener to a project #
  SUBSCRIBE_LISTENER = 'subscribe_listener',
  #* Unsubscribe a listener to a project #
  UNSUBSCRIBE_LISTENER = 'unsubscribe_listener',
  #* Callback when the subscription to a listener worked #
  SUBSCRIBE_LISTENER_SUCCESS = 'subscribe_listener_success',
  #* Callback when the unsubscription to a listener worked #
  UNSUBSCRIBE_LISTENER_SUCCESS = 'subscribe_listener_success',
  #* Receives a listen callback #
  RECEIVE_LISTEN = 'receive_listen',

  #---------- Broadcast Events ----------#

  #* Sendinga broadcast to the other objects connected to the same project #
  SEND_BROADCAST = 'send_broadcast',
  #* Receiving a broadcast from another object connected to the same project #
  RECEIVE_BROADCAST = 'receive_broadcast',

  #---------- Error Events ----------#

  #* When an error occurs #
  ERROR = 'error',

  #---------- Misc Events ----------#

  #* Sending an action to an object #
  SEND_ACTION = 'send_action',
  #* Object receives an action request #
  RECEIVE_ACTION = 'receive_action',
  #* A route of the project is triggered #
  SEND_ROUTE = 'send_route',
  #* Update the interface of an interface #
  UPDATE_INTERFACE = 'update_interface',
  #* Receiveds an updated interface request #
  RECEIVE_INTERFACE = 'receive_interface',

  #---- Deprecated events ----#
  UPDATE_COMPONENT = 'update_component',
  RECEIVE_UPDATE_COMPONENT = 'receive_update_component',

  #---- Http requests ----#

  #* Get the document of a project #
  GET_DOC = 'getDoc',
  #* Get the field of a document of a project #
  GET_FIELD = 'getField',