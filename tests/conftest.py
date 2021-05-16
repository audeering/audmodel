import datetime
import glob
import os
import shutil

import pytest

import audeer


pytest.ROOT = audeer.mkdir(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'tmp',
    )
)

pytest.AUTHOR = 'Calvin and Hobbes'
pytest.BACKEND_HOST = ('file-system', os.path.join(pytest.ROOT, 'host'))
pytest.CACHE_ROOT = os.path.join(pytest.ROOT, 'cache')
pytest.DATE = datetime.date(1985, 11, 18)
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
        'spectrogram': {
            'win_dur': '32ms',
            'hop_dur': '10ms',
            'num_fft': 512,
            'num_bands': 64,
        },
        'cnn': {
            'type': 'pann',
            'layers': 10,
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
        'spectrogram': {
            'win_dur': '32ms',
            'hop_dur': '10ms',
            'num_fft': 512,
            'num_bands': 64,
        },
        'cnn': {
            'type': 'pann',
            'layers': 10,
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
        'spectrogram': {
            'win_dur': '32ms',
            'hop_dur': '10ms',
            'num_fft': 512,
            'num_bands': 64,
        },
        'cnn': {
            'type': 'pann',
            'layers': 14,
        }
    }
}
pytest.MODEL_ROOT = audeer.mkdir(os.path.join(pytest.ROOT, pytest.ID, 'model'))
pytest.NAME = 'test'
pytest.PARAMS = {
    'feature': 'spectrogram',
    'model': 'cnn',
    'sampling_rate': 16000,
}


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
