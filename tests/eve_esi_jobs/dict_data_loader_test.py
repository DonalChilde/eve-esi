import logging
from typing import Dict

from tests.eve_esi_jobs.conftest import FileResource

from eve_esi_jobs.eve_esi_jobs import DictDataLoader


def test_loader(sample_data: Dict[str, FileResource], logger: logging.Logger):
    with DictDataLoader(
        sample_data["market_history_params_extras.csv"].file_path
    ) as loader:

        # loader = EveDataLoader(sample_data["market_history_params_extras.json"].file_path)
        print(sample_data["market_history_params_extras.json"])
        data_list = list(loader)
        print(data_list)
    assert len(data_list) == 3


# TODO Test - yaml dict with/without keys
# TODO Test - json dict with/without keys
# TODO Test - csv with headers with/without keys
# TODO Test - yaml list with/without keys short/long keys
# TODO Test - json list with/without keys short/long keys
# TODO Test - csv no headers with/without keys
# TODO Test - yaml not list/dict
# TODO Test - json not list/dict
