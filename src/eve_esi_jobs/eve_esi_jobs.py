import asyncio
import csv
import json
import logging
from asyncio import Task, create_task, gather
from asyncio.queues import Queue
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple
from uuid import uuid4

import yaml
from aiohttp import ClientSession
from more_itertools import spy

from eve_esi_jobs.callback_manifest import CallbackManifest, new_manifest
from eve_esi_jobs.exceptions import (
    CallbackError,
    DataUnchangedException,
    DeserializationError,
    EsiLocalSourceException,
    EsiRemoteSourceException,
    ValidationError,
)
from eve_esi_jobs.helpers import combine_dictionaries, optional_object
from eve_esi_jobs.models import EsiJob, EsiJobResult, EsiWorkOrder, JobCallback
from eve_esi_jobs.observers import QueueObserver
from eve_esi_jobs.operation_manifest import OperationManifest
from eve_esi_jobs.sources import EsiLocalSource, EsiRemoteSource

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class EveEsiJobs:
    def __init__(
        self,
        esi_schema: Dict,
        local_source: Optional[EsiLocalSource] = None,
        remote_source: Optional[EsiRemoteSource] = None,
        offline=False,
        operation_manifest: Optional[OperationManifest] = None,
        callback_manifest: Optional[CallbackManifest] = None,
        session_kwargs: Optional[Dict] = None,
        session: Optional[ClientSession] = None,
    ) -> None:
        if local_source is None and remote_source is None and offline:
            raise ValueError("Need at least one valid source")
        if local_source is None and offline:
            raise ValueError("Offline mode needs a local source.")
        self.operation_manifest = optional_object(
            operation_manifest, OperationManifest, schema=esi_schema
        )
        if not offline:
            if remote_source is None:
                self.remote_source: Optional[EsiRemoteSource] = EsiRemoteSource(
                    operation_manifest=self.operation_manifest
                )
            else:
                self.remote_source = remote_source
        else:
            self.remote_source = None
        self.local_source = local_source
        self.offline = offline
        self.callback_manifest = optional_object(callback_manifest, new_manifest)
        self.session_kwargs = optional_object(session_kwargs, dict)
        self.session = session
        self.data_formats = ["json", "yaml"]

    def do_job(
        self,
        job: EsiJob,
        override_values: Dict[str, Any] = None,
        observers: Optional[List[QueueObserver]] = None,
    ):
        override_values = optional_object(override_values, dict)
        observers = optional_object(observers, list)
        asyncio.run(
            self.job_runner(
                job=job, override_values=override_values, observers=observers
            )
        )

    def do_jobs(
        self,
        jobs: List[EsiJob],
        max_workers: int = 100,
        override_values: Dict[str, Any] = None,
        observers: Optional[List[QueueObserver]] = None,
    ):
        override_values = optional_object(override_values, dict)
        observers = optional_object(observers, list)
        asyncio.run(
            self.job_queue_runner(
                jobs=jobs,
                override_values=override_values,
                max_workers=max_workers,
                observers=observers,
            )
        )

    def do_workorder(
        self,
        workorder: EsiWorkOrder,
        max_workers: int = 100,
        override_values: Dict[str, Any] = None,
        observers: Optional[List[QueueObserver]] = None,
    ):
        override_values = optional_object(override_values, dict)
        observers = optional_object(observers, list)
        workorder.update_attributes(override=override_values)
        asyncio.run(
            self.job_queue_runner(
                jobs=workorder.jobs,
                override_values=workorder.attributes(),
                max_workers=max_workers,
                observers=observers,
            )
        )

    def do_workorders(
        self,
        workorders: Sequence[EsiWorkOrder],
        max_workers: int = 100,
        override_values: Dict[str, Any] = None,
        observers: Optional[List[QueueObserver]] = None,
    ):
        override_values = optional_object(override_values, dict)
        observers = optional_object(observers, list)
        jobs = []
        for workorder in workorders:
            workorder.update_attributes(override=override_values)
            for job in workorder.jobs:
                job.update_attributes(workorder.attributes())
                jobs.append(job)
        asyncio.run(
            self.job_queue_runner(
                jobs=jobs,
                override_values={},
                max_workers=max_workers,
                observers=observers,
            )
        )

    def create_job(
        self,
        op_id: str,
        parameters: Dict[str, Any],
        callbacks: Optional[List[JobCallback]] = None,
        name: str = "",
        description: str = "",
        id_: str = "",
    ) -> EsiJob:
        try:
            job = EsiJob(
                name=name,
                op_id=op_id,
                parameters=parameters,
                callbacks=callbacks,
                description=description,
                id_=id_,
            )
            self.validate_job(job)
            return job
        except Exception as ex:
            raise ValidationError(None, exception=ex, obj=job) from ex

    def create_workorder(
        self,
        name: str = "",
        description: str = "",
        id_: str = "",
        output_path: str = "",
        jobs: Optional[Sequence[EsiJob]] = None,
    ):
        jobs = optional_object(jobs, list)
        try:
            workorder = EsiWorkOrder(
                name=name, description=description, id_=id_, output_path=output_path
            )
            workorder.jobs.extend(jobs)
            self.validate_workorder(workorder)
        except Exception as ex:
            raise ValidationError(None, exception=ex, obj=workorder) from ex

    def validate_workorder(self, workorder: EsiWorkOrder):
        try:
            for job in workorder.jobs:
                self.validate_job(job)
        except Exception as ex:
            raise ValidationError(None, exception=ex, obj=workorder) from ex

    def validate_job(self, job: EsiJob):
        try:
            # validate op_id
            self.validate_params(op_id=job.op_id, params=job.parameters)
            for callback in job.callbacks:
                self.validate_callback(callback)
        except Exception as ex:
            raise ValidationError(None, exception=ex, obj=job) from ex

    def validate_params(self, op_id: str, params: Dict):
        pass

    def validate_callback(self, callback: JobCallback):
        pass

    def deserialize_job(
        self, file_path: Optional[Path], job_string: str = "", data_format: str = "json"
    ):
        if file_path is None and job_string == "":
            raise ValueError(
                "Must have either a Path to a file, or a valid job_string."
            )
        if data_format.lower() not in self.data_formats:
            raise ValueError(
                f"Data format must be one of {self.data_formats}, got {data_format}"
            )
        try:
            if file_path is not None:
                job = EsiJob.deserialize_file(file_path)
            else:
                if data_format.lower() == "json":
                    job = EsiJob.deserialize_json(job_string)
                elif data_format.lower() == "yaml":
                    job = EsiJob.deserialize_yaml(job_string)
        except Exception as ex:
            raise DeserializationError(None, ex) from ex
        return job

    def deserialize_workorder(
        self,
        file_path: Optional[Path],
        workorder_string: str = "",
        data_format: str = "json",
    ):
        if file_path is None and workorder_string == "":
            raise ValueError(
                "Must have either a Path to a file, or a valid workorder_string."
            )
        if data_format.lower() not in self.data_formats:
            raise ValueError(
                f"Data format must be one of {self.data_formats}, got {data_format}"
            )
        try:
            if file_path is not None:
                workorder = EsiWorkOrder.deserialize_file(file_path)
            else:
                if data_format.lower() == "json":
                    workorder = EsiWorkOrder.deserialize_json(workorder_string)
                elif data_format.lower() == "yaml":
                    workorder = EsiWorkOrder.deserialize_yaml(workorder_string)
        except Exception as ex:
            raise DeserializationError(None, ex) from ex
        return workorder

    def serialize_job(
        self,
        job: EsiJob,
        file_path: Optional[Path],
        data_format: str = "json",
        **kwargs,
    ) -> Tuple[Optional[Path], str]:
        if data_format.lower() not in self.data_formats:
            raise ValueError(
                f"Data format must be one of {self.data_formats}, got {data_format}"
            )
        if data_format.lower() == "json":
            job_string = job.serialize_json(job=job, **kwargs)
        elif data_format.lower() == "yaml":
            job_string = job.serialize_yaml(job=job, **kwargs)
        save_path = file_path
        if save_path is not None:
            save_path = job.serialize_file(
                file_path=save_path, file_format=data_format, **kwargs
            )
        return save_path, job_string

    def serialize_workorder(
        self,
        workorder: EsiWorkOrder,
        file_path: Optional[Path],
        data_format: str = "json",
        **kwargs,
    ):
        if data_format.lower() not in self.data_formats:
            raise ValueError(
                f"Data format must be one of {self.data_formats}, got {data_format}"
            )
        if data_format.lower() == "json":
            job_string = workorder.serialize_json(workorder=workorder, **kwargs)
        elif data_format.lower() == "yaml":
            job_string = workorder.serialize_yaml(workorder=workorder, **kwargs)
        save_path = file_path
        if save_path is not None:
            save_path = workorder.serialize_file(
                file_path=save_path, file_format=data_format, **kwargs
            )
        return save_path, job_string

    def _preprocess_job(self, job: EsiJob):
        self._add_file_path_prefix_to_callbacks(job)

    def _add_file_path_prefix_to_callbacks(self, esi_job: EsiJob):
        job_attributes = esi_job.attributes()
        parent_path = job_attributes.get("ewo_output_path", None)
        if parent_path is not None:
            for callback in esi_job.callbacks:
                file_path_template = callback.kwargs.get("file_path_template", None)
                if file_path_template is not None:
                    full_path_string = str(Path(parent_path) / Path(file_path_template))
                    callback.kwargs["file_path_template"] = full_path_string

    async def job_runner(
        self,
        job: EsiJob,
        override_values: Dict[str, Any] = None,
        observers: Optional[List[QueueObserver]] = None,
    ):
        observers = optional_object(observers, list)
        override_values = optional_object(override_values, dict)
        worker = JobQueueWorker(
            local_source=self.local_source,
            remote_source=self.remote_source,
            observers=observers,
            callback_manifest=self.callback_manifest,
        )
        job.update_attributes(override=override_values)
        self._preprocess_job(job)
        start = datetime.now()
        if self.session is not None:
            await worker.do_job(job=job, queue=None, session=self.session)
        else:
            async with ClientSession(**self.session_kwargs) as session:
                await worker.do_job(job=job, queue=None, session=session)
        end = datetime.now()
        logger.info(
            "EsiJob(uid=%s, op_id=%s) took %s",
            job.uid,
            job.op_id,
            f"{(end-start).total_seconds():.3f}",
        )

    async def job_queue_runner(
        self,
        jobs: Sequence[EsiJob],
        max_workers: int = 100,
        override_values: Dict[str, Any] = None,
        observers: Optional[List[QueueObserver]] = None,
    ):
        observers = optional_object(observers, list)
        override_values = optional_object(override_values, dict)
        worker_count = get_worker_count(len(jobs), max_workers=max_workers)
        workers: List[JobQueueWorker] = []
        for _ in range(worker_count):
            workers.append(
                JobQueueWorker(
                    local_source=self.local_source,
                    remote_source=self.remote_source,
                    observers=observers,
                    callback_manifest=self.callback_manifest,
                )
            )
        queue: Queue = Queue()
        worker_tasks: List[Task] = []
        for job in jobs:
            job.update_attributes(override=override_values)
            self._preprocess_job(job)
            queue.put_nowait(job)
        start = datetime.now()
        if self.session is not None:
            for worker in workers:
                worker_tasks.append(
                    create_task(worker.consumer(queue=queue, session=self.session))
                )
                await queue.join()
        else:
            async with ClientSession(**self.session_kwargs) as session:
                for worker in workers:
                    worker_tasks.append(
                        create_task(worker.consumer(queue=queue, session=session))
                    )
                    await queue.join()
        for worker_task in worker_tasks:
            worker_task.cancel()
        await gather(*worker_tasks, return_exceptions=True)  # TODO read about return ex
        end = datetime.now()
        took = end - start
        logger.info(
            "%s Jobs concurrently completed - took %s, "
            "%s Jobs per second using %s workers.",
            len(jobs),
            took,
            f"{(len(jobs)/took.total_seconds()):.2f}",
            len(worker_tasks),
        )


class JobQueueWorker:
    def __init__(
        self,
        local_source: Optional[EsiLocalSource],
        remote_source: Optional[EsiRemoteSource],
        # session: ClientSession,
        observers: Optional[List[QueueObserver]] = None,
        callback_manifest: Optional[CallbackManifest] = None,
    ) -> None:
        if local_source is None and remote_source is None:
            raise ValueError("Must have at least one valid data source.")

        self.uid = uuid4()
        self.task_count = 0
        self.local_source = local_source
        self.remote_source = remote_source
        # self.session = session
        self.observers = optional_object(observers, list)
        self.callback_manifest = optional_object(callback_manifest, new_manifest)

    def update_observers(
        self,
        job: EsiJob,
        result: Optional[EsiJobResult] = None,
        msg: str = "",
        exceptions: Optional[List[Exception]] = None,
        **kwargs,
    ):

        for observer in self.observers:
            # logger.info("updating observers")
            observer.update(
                self, job=job, result=result, msg=msg, exceptions=exceptions, **kwargs
            )

    async def consumer(self, queue: Queue, session: Optional[ClientSession] = None):
        while True:
            job: EsiJob = await queue.get()
            try:
                await self.do_job(job, queue, session)

            except Exception as ex:
                msg = f"Exception {ex} trapped in worker for job {str(job)[:500]}"
                logger.exception(msg)
                queue.task_done()
                raise ex

    async def from_local_source(self, job: EsiJob) -> Optional[EsiJobResult]:
        if self.local_source is not None:
            try:
                local_result = await self.local_source.do_job(job)
                self.update_observers(job=job, result=local_result, msg="From Local")
                return local_result
            except EsiLocalSourceException as ex:
                logger.exception("Error loading from local source. %r", ex)
                self.update_observers(
                    job=job, result=local_result, msg="From Local error"
                )
        return None

    async def do_job(
        self,
        job: EsiJob,
        queue: Optional[Queue] = None,
        session: Optional[ClientSession] = None,
    ):
        # TODO handle final None result, raise error?
        self.task_count += 1
        local_result = await self.from_local_source(job)
        if self.remote_source is None:
            job.result = local_result
            if queue is not None:
                queue.task_done()
            return
        if local_result is not None:
            etag = local_result.response.get_response_header("etag")
        else:
            etag = None
        if self.remote_source is not None and session is not None:
            try:
                remote_result = await self.remote_source.do_job(job, session, etag)
                job.result = remote_result
                self.update_observers(job=job, result=remote_result)
                if self.local_source is not None:
                    await self.local_source.store_result(remote_result)
            except DataUnchangedException as ex:
                # use local result
                job.result = local_result
            except EsiRemoteSourceException as ex:
                self.update_observers(
                    job=job,
                    result=None,
                    msg=f"Expected a result from the server, but there was an error. {ex}",
                )
                logger.exception("Error getting job data from Eve Esi, %s", ex)
        else:
            job.result = local_result
        if job.result is not None:
            await self._do_callbacks(job)
        if queue is not None:
            queue.task_done()

    async def _do_callbacks(self, job: EsiJob):
        """Do job callbacks after a successful retrieval

        intent is to report collected errors from callbacks to observer.
        one callbacks error will not stop other callbacks.
        """
        for job_callback in job.callbacks:
            errors: List[Exception] = []
            try:
                callback = self.callback_manifest.init_callback(job_callback, job)
                await callback.do_callback()
            except Exception as ex:
                error = CallbackError(None, exception=ex, callback=callback)
                logger.exception("Exception during %r, %r", job_callback, error)
                errors.append(error)
            finally:
                self.update_observers(job=job, result=None, exceptions=errors)


def get_worker_count(job_count, max_workers: int = 100) -> int:
    """Try to strike a reasonable balance between speed and DOS."""
    # worker_calc = ceil(job_count / 2)
    worker_calc = job_count
    if worker_calc > max_workers:
        worker_calc = max_workers
    return worker_calc


class BulkCreateJobs:
    def __init__(
        self,
        runner: EveEsiJobs,
        op_id: str,
        params: Dict[str, Any],
        bulk_params: Iterable[Dict[str, Any]],
        callbacks: Sequence[JobCallback],
    ) -> None:
        self.runner = runner
        self.op_id = op_id
        self.params = params
        self.bulk_params = bulk_params
        self.callbacks = callbacks

    def __iter__(self):
        return self

    def __next__(self):
        bulk_param = next(self.bulk_params)
        parameters = combine_dictionaries(bulk_param, [self.params])
        job = self.runner.create_job(
            op_id=self.op_id, parameters=parameters, callbacks=self.callbacks
        )
        return job


class DictDataLoader:
    def __init__(self, file_path: Path, keys: Optional[List[str]] = None) -> None:
        self.file_path = file_path
        self.file = open(file_path)
        self._iterable = self._get_iterable()
        self.keys = keys
        # TODO custom headers for loading lists, csv with no header line.

    def __exit__(self, exc_type, exc_value, traceback):
        self.file.close()

    def __iter__(self):
        for item in self._iterable:
            yield item

    def __enter__(self):
        return self

    def _get_iterable(self):
        if self.file_path.suffix.lower() == ".json":
            data = json.load(self.file)
            # head, iterator = spy(data)
            # if isinstance(head, dict):
            #     return iterator
            return self._check_obj(data)
        if self.file_path.suffix.lower() == ".yaml":
            data = yaml.safe_load(self.file)
            return self._check_obj(data)
            # return data
        if self.file_path.suffix.lower() == ".csv":
            csv_reader = csv.DictReader(self.file)
            return csv_reader

    def _check_obj(self, obj: Iterable) -> Iterator[Dict]:
        head, iterator = spy(obj)
        if isinstance(head, dict):
            return iterator
        if isinstance(head, list) and self.keys is not None:
            # TODO is it possible to split this out as a generator function to allow more inspection
            # TODO of the inputs? esp. check for length of keys and input.
            with_keys = iter([dict(zip(self.keys, x)) for x in iterator])
            return with_keys
        raise ValueError("Loaded data was not a dict. Did you provide the custom keys?")
