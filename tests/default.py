import os


class default:

    ROOT = os.path.dirname(os.path.realpath(__file__))
    NAME = 'audmodel'
    COLUMNS = ['property1', 'property2', 'property3']
    PARAMS = [
        {
            'property1': 'foo',
            'property2': 'bar',
            'property3': idx,
        } for idx in range(3)
    ]
    VERSION = '1.0.0'
