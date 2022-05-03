
class AliotDocument(dict):
    def __init__(self):
        super().__init__()

    def __delitem__(self, key):
        super(AliotDocument, self).__delitem__(key)
        # post to delete item in server



doc = AliotDocument()

doc["idk"] = 3

del doc["idk"]

