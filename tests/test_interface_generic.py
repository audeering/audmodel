import os

import audiofile as af
import numpy as np
import pandas as pd
import pytest

import audmodel


# Different process_func
def signal_duration(signal, sampling_rate):
    return signal.shape[1] / sampling_rate


def signal_max(signal, sampling_rate):
    return np.max(signal)


def signal_modification(signal, sampling_rate, subtract=False):
    if subtract:
        signal -= 0.1 * signal
    else:
        signal += 0.1 * signal
    return signal


@pytest.mark.parametrize(
    'model_process_func,signal,selected_channel,expected_output',
    [
        (
            signal_max,
            np.ones((1, 3)),
            None,
            1,
        ),
        (
            signal_max,
            np.ones(3),
            0,
            1,
        ),
        (
            signal_max,
            np.array([[0., 0., 0.], [1., 1., 1.]]),
            0,
            0,
        ),
        (
            signal_max,
            np.array([[0., 0., 0.], [1., 1., 1.]]),
            1,
            1,
        ),
        pytest.param(
            signal_max,
            np.ones((1, 3)),
            1,
            1,
            marks=pytest.mark.xfail(raises=ValueError),
        ),
    ],
)
def test_channel(
        tmpdir,
        model_process_func,
        signal,
        selected_channel,
        expected_output,
):
    sampling_rate = 8000
    model = audmodel.interface.Generic(
        process_func=model_process_func,
        sampling_rate=sampling_rate,
        resample=False,
        verbose=False,
    )
    path = str(tmpdir.mkdir('wav'))
    filename = f'{path}/channel.wav'
    af.write(filename, signal, sampling_rate)
    output = model.process_file(filename, channel=selected_channel)
    np.testing.assert_almost_equal(output, expected_output, decimal=4)


def test_folder(tmpdir):
    model = audmodel.interface.Generic(
        process_func=lambda signal, sampling_rate: signal,
        sampling_rate=None,
        resample=False,
        verbose=False,
    )
    sampling_rate = 8000
    signal = np.ones((1, 8000))
    path = str(tmpdir.mkdir('wav'))
    files = [f'{path}/file{n}.wav' for n in range(3)]
    for file in files:
        af.write(file, signal, sampling_rate)
    model.process_folder(path)


@pytest.mark.parametrize(
    'process_func,process_func_kwargs,signal,sampling_rate,expected_signal',
    [
        (
            None,
            {},
            np.array([1., 2., 3.]),
            44100,
            np.array([1., 2., 3.]),
        ),
        (
            signal_max,
            {},
            np.array([1., 2., 3.]),
            44100,
            3.0,
        ),
        (
            signal_duration,
            {},
            np.array([1., 2., 3.]),
            3,
            1.0,
        ),
        (
            signal_modification,
            {},
            np.array([1., 1., 1.]),
            44100,
            np.array([[1.1, 1.1, 1.1]]),
        ),
        (
            signal_modification,
            {'subtract': False},
            np.array([1., 1., 1.]),
            44100,
            np.array([[1.1, 1.1, 1.1]]),
        ),
        (
            signal_modification,
            {'subtract': True},
            np.array([1., 1., 1.]),
            44100,
            np.array([[0.9, 0.9, 0.9]]),
        ),
    ],
)
def test_process_func(
        process_func,
        process_func_kwargs,
        signal,
        sampling_rate,
        expected_signal,
):
    model = audmodel.interface.Generic(
        process_func=process_func,
        sampling_rate=None,
        resample=False,
        verbose=False,
        **process_func_kwargs,
    )
    predicted_signal = model.process_signal(signal, sampling_rate)
    np.array_equal(predicted_signal, expected_signal)


def test_read_audio(tmpdir):
    # Currently the start and end options
    # of audmodel.interface.Generic.read_audio() are not covered
    # by the interface usage
    # as they are only need for process_index()
    sampling_rate = 8000
    signal = np.ones((1, 8000))
    path = str(tmpdir.mkdir('wav'))
    file = os.path.join(path, 'file.wav')
    af.write(file, signal, sampling_rate)
    s, sr = audmodel.interface.Generic.read_audio(
        file,
        start=pd.Timedelta('00:00:00.1'),
        end=pd.Timedelta('00:00:00.2'),
    )
    assert sr == sampling_rate
    assert s.shape[1] == 0.1 * sr


@pytest.mark.parametrize(
    'signal_sampling_rate,model_sampling_rate,resample',
    [
        pytest.param(
            44100,
            None,
            True,
            marks=pytest.mark.xfail(raises=ValueError),
        ),
        (
            44100,
            44100,
            True,
        ),
        (
            44100,
            44100,
            False,
        ),
        pytest.param(
            48000,
            44100,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        (
            4,
            3,
            True,
        ),
    ],
)
def test_sampling_rate_mismatch(
        signal_sampling_rate,
        model_sampling_rate,
        resample,
):
    model = audmodel.interface.Generic(
        process_func=lambda signal, sampling_rate: signal,
        sampling_rate=model_sampling_rate,
        resample=resample,
        verbose=False,
    )
    signal = np.array([1., 2., 3.])
    model.process_signal(signal, signal_sampling_rate)
