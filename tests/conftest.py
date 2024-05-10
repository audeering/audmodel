import datetime
import glob
import os
import shutil

import pytest

import audeer

import audmodel


pytest.ROOT = audeer.mkdir(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        audeer.uid(),
    )
)

pytest.NAME = "torch"
pytest.PARAMS = {
    "model": "cnn10",
    "data": "emodb",
    "feature": "melspec",
    "sampling_rate": 16000,
}
pytest.AUTHOR = "Calvin and Hobbes"
pytest.CACHE_ROOT = os.path.join(pytest.ROOT, "cache")
pytest.DATE = datetime.date(1985, 11, 18)
pytest.HOST = os.path.join(pytest.ROOT, "host")
pytest.ID = audeer.uid()
pytest.META = {
    "1.0.0": {
        "data": {
            "emodb": {"version": "1.2.0"},
        },
        "feature": {
            "melspec": {
                "win_dur": "32ms",
                "hop_dur": "10ms",
                "num_fft": 512,
                "mel_bins": 64,
            },
        },
        "model": {
            "cnn10": {
                "learning-rate": 1e-3,
                "optimizer": "sgd",
            },
        },
    },
    "2.0.0": {
        "data": {
            "emodb": {"version": "1.2.0"},
        },
        "feature": {
            "melspec": {
                "win_dur": "64ms",
                "hop_dur": "32ms",
                "num_fft": 1024,
                "mel_bins": 64,
            },
        },
        "model": {
            "cnn10": {
                "learning-rate": 1e-3,
                "optimizer": "sgd",
            },
        },
    },
    "3.0.0": {
        "data": {
            "emodb": {"version": "1.2.0"},
        },
        "feature": {
            "melspec": {
                "win_dur": "32ms",
                "hop_dur": "10ms",
                "num_fft": 512,
                "mel_bins": 64,
            },
        },
        "model": {
            "cnn10": {
                "learning-rate": 1e-2,
                "optimizer": "adam",
            },
        },
    },
}
pytest.MODEL_ROOT = audeer.mkdir(os.path.join(pytest.ROOT, pytest.ID, "model"))
pytest.REPOSITORIES = [
    audmodel.Repository("repo1", pytest.HOST, "file-system"),
    audmodel.Repository("repo2", pytest.HOST, "file-system"),
]
audeer.mkdir(audeer.path(pytest.HOST, "repo1"))
audeer.mkdir(audeer.path(pytest.HOST, "repo2"))


# create object that cannot be pickled
# so it will raise an error when converted to yaml
class CannotPickle:
    def __getstate__(self):
        r"""Check if object can be pickled."""
        raise Exception("cannot pickle object")


pytest.CANNOT_PICKLE = CannotPickle()


@pytest.fixture(scope="session", autouse=True)
def cleanup_session():
    path = os.path.join(
        pytest.ROOT,
        "..",
        ".coverage.*",
    )
    for file in glob.glob(path):
        os.remove(file)
    yield
    if os.path.exists(pytest.ROOT):
        shutil.rmtree(pytest.ROOT)


@pytest.fixture(scope="function", autouse=False)
def non_existing_repository():
    repository = audmodel.Repository("repo", "non-existing", "file-system")
    current_repositories = audmodel.config.REPOSITORIES
    audmodel.config.REPOSITORIES = [repository]

    yield repository

    audmodel.config.REPOSITORIES = current_repositories
