from pprint import pformat
import json
import sys
from spacy.tokens import Token
import spacy

# nlp = spacy.load('en_core_web_sm')
nlp = spacy.load('en_core_sci_sm')


def init_vocab():
    return nlp.vocab


def set_token_extensions(token, features):
    if not features:
        return
    for key, val in features.items():
        try:
            Token.set_extension(key, default=None)
        except ValueError:  # Extension already set
            pass
        token._.set(key, val)


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
