import pickle
from spacy.tokens import Doc
from spacy.vocab import Vocab
from db import sql
import util


def get_sentence_linguistic_data(sentence_id):
    query = 'select spacy_doc, spacy_vocab from sentence_linguistic_data where sentence_id = ?'
    values = (sentence_id,)
    results = sql.db_query(query, values=values, fetch='one')
    spacy_doc, spacy_vocab = results
    return spacy_doc, spacy_vocab


def load_sentence_doc(sentence_id):
    spacy_doc_bytes, spacy_vocab_bytes = get_sentence_linguistic_data(sentence_id)
    vocab = Vocab().from_bytes(spacy_vocab_bytes)
    doc = Doc(vocab).from_bytes(spacy_doc_bytes)
    return doc


def load_role_pattern(pattern_id):
    row = sql.fetch_row('patterns', pattern_id, return_type='dict')
    if not row:
        raise Exception('No pattern found for id {}' .format(pattern_id))
    role_pattern_instance = row['role_pattern_instance']
    role_pattern = pickle.loads(role_pattern_instance)
    return role_pattern


def despacify_match(match, sentence_id):
    # Replace each token with its database representation
    slots = {}  # The labelled tokens
    for label, tokens in match.items():
        despacified_tokens = []
        for token in tokens:
            despacified_token = token_from_db(sentence_id, token.i)
            despacified_token = util.unpack_json_field(despacified_token, 'data')
            despacified_tokens.append(despacified_token)
        slots[label] = despacified_tokens
    match_tokens = match.match_tokens  # Includes the unlabelled tokens
    match_tokens = [token_from_db(sentence_id, token.i) for token in match_tokens]
    match_tokens = [util.unpack_json_field(token, 'data') for token in match_tokens]
    return slots, match_tokens


def spacify_match(match, sentence_id):
    for label, tokens in match.items():
        spacy_tokens = spacify_tokens(tokens, sentence_id)
        match[label] = spacy_tokens
    return match


def spacify_tokens(tokens, sentence_id):
    doc = load_sentence_doc(sentence_id)
    spacy_tokens = []
    for token in tokens:
        token_offset = token['token_offset']
        spacy_token = doc[token_offset]
        spacy_tokens.append(spacy_token)
    return spacy_tokens


def token_from_db(sentence_id, token_offset):
    query = 'select * from tokens where sentence_id = {0} and token_offset = {1}'.format(sentence_id, token_offset)
    token_row = sql.db_query(query, fetch='one')
    token_row = sql.row_to_dict(token_row, 'tokens')
    return token_row
