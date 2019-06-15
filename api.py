from flask import Flask, request
from flask_socketio import SocketIO, send, emit
import pickle
import json
from role_pattern_nlp import RolePatternBuilder
import db


app = Flask(__name__)
# app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


@socketio.on('connect')
def on_connect():
    print('connected')
    send('connected')


@socketio.on('error')
def error_handler(data):
    send('error', data)
    raise RuntimeError()


@socketio.on_error_default
def default_error_handler(e):
    print(e)
    emit('error', 'Something went wrong')
    print(request.event["message"])
    print(request.event["args"])
    raise e


@socketio.on('build_pattern')
def build_pattern(data):
    send('Build pattern request received')
    pos_match_id = data['pos_match_id']
    pos_match_row = db.fetch_row(
        'matches',
        pos_match_id,
        return_type='dict',
    )
    sentence_id = pos_match_row['sentence_id']
    send('Preparing training data')
    pos_match = json.loads(pos_match_row['data'])['slots']
    pos_match = db.spacify_match(pos_match, sentence_id)
    send('Calculating pattern')
    feature_dict = {'DEP': 'dep_', 'TAG': 'tag_'}
    role_pattern_builder = RolePatternBuilder(feature_dict)
    role_pattern = role_pattern_builder.build(pos_match)
    role_pattern_bytes = pickle.dumps(role_pattern)
    pattern_row = {
        'role_pattern_instance': role_pattern_bytes
    }
    pattern_id = db.insert_row('patterns', pattern_row)
    pattern_training_match_row = {
        'match_id': pos_match_id,
        'pattern_id': pattern_id,
        'pos_or_neg': 'pos',
    }
    pattern_id = db.insert_row('pattern_training_matches', pattern_training_match_row)
    send('Pattern saved. ID: {}'.format(pattern_id))
    emit('build_pattern_success', {'pattern_id': pattern_id})


@socketio.on('find_matches')
def find_matches(data):
    # Look for matches in all sentences
    # Load the role pattern class
    send('Find matches request received')
    send('Loading pattern')
    pattern_id = data['pattern_id']
    role_pattern = db.load_role_pattern(pattern_id)
    send('Finding matches')
    sentence_ids = db.get_ids('sentences')
    match_ids = []
    for sentence_id in sentence_ids:
        doc = db.load_sentence_doc(sentence_id)
        matches = role_pattern.match(doc)
        matches = [db.despacify_match(match, sentence_id) for match in matches]
        for match in matches:
            match_row = {
                'sentence_id': sentence_id,
                'data': json.dumps({'slots': match})
            }
            match_id = db.insert_row('matches', match_row)
            match_ids.append(match_id)
            pattern_match_row = {
                'match_id': match_id,
                'pattern_id': pattern_id,
            }
            db.insert_row('pattern_matches', pattern_match_row)
    send('Matches saved. IDs: {}'.format(match_ids))
    emit('find_matches_success')


@socketio.on('refine_pattern')
def refine_pattern(data):
    send('refine pattern request received')
    send('Loading pattern')
    pattern_id = data['pattern_id']
    role_pattern = db.load_role_pattern(pattern_id)
    send('Loading matches')
    pos_match_id = data['pos_match_id']
    neg_match_ids = data['neg_match_ids']
    pos_match_row = db.fetch_row('matches', pos_match_id, return_type='dict')
    if not pos_match_row:
        emit('error', 'no row found for pos match id: {}'.format(pos_match_id))
    neg_match_rows = db.fetch_rows('matches', neg_match_ids, return_type='dict')
    for id_, row in zip(neg_match_ids, neg_match_rows):
        if not row:
            emit('error', 'no row found for neg match id: {}'.format(id_))
    send('preparing training data')
    pos_match_sentence_id = pos_match_row['sentence_id']
    pos_match = json.loads(pos_match_row['data'])
    pos_match = db.spacify_match(pos_match, pos_match_sentence_id)
    neg_matches = []
    for neg_match_row in neg_match_rows:
        sentence_id = neg_match_row['sentence_id']
        neg_match = json.loads(neg_match_row['data'])
        neg_match = db.spacify_match(neg_match, sentence_id)
        neg_matches.append(neg_match)
    send('calculating pattern')
    feature_dict = {'DEP': 'dep_', 'TAG': 'tag_', 'LOWER': 'lower_'}
    role_pattern_builder = RolePatternBuilder(feature_dict)
    role_pattern_variants = role_pattern_builder.refine(
        role_pattern,
        pos_match,
        neg_matches
    )
    role_pattern_variants = list(role_pattern_variants)
    try:  # Try to take the first pattern
        refined_pattern = role_pattern_variants[0]
    except IndexError as e:  # None meet the criteria
        refined_pattern = None
    if refined_pattern:
        send('success. saving pattern')
        pattern_row = {
            'name': 'unamed_pattern',
            'role_pattern_instance': pickle.dumps(role_pattern)
        }
        pattern_id = db.insert_row('patterns', pattern_row)
        send('pattern saved: {}'.format(pattern_id))
    else:
        send('pattern refinement unsuccessful')
    emit('refine_pattern_success')


@socketio.on('find_all_pattern_matches')
def find_all_pattern_matches():
    pattern_ids = db.get_ids('patterns')
    for pattern_id in pattern_ids:
        find_matches_data = {'pattern_id': pattern_id}
        find_matches(find_matches_data)


@socketio.on('delete_all_pattern_matches')
def delete_all_pattern_matches():
    query = 'delete from pattern_matches'
    db.db_query(query, fetch='none')


@socketio.on('refresh_pattern_matches')
def refresh_pattern_matches():
    send('Refresh pattern matches request received')
    delete_all_pattern_matches()
    find_all_pattern_matches()
    send('Refresh pattern matches done')
    emit('refresh_pattern_matches_success')


if __name__ == '__main__':
    socketio.run(app)
