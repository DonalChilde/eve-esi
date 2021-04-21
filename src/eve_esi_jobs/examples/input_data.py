def market_history_params_extras():
    data = [
        {"region_id": 10000002, "type_id": 34, "fruit": "apple"},
        {"region_id": 10000002, "type_id": 36, "fruit": "orange"},
        {"region_id": 10000002, "type_id": 38, "fruit": "pear"},
    ]
    return data


def market_history_params():
    data = [
        {"region_id": 10000002, "type_id": 34},
        {"region_id": 10000002, "type_id": 36},
        {"region_id": 10000002, "type_id": 38},
    ]
    return data


def type_ids():
    data = [{"type_id": 34}, {"type_id": 36}, {"type_id": 38}]
    return data


def region_ids():
    data = [{"region_id": 10000002}]
    return data
