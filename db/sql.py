import sqlite3
from config import config

db_path = config['db_file_path']


def db_query(query, values=None, fetch='all', return_id=False):
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
        if return_id:
            result = cur.lastrowid
    return result


def fetch_row(table, row_id, return_type='tup'):
    query = 'select * from {0} where id = {1}'.format(table, row_id)
    result = db_query(query, fetch='one')
    if return_type == 'dict':
        result = row_to_dict(result, table)
    return result


def insert_row(table, data):
    column_names = ', '.join(data.keys())
    query = 'insert into {0} ({1}) values ({2})'.format(
        table,
        column_names,
        ', '.join(['?' for i in range(len(data))])
    )
    values = tuple(data.values())
    row_id = db_query(query, values=values, return_id=True)
    return row_id


def get_column_names(table):
    query = 'PRAGMA TABLE_INFO({})'.format(table)
    result = db_query(query, fetch='all')
    names = [tup[1] for tup in result]
    return names


def row_to_dict(row, table):
    column_names = get_column_names(table)
    dict_ = dict(zip(column_names, row))
    return dict_


def get_ids(table):
    query = 'select id from {}'.format(table)
    results = db_query(query)
    ids = [result[0] for result in results]
    return ids
