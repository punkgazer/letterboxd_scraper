""" Custom-made Exceptions for the program. """

class LoginException(Exception):
    """ Raises if incorrect credentials given for login. """
    def __init__(self, msg=''):
        super().__init__(msg)

class LetterboxdException(Exception):
    """ Raises if valid Letterboxd exception found. """
    def __init__(self, msg=''):
        super().__init__(msg)
