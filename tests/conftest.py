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

pytest.AUTHOR = 'A. Uthor'
pytest.BACKEND_HOST = ('file-system', os.path.join(pytest.ROOT, 'host'))
pytest.CACHE_ROOT = os.path.join(pytest.ROOT, 'cache')
pytest.DATE = datetime.datetime.now()
pytest.ID = audeer.uid()
pytest.META = {
    'data': {
        'emodb': {
            'version': '1.0.0',
            'format': 'wav',
            'mixdown': True,
        }
    },
    'feature': {
        'win_dur': '32ms',
        'hop_dur': '10ms',
        'num_fft': 512,
        'num_bands': 64,
    }
}
pytest.MODEL_ROOT = audeer.mkdir(os.path.join(pytest.ROOT, pytest.ID, 'model'))
pytest.NAME = 'test'
pytest.PARAMS = {
    'sampling_rate': 16000,
    'feature': 'spectrogram',
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
