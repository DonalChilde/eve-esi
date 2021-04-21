"""Top-level package for Eve Esi Jobs."""
import logging

from eve_esi_jobs.runners import do_jobs, do_workorder

__author__ = """Chad Lowe"""
__email__ = "pfmsoft@gmail.com"
__version__ = "0.1.2"

__all__ = ["do_jobs", "do_workorder"]
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
