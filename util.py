import requests
import pickle
import sqlite3
from spacy.tokens import Doc
from spacy.vocab import Vocab
from config import config


url = config['db_rest_url']
db_path = config['db_file_path']


def build_query_url(query):
    query_url = '{0}{1}'.format(url, query)
    return query_url


def get_response_json(query_url):
    response = requests.get(query_url)
    try:
        json = response.json()
    except Exception as e:
        raise e
    return json


def get_sentence_linguistic_data(sentence_id):
    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        query = 'select spacy_doc, spacy_vocab from sentence_linguistic_data where sentence_id = ?'
        cur.execute(query, (sentence_id,))
        results = cur.fetchone()
        spacy_doc, spacy_vocab = results
    return spacy_doc, spacy_vocab


def insert_pattern(pattern):
    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        role_pattern_instance = pattern['role_pattern_instance']
        query = 'insert into patterns (name, seed_example_id, role_pattern_instance) values (?, ?, ?)'
        cur.execute(query, (pattern['name'], pattern['seed_example_id'], role_pattern_instance,))
        pattern_id = cur.lastrowid
    return pattern_id


def insert_row(table, data):
    column_names = ', '.join(data.keys())
    query = 'insert into {0} ({1}) values ({2})'.format(
        table,
        column_names,
        ', '.join(['?' for i in range(len(data))])
    )
    values = tuple(data.values())
    row_id = db_query(query, 'fetchone', values=values)
    return row_id


def load_sentence_doc(sentence_id):
    spacy_doc_bytes, spacy_vocab_bytes = get_sentence_linguistic_data(sentence_id)
    vocab = Vocab().from_bytes(spacy_vocab_bytes)
    doc = Doc(vocab).from_bytes(spacy_doc_bytes)
    return doc


def get_row(table, id_):
    query = '{0}/?id={1}'.format(table, id_)
    query_url = build_query_url(query)
    records = get_response_json(query_url)
    row = records[0]
    return row


def post_row(table, payload):
    query = 'patterns'
    query_url = build_query_url(query)
    response = requests.post(query_url, payload)
    return response


def get_ids(table):
    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        query = 'select id from {}'.format(table)
        cur.execute(query)
        results = cur.fetchall()
        ids = [result[0] for result in results]
    return ids


def db_query(query, values=None, fetch='all'):
    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        if values:
            cur.execute(query, values)
        else:
            cur.execute(query)
        if fetch == 'one':
            result = cur.fetchone()
        if fetch == 'all':
            result = cur.fetchall()
    return result


def fetch_row(table, row_id, columns='*'):
    query = 'select {0} from {1} where id = {2}'.format(columns, table, row_id)
    result = db_query(query, fetch='all')
    return result


def load_role_pattern(pattern_id):
    result = fetch_row('patterns', pattern_id, columns='role_pattern_instance')
    role_pattern_instance = result[0]
    role_pattern = pickle.loads(role_pattern_instance)
    return role_pattern


def despacify_role_pattern_match(match, sentence_id):
    # Replace each token with its database representation
    for label, tokens in match.items():
        for token in tokens:
            query = 'select * from tokens where sentence_id = {0} and i = {1}'.format(sentence_id, token.i)
            token_row = db_query(query, fetch='one')
            