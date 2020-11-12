
class A():

    def __init__(self):
        self.func()

    def func(self):
        print("Hi")



class B(A):

    def __init__(self):
        super().__init__()

    def func(self):
        print("BYE")


B()