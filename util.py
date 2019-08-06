from pprint import pformat
import json
import sys
from spacy.tokens import Token


def init_spacy_extensions(extensions):
    for extension in extensions:
        try:
            Token.set_extension(extension, default=None)
        except ValueError:  # Extension already set
            pass


def eprint(*args):
    print(*args, file=sys.stderr)


def pprint(*args):
    eprint(pformat(*args))


def unpack_json_field(item, field):
    field_data = item.pop('data')
    field_data = json.loads(field_data)
    for k, v in field_data.items():
        item[k] = v
    return item
