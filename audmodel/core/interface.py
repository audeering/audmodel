import typing
import pathlib

import audiofile as af
import numpy as np
import pandas as pd

import audeer
import audsp


class Generic:
    r"""Generic model interface.

    Args:
        process_func: processing function,
            which expects the two positional arguments ``signal``
            and ``sampling_rate``
            and any number of additional keyword arguments.
        sampling_rate: sampling rate in Hz.
            If ``None`` it will call ``process_func`` with the actual
            sampling rate of the signal.
        resample: if ``True`` enforces given sampling rate by resampling
        verbose: show debug messages
        kwargs: additional keyword arguments to the processing function

    Raises:
        ValueError: if ``resample = True``, but ``sampling_rate = None``

    """
    def __init__(
            self,
            *,
            process_func: typing.Callable[..., typing.Any] = None,
            sampling_rate: int = None,
            resample: bool = False,
            verbose: bool = False,
            **kwargs,
    ):
        if resample and sampling_rate is None:
            raise ValueError(
                'sampling_rate has to be provided for resample = True.'
            )
        self.sampling_rate = sampling_rate
        self.verbose = verbose
        self.process_func = process_func
        self.process_func_kwargs = kwargs
        if resample:
            self.resample = audsp.Resample(
                sampling_rate=sampling_rate,
                quality=audsp.define.ResampleQuality.HIGH,
            )
        else:
            self.resample = None

    @staticmethod
    def read_audio(
            path: str,
            start: pd.Timedelta = None,
            end: pd.Timedelta = None,
            channel: int = None,
    ) -> typing.Tuple[np.ndarray, int]:
        """Load audio using audiofile."""

        if start is not None:
            offset = start.total_seconds()
        else:
            offset = 0

        if end is not None:
            duration = None if pd.isna(end) else end.total_seconds() - offset
        else:
            duration = None

        # load raw audio
        signal, sampling_rate = af.read(
            path,
            always_2d=True,
            offset=offset,
            duration=duration,
        )

        # mix down
        if channel is not None:
            if channel < 0 or channel >= signal.shape[0]:
                raise ValueError(
                    f'We need 0<=channel<{signal.shape[0]}, '
                    f'but we have channel={channel}.'
                )
            signal = signal[channel, :]

        return signal, sampling_rate

    def process_file(
            self,
            file: str,
            *,
            channel: int = None,
    ) -> typing.Any:
        r"""Process the content of an audio file.

        Args:
            file: file path
            channel: channel number

        Returns:
            output of process function

        Raises:
            RuntimeError: if sampling rates of model and signal do not match

        """
        signal, sampling_rate = self.read_audio(
            file,
            channel=channel,
        )
        return self.process_signal(
            signal,
            sampling_rate,
        )

    def process_files(
            self,
            files: typing.Sequence[str],
            *,
            channel: int = None,
    ) -> typing.Dict[str, typing.Any]:
        r"""Process a list of files.

        Args:
            files: list of file paths
            channel: channel number

        Returns:
            Dictionary mapping files to output of process function

        Raises:
            RuntimeError: if sampling rates of model and signal do not match

        """
        result = {}
        with audeer.progress_bar(
                files,
                total=len(files),
                desc='',
                disable=not self.verbose,
        ) as pbar:
            for file in pbar:
                desc = audeer.format_display_message(file, pbar=True)
                pbar.set_description(desc, refresh=True)
                result[file] = self.process_file(file, channel=channel)
        return result

    def process_folder(
            self,
            root: str,
            *,
            filetype: str = 'wav',
            channel: int = None,
    ) -> typing.Dict[str, typing.Any]:
        r"""Process files in a folder.

        .. note:: At the moment does not scan in sub-folders!

        Args:
            root: root folder
            file_ext: file extension
            channel: channel number

        Returns:
            Dictionary mapping files to output of process function

        Raises:
            RuntimeError: if sampling rates of model and signal do not match

        """
        files = audeer.list_file_names(root, filetype=filetype)
        return self.process_files(files, channel=channel)

    def process_signal(
            self,
            signal: np.ndarray,
            sampling_rate: int,
    ) -> typing.Any:
        r"""Process audio signal and return result.

        Args:
            signal: signal values
            sampling_rate: sampling rate in Hz

        Returns:
            output of process function

        Raises:
            RuntimeError: if sampling rates of model and signal do not match

        """
        # Enforce 2D signals
        signal = np.atleast_2d(signal)
        if (
                self.sampling_rate is not None
                and sampling_rate != self.sampling_rate
        ):
            if self.resample is not None:
                signal = self.resample(signal, sampling_rate)
            else:
                raise RuntimeError(
                    f'Signal sampling rate of {sampling_rate} Hz '
                    f'does not match requested model sampling rate of '
                    f'{self.sampling_rate} Hz.'
                )
        if self.process_func is not None:
            return self.process_func(
                signal,
                sampling_rate,
                **self.process_func_kwargs,
            )
        else:
            return signal
