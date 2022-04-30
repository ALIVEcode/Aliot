from aliot_old import alive_iot as iot

lumiere = iot.ObjConnecteAlive("ef4228d0-8e4e-4ec6-ab7e-7618d588f94e")
iot.ObjConnecteAlive.set_url("ws://localhost:8881")

@lumiere.on_recv(12)
def afficher_data(data):
    print(data)

@lumiere.main_loop(10)
def main():
    pass


lumiere.begin()


def abc():
    run = True
    while run:
        yield True
    yield False

a = abc()


# iot.ObjConnecteAlive.set_url("ws://localhost:8881/")
# @feu.on_recv(action_id=FEU_ROUGE)
# def change_lum_rouge(_):
#     set_lum("rouge")
#
#
# @feu.on_recv(action_id=FEU_JAUNE)
# def change_lum_jaune(_):
#     set_lum("jaune")
#
#
# @feu.on_recv(action_id=FEU_VERT)
# def change_lum_vert(_):
#     set_lum("vert")
#