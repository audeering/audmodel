import os


class config:

    ROOT = os.path.dirname(os.path.realpath(__file__))
    NAME = 'audfactory'
    DEFAULT_COLUMNS = ['property1', 'property2', 'property3']
    DEFAULT_PARAMS = [
        {
            'property1': 'foo',
            'property2': 'bar',
            'property3': idx,
        } for idx in range(3)
    ]
    DEFAULT_VERSION = '1.0.0'
