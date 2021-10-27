class IntFile:
    """
    Represents an .INT file in a PaRappa The Rapper 2 ISO.
    """
    def __init__(self, data: bytes):
        self.data: bytes = data
