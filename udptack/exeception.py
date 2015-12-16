#author: plasmashadow


class TrackerException(Exception):
    """Base class for all Tracker Exceptions"""

    mode = 'tracker'

    def __init__(self, message, data):
        self.message = message
        self.data = data

    def __repr__(self):
        return "<%s=>%s>%s:%s"%(self.__class__.__name__, self.mode, self.message, str(self.data))


class TrackerRequestException(TrackerException):
    """Exception that occures on tracker reqeust"""
    mode = "request"


class TrackerResponseException(TrackerException):
    """Exception that occures on tracker response"""
    mode = "response"