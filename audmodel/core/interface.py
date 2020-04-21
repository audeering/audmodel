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
            start: pd.Timedelta = None,
            end: pd.Timedelta = None,
            channel: int = None,
    ) -> typing.Any:
        r"""Process the content of an audio file.

        Args:
            file: file path
            channel: channel number
            start: start processing at this position
            end: end processing at this position

        Returns:
            Output of process function

        Raises:
            RuntimeError: if sampling rates of model and signal do not match

        """
        signal, sampling_rate = self.read_audio(
            file,
            channel=channel,
            start=start,
            end=end,
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
    ) -> pd.Series:
        r"""Process a list of files.

        Args:
            files: list of file paths
            channel: channel number

        Returns:
            Dictionary mapping files to output of process function

        Raises:
            RuntimeError: if sampling rates of model and signal do not match

        """
        data = [None] * len(files)
        with audeer.progress_bar(
                files,
                total=len(files),
                desc='',
                disable=not self.verbose,
        ) as pbar:
            for idx, file in enumerate(pbar):
                desc = audeer.format_display_message(file, pbar=True)
                pbar.set_description(desc, refresh=True)
                data[idx] = self.process_file(file, channel=channel)
        return pd.Series(data, index=pd.Index(files, name='file'))

    def process_folder(
            self,
            root: str,
            *,
            filetype: str = 'wav',
            channel: int = None,
    ) -> pd.Series:
        r"""Process files in a folder.

        .. note:: At the moment does not scan in sub-folders!

        Args:
            root: root folder
            filetype: file extension
            channel: channel number

        Returns:
            Dictionary mapping files to output of process function

        Raises:
            RuntimeError: if sampling rates of model and signal do not match

        """
        files = audeer.list_file_names(root, filetype=filetype)
        return self.process_files(files, channel=channel)

    def process_index(
            self,
            index: pd.MultiIndex,
            *,
            channel: int = None) -> pd.Series:
        r"""Process from a segmented index.

        .. note:: The index has to provide segment information conform to the
            Unified Format.

        Args:
            index: index with segment information
            channel: channel number (default 0)

        Returns:
            Series with predictions in the Unified Format

        Raises:
            RuntimeError: if sampling rates of model and signal do not match

        """
        if not index.names == ('file', 'start', 'end'):
            raise ValueError('Not a segmented index conform to Unified Format')

        y = [None] * len(index)

        with audeer.progress_bar(index, total=len(index),
                                 desc=f'Process',
                                 disable=not self.verbose) as pbar:
            for idx, (file, start, end) in enumerate(pbar):
                y[idx] = self.process_file(file, channel=channel, start=start,
                                           end=end)

        return pd.Series(y, index=index)

    def process_signal(
            self,
            signal: np.ndarray,
            sampling_rate: int,
            *,
            start: pd.Timedelta = None,
            end: pd.Timedelta = None,
    ) -> typing.Any:
        r"""Process audio signal and return result.

        Args:
            signal: signal values
            sampling_rate: sampling rate in Hz
            start: start processing at this position
            end: end processing at this position

        Returns:
            Output of process function

        Raises:
            RuntimeError: if sampling rates of model and signal do not match

        """
        # Enforce 2D signals
        signal = np.atleast_2d(signal)

        # Resample signal
        if (
                self.sampling_rate is not None
                and sampling_rate != self.sampling_rate
        ):
            if self.resample is not None:
                signal = self.resample(signal, sampling_rate)
                signal = np.atleast_2d(signal)
            else:
                raise RuntimeError(
                    f'Signal sampling rate of {sampling_rate} Hz '
                    f'does not match requested model sampling rate of '
                    f'{self.sampling_rate} Hz.'
                )

        # Find start and end index
        max_i = signal.shape[-1]
        if start is not None:
            start_i = int(round(start.total_seconds() * sampling_rate))
            start_i = max(start_i, max_i)
        else:
            start_i = 0
        if end is not None and not pd.isna(end):
            end_i = int(round(end.total_seconds() * sampling_rate))
            end_i = max(end_i, max_i)
        else:
            end_i = max_i

        # Process signal
        if self.process_func is not None:
            return self.process_func(
                signal[:, start_i:end_i],
                sampling_rate,
                **self.process_func_kwargs,
            )
        else:
            return signal
