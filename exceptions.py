""" Custom-made Exceptions for the program. """

class LoginException(Exception):
    """ Raises if incorrect credentials given for login. """
    def __init__(self, msg=''):
        super().__init__(msg)

class LetterboxdException(Exception):
    """ Exceptions that relate to the site itself.
    e.g. cannot create comment on private list.
    """
    def __init__(self, msg=''):
        super().__init__(msg)
