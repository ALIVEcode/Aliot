def minimal_template(obj_name: str):
    variable = obj_name.replace('-', '_')
    return f"""from aliot.aliot_obj import AliotObj

{variable} = AliotObj("{obj_name}")

# write your code here

{variable}.run()
"""


def normal_template(obj_name: str):
    variable = obj_name.replace('-', '_')
    return f"""from aliot.aliot_obj import AliotObj

{variable} = AliotObj("{obj_name}")


# write your listeners and receivers here


def start():
    # write the code you want to execute once your object is connected to the server
    pass


{variable}.on_start(callback=start)
{variable}.run()
"""


def complete_template(obj_name: str, path: str):
    variable = obj_name.replace('-', '_')
    capitalized = "".join(letter.capitalize() for letter in variable.split("_"))

    with open(f"{path}/{variable}_state.py", "w+") as f:
        f.write(f"""from dataclasses import dataclass
from aliot.state import AliotObjState


@dataclass
class {capitalized}State(AliotObjState):
    # write the different properties of your object
    pass
""")

    return f"""from aliot.aliot_obj import AliotObj
from {variable}_state import {capitalized}State

{variable} = AliotObj("{obj_name}")

# the state of your object should be defined in this class
{variable}_state = {capitalized}State()


# write your listeners and receivers here


def start():
    # write the code you want to execute once your object is connected to the server
    pass


def end():
    # write the code you want to execute once your object is disconnected from the server
    pass


{variable}.on_start(callback=start)
{variable}.on_end(callback=end)
{variable}.run()  # connects your object to the sever
"""


def blank_template():
    return ""


def from_template(template_name: str, obj_name: str, path: str):
    match template_name:
        case "minimal":
            return minimal_template(obj_name)
        case "normal":
            return normal_template(obj_name)
        case "complete":
            return complete_template(obj_name, path)
        case "blank" | _:
            return blank_template()
