"""
============
Eve Esi Jobs
============
"""
import logging

from eve_esi_jobs import models
from eve_esi_jobs.callback_manifest import CallbackManifest
from eve_esi_jobs.eve_esi_jobs import EveEsiJobs
from eve_esi_jobs.operation_manifest import OperationManifest

__author__ = """Chad Lowe"""
__email__ = "pfmsoft@gmail.com"
__version__ = "0.1.3"

__all__ = [
    # "do_jobs",
    # "do_workorder",
    "EveEsiJobs",
    # "JobsToActionsOpMan",
    "models",
    "CallbackManifest",
    "OperationManifest",
]
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
