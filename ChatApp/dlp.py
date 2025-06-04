import re
import importlib
import inspect
import logging

PCI_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
PHI_PATTERN = re.compile(r"\b(?:SSN\s*\d{3}-\d{2}-\d{4})\b", re.IGNORECASE)

logger = logging.getLogger(__name__)

async def default_dlp_callback(message: str, sender=None):
    """Simple regex check for PCI/PHI patterns."""
    if PCI_PATTERN.search(message) or PHI_PATTERN.search(message):
        return False
    return True

async def run_dlp_hook(message: str, sender=None, hook_path: str | None = None):
    """Load and execute a DLP hook. Returns True if send should proceed."""
    if not hook_path:
        return True
    try:
        module_path, func_name = hook_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
        if inspect.iscoroutinefunction(func):
            return await func(message=message, sender=sender)
        return func(message=message, sender=sender)
    except Exception as exc:
        logger.error("DLP hook failed: %s", exc)
        return True
