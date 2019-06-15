import sqlite3
from config import config

db_path = config['db_file_path']


def db_query(query, values=None, fetch='all', return_id=False):
    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys=ON')
        if values:
            cur.execute(query, values)
        else:
            cur.execute(query)
        if fetch == 'one':
            result = cur.fetchone()
        if fetch == 'all':
            result = cur.fetchall()
        if fetch == 'none':
            result = None
        if return_id:
            result = cur.lastrowid
    return result


def fetch_row(table, row_id, return_type='tup'):
    query = 'select * from {0} where id = {1}'.format(table, row_id)
    result = db_query(query, fetch='one')
    if return_type == 'dict':
        result = row_to_dict(result, table)
    return result


def fetch_rows(table, row_ids, return_type='tup'):
    id_list = ', '.join([str(id_) for id_ in row_ids])
    query = 'select * from {0} where id IN ({1})'.format(table, id_list)
    results = db_query(query, fetch='all')
    if return_type == 'dict':
        results = rows_to_dicts(results, table)
    return results


def insert_row(table, data):
    column_names = []
    values = []
    for key, value in data.items():
        column_names.append(key)
        if isinstance(value, bytes):
            value = sqlite3.Binary(value)
        values.append(value)
    placeholders = ', '.join(['?' for i in range(len(column_names))])
    column_names = ', '.join(column_names)
    query = 'insert into {0} ({1}) values ({2})'.format(
        table,
        column_names,
        placeholders,
    )
    values = tuple(values)
    row_id = db_query(query, values=values, return_id=True)
    return row_id


def get_column_names(table):
    query = 'PRAGMA TABLE_INFO({})'.format(table)
    result = db_query(query, fetch='all')
    names = [tup[1] for tup in result]
    return names


def row_to_dict(row, table):
    if not row:
        return {}
    column_names = get_column_names(table)
    dict_ = dict(zip(column_names, row))
    return dict_


def rows_to_dicts(rows, table):
    column_names = get_column_names(table)
    dicts = []
    for row in rows:
        if not row:
            dict_ = {}
        else:
            dict_ = dict(zip(column_names, row))
        dicts.append(dict_)
    return dicts


def get_ids(table):
    query = 'select id from {}'.format(table)
    results = db_query(query)
    ids = [result[0] for result in results]
    return ids
