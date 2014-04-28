
def mul(x, y):
    '''
    >>> mul(2, 4)
    8
    '''
    return x * y

class addcls:
    """
    >>> x = addcls(5)
    >>> x + 3
    >>> x.x
    8
    """
    def __init__(self, x):
        self.x = x

    def __add__(self, y):
        self.x += y

if __name__ == "__main__":
    import doctest
    from pygaga.helpers.logger import log_init
    log_init()
    doctest.testmod(verbose=True)
