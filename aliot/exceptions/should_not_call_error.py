class ShouldNotCallError(Exception):
    def __init__(self, msg: str = ""):
        super(ShouldNotCallError, self).__init__(msg)

    @staticmethod
    def wrap_do_not_call_error(msg: str):
        return lambda *a, **k: ShouldNotCallError(msg).__raise()

    def __raise(self):
        raise self
