import os

db_file_name = os.environ['LIPA_SQLITE_DB_FILE']
if not db_file_name:
    db_file_name = 'valence_rel_db.db'
print(db_file_name)

db_file_path = '../lipa-db/databases/{}'.format(db_file_name)

config = {
    'db_rest_url': 'http://localhost:8085/',
    'db_file_path': db_file_path,
}
