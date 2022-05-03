class ShouldNotCallError(Exception):
    def __init__(self, msg: str = ""):
        super(ShouldNotCallError, self).__init__(msg)
