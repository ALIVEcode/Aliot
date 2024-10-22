def minimal_template(obj_name: str, path: str):
    variable = obj_name.replace('-', '_')
    return f"""# Documentation: https://alivecode.ca/docs/aliot
from aliot.aliot_obj import AliotObj

# Création de l'objet à partir du fichier de configuration
{variable} = AliotObj("{obj_name}")

# Écrivez votre code ici

# Connection de l'objet au serveur ALIVEcode
{variable}.run()
"""


def normal_template(obj_name: str, path: str):
    variable = obj_name.replace('-', '_')
    return f"""# Documentation: https://alivecode.ca/docs/aliot
from aliot.aliot_obj import AliotObj

# Création de l'objet à partir du fichier de configuration
{variable} = AliotObj("{obj_name}")


def start():
    # Écrivez le code que vous voulez exécuter une fois que l'objet
    # est connecté au serveur
    pass


# Appel de la fonction start une fois que l'objet se connecte au serveur
{variable}.on_start(callback=start)

# Connection de l'objet au serveur ALIVEcode
{variable}.run()
"""


def complete_template(obj_name: str, path: str):
    variable = obj_name.replace('-', '_')
    capitalized = "".join(letter.capitalize() for letter in variable.split("_"))

    with open(f"{path}/{variable}_state.py", "w+", encoding="utf-8") as f:
        f.write(f"""from dataclasses import dataclass
from aliot.state import AliotObjState


@dataclass
class {capitalized}State(AliotObjState):
    # Écrivez ici les attributs de l'objet
    pass
""")

    return f"""# Documentation: https://alivecode.ca/docs/aliot
from aliot.aliot_obj import AliotObj
from {variable}_state import {capitalized}State

# Création de l'objet à partir du fichier de configuration
{variable} = AliotObj("{obj_name}")

# L'état de l'objet devrait être défini dans cette classe
{variable}_state = {capitalized}State()


def start():
    # Écrivez le code que vous voulez exécuter une fois que l'objet
    # est connecté au serveur
    pass


def end():
    # Écrivez le code que vous voulez exécuter une fois que l'objet
    # est déconnecté du serveur
    pass


# Appel de la fonction start une fois que l'objet se connecte au serveur
{variable}.on_start(callback=start)
# Appel de la fonction end une fois que l'objet se déconnecte du serveur
{variable}.on_end(callback=end)

# Connection de l'objet au serveur ALIVEcode
{variable}.run()
"""


def blank_template(obj_name: str, path: str):
    return ""


__templates = {
    "minimal": minimal_template,
    "normal": normal_template,
    "complete": complete_template,
    "blank": blank_template,
}

def from_template(template_name: str, obj_name: str, path: str):
    if template_name not in __templates:
        raise ValueError(f"Unknown template {template_name}")
    return __templates[template_name](obj_name, path)
