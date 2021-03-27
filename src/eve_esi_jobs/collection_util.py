from typing import Dict, Optional, Sequence


def combine_dictionaries(base_dict: dict, overrides: Optional[Sequence[Dict]]) -> Dict:
    # TODO move this to collection util - NB makes a new dict with optional overrides
    combined_dict: Dict = {}
    combined_dict.update(base_dict)
    if overrides is not None:
        for override in overrides:
            combined_dict.update(override)
    return combined_dict
