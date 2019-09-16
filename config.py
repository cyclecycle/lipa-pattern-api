import os

db_file_name = os.environ['LIPA_SQLITE_DB_FILE']
if not db_file_name:
    db_file_name = 'valence_rel_db.db'

port = os.environ['PATTERN_API_PORT']
if not port:
    port = 8085

db_file_path = '../lipa-db/databases/{}'.format(db_file_name)

config = {
    'port': port,
    'db_rest_url': 'http://localhost:{}/'.format(port),
    'db_file_path': db_file_path,
}
