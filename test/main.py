from aliot.aliot_obj import AliotObj
from test_state import TestState
from time import sleep

test = AliotObj("test")

# the state of your object should be defined in this class
test_state = TestState()


# write your listeners and receivers here


def start():
    # write the code you want to execute once your object is connected to the server
    sleep(5)
    test.stop()


def end():
    # write the code you want to execute once your object is disconnected from the server
    pass


test.on_start(callback=start)
test.on_end(callback=end)
test.run()  # connects your object to the sever
