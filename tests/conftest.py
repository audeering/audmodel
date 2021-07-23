import datetime
import glob
import os
import shutil

import pytest

import audbackend
import audeer


pytest.ROOT = audeer.mkdir(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        audeer.uid(),
    )
)

pytest.AUTHOR = 'Calvin and Hobbes'
pytest.CACHE_ROOT = os.path.join(pytest.ROOT, 'cache')
pytest.DATE = datetime.date(1985, 11, 18)
pytest.HOST = os.path.join(pytest.ROOT, 'host')
pytest.ID = audeer.uid()
pytest.META = {
    '1.0.0': {
        'data': {
            'emodb': {
                'version': '1.0.0',
                'format': 'wav',
                'mixdown': True,
            }
        },
        'melspec64': {
            'win_dur': '32ms',
            'hop_dur': '10ms',
            'num_fft': 512,
        },
        'cnn10': {
            'learning-rate': 1e-3,
            'optimizer': 'sgd',
        }
    },
    '2.0.0': {
        'data': {
            'emodb': {
                'version': '1.1.1',
                'format': 'wav',
                'mixdown': True,
            }
        },
        'melspec64': {
            'win_dur': '32ms',
            'hop_dur': '10ms',
            'num_fft': 512,
        },
        'cnn10': {
            'learning-rate': 1e-3,
            'optimizer': 'sgd',
        }
    },
    '3.0.0': {
        'data': {
            'emodb': {
                'version': '1.1.1',
                'format': 'wav',
                'mixdown': True,
            }
        },
        'melspec64': {
            'win_dur': '32ms',
            'hop_dur': '10ms',
            'num_fft': 512,
        },
        'cnn10': {
            'learning-rate': 1e-2,
            'optimizer': 'adam',
        }
    }
}
pytest.MODEL_ROOT = audeer.mkdir(os.path.join(pytest.ROOT, pytest.ID, 'model'))
pytest.NAME = 'test'
pytest.PARAMS = {
    'feature': 'melspec64',
    'model': 'cnn10',
    'sampling_rate': 16000,
}
pytest.REPOSITORIES = [
    audbackend.Repository(
        'repo1',
        pytest.HOST,
        'file-system',
    ),
    audbackend.Repository(
        'repo2',
        pytest.HOST,
        'file-system',
    ),
]


# create object that cannot be pickled
# so it will raise an error when converted to yaml
class CannotPickle:
    def __getstate__(self):
        raise Exception('cannot pickle object')


pytest.CANNOT_PICKLE = CannotPickle()


@pytest.fixture(scope='session', autouse=True)
def cleanup_session():
    path = os.path.join(
        pytest.ROOT,
        '..',
        '.coverage.*',
    )
    for file in glob.glob(path):
        os.remove(file)
    yield
    if os.path.exists(pytest.ROOT):
        shutil.rmtree(pytest.ROOT)
