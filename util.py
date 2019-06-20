import json


def unpack_json_field(item, field):
    field_data = item.pop('data')
    field_data = json.loads(field_data)
    for k, v in field_data.items():
        item[k] = v
    return item
