import fcntl
import os
from contextlib import contextmanager
from typing import Optional

from irony.config.logger import logger


class FileLockError(Exception):
    pass


@contextmanager
def file_lock(lock_file: str):
    """Context manager for file locking operations"""
    fd: Optional[int] = None
    try:
        fd = os.open(lock_file, os.O_CREAT | os.O_RDWR)
        try:
            # Attempt non-blocking exclusive lock
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        except BlockingIOError:
            logger.warning("Another instance of the batch job is already running")
            raise FileLockError("Process already running")
    except OSError as e:
        logger.error(f"Failed to open or process lock file: {e}")
        raise FileLockError(f"Lock file error: {e}")
    finally:
        if fd is not None:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
            except Exception as e:
                logger.error(f"Error closing lock file: {e}")
