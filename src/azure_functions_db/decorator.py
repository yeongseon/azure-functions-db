from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any

from azure_functions_db.trigger.poll import PollTrigger
from azure_functions_db.trigger.retry import RetryPolicy
from azure_functions_db.trigger.runner import SourceAdapter, StateStore

logger = logging.getLogger(__name__)


class _DbNamespace:
    def poll(
        self,
        *,
        name: str,
        source: SourceAdapter,
        checkpoint_store: StateStore,
        batch_size: int = 100,
        max_batches_per_tick: int = 1,
        lease_ttl_seconds: int = 120,
        retry_policy: RetryPolicy | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., int]]:
        trigger = PollTrigger(
            name=name,
            source=source,
            checkpoint_store=checkpoint_store,
            batch_size=batch_size,
            max_batches_per_tick=max_batches_per_tick,
            lease_ttl_seconds=lease_ttl_seconds,
            retry_policy=retry_policy,
        )

        def decorator(fn: Callable[..., Any]) -> Callable[..., int]:
            def wrapper(timer: object) -> int:
                return trigger.run(timer=timer, handler=fn)

            return wrapper

        return decorator


db = _DbNamespace()
