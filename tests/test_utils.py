import signal
import threading

import pytest

from audmodel.core import utils


def test_sigterm_as_interrupt():
    r"""Test SIGTERM raises KeyboardInterrupt.

    Inside the context manager
    SIGTERM has to raise a ``KeyboardInterrupt``,
    and the previous handler
    has to be restored afterwards.

    """
    previous_handler = signal.getsignal(signal.SIGTERM)

    with utils.sigterm_as_interrupt():
        handler = signal.getsignal(signal.SIGTERM)
        assert handler is not previous_handler
        with pytest.raises(KeyboardInterrupt):
            handler(signal.SIGTERM, None)

    assert signal.getsignal(signal.SIGTERM) is previous_handler


def test_sigterm_as_interrupt_outside_main_thread():
    r"""Test SIGTERM is not changed outside the main thread.

    Signal handlers can only be installed in the main thread,
    outside of it the context manager
    has to leave SIGTERM untouched.

    """
    handlers = []

    def target():
        r"""Store SIGTERM handler inside the context manager."""
        with utils.sigterm_as_interrupt():
            handlers.append(signal.getsignal(signal.SIGTERM))

    thread = threading.Thread(target=target)
    thread.start()
    thread.join()

    assert handlers == [signal.getsignal(signal.SIGTERM)]
