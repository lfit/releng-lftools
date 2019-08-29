class UnsupportedRequestType(Exception):
    def __str__(self):
        return "Unknown request type"
