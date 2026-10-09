"""Worker entry point: `python -m app.workers.main`. Same image as the API, run as its own
process (one replica). Runs the TD-007 SLA breach sweep every 30 s."""

import asyncio
import logging

from app.features import load_models
from app.features.sla.sweep import sweep

INTERVAL_SECONDS = 30
log = logging.getLogger("ticketdesk.worker")


async def run_forever() -> None:
    load_models()
    while True:
        try:
            result = await sweep()
            if result.breaches:
                log.info("sla sweep: %d breaches", len(result.breaches))  # counts only, no PII
        except Exception:  # keep sweeping; one bad pass must not stop breach detection
            log.exception("sla sweep failed")
        await asyncio.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_forever())
