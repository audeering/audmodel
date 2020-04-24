r"""Model interference interfaces.

The idea is that all our models provide a common set
of methods to apply them to signals or files, e.g.:

* :func:`process_signal`
* :func:`process_file`
* :func:`process_files`
* :func:`process_folder`

:mod:`audbmodel.interface` provides you classes
that you can inherit or just instanciate
to get some standard implementations of those methods.

Example:
    >>> import numpy as np
    >>> def process_func(signal, sampling_rate):
    ...     return signal.shape[1] / sampling_rate
    ...
    >>> model = Process(process_func=process_func)
    >>> signal = np.array([1., 2., 3.])
    >>> model.process_signal(signal, sampling_rate=3)
    1.0

"""
from audmodel.core.interface import (
    Process,
    ProcessWithContext,
    Segment,
)
