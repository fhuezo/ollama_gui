"""Threading helpers — run background work without freezing the UI."""

from __future__ import annotations

import threading
from typing import Any, Callable


def run_in_thread(
    fn: Callable[..., Any],
    *,
    args: tuple = (),
    on_success: Callable[[Any], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
    daemon: bool = True,
) -> threading.Thread:
    """Execute *fn* in a daemon thread.

    After *fn* completes:
    - on success, *on_success(result)* is called (if provided).
    - on exception, *on_error(exc)* is called (if provided).

    The callbacks are called from the **worker thread** — callers should
    use ``widget.after()`` to marshal back to the Tk main loop.
    """

    def _worker() -> None:
        try:
            result = fn(*args)
            if on_success:
                on_success(result)
        except Exception as exc:
            if on_error:
                on_error(exc)

    t = threading.Thread(target=_worker, daemon=daemon)
    t.start()
    return t
