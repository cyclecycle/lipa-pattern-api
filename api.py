from flask import Flask
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
    send('connected')


@socketio.on('build_pattern')
def build_pattern(data):
    send('build pattern request received')
    pos_training_example_id = data['pos_training_example_id']
    pos_training_example = db.fetch_row(
        'training_examples',
        pos_training_example_id,
        return_type='dict',
    )
    sentence_id = pos_training_example['sentence_id']
    send('loading linguistic data')
    doc = db.load_sentence_doc(sentence_id)
    send('preparing training data')
    match_example = {}
    role_slots = json.loads(pos_training_example['data'])['slots']
    for role_slot in role_slots:
        label = role_slot['label']
        tokens = [doc[token['i']] for token in role_slot['tokens']]
        match_example[label] = tokens
    send('calculating pattern')
    feature_dict = {'DEP': 'dep_', 'TAG': 'tag_'}
    role_pattern_builder = RolePatternBuilder(feature_dict)
    role_pattern = role_pattern_builder.build(doc, match_example)
    send('saving pattern to database')
    pattern_row = {
        'name': 'unamed_pattern',
        'seed_example_id': pos_training_example_id,
        'role_pattern_instance': pickle.dumps(role_pattern)
    }
    pattern_id = db.insert_row('patterns', pattern_row)
    send('pattern saved: {}'.format(pattern_id))


@socketio.on('find_matches')
def find_matches(data):
    # Look for matches in all sentences
    # Load the role pattern class
    send('loading pattern')
    pattern_id = data['pattern_id']
    role_pattern = db.load_role_pattern(pattern_id)
    send('finding matches')
    sentence_ids = db.get_ids('sentences')
    match_ids = []
    for sentence_id in sentence_ids:
        doc = db.load_sentence_doc(sentence_id)
        matches = role_pattern.match(doc)
        matches = [db.despacify_role_pattern_match(match, sentence_id) for match in matches]
        for match in matches:
            match_row = {
                'pattern_id': pattern_id,
                'sentence_id': sentence_id,
                'data': json.dumps(match)
            }
            match_id = db.insert_row('matches', match_row)
            print(match_id)
            match_ids.append(match_id)
    send('matches saved: {}'.format(match_ids))


def refine_pattern(data):
    send('refine pattern request received')
    pos_training_example_id = data['pos_training_example_id']
    neg_match_ids = data['neg_match_ids']
    # pos_training_example = db.get_row('training_example', pos_training_example_id)
    # neg_matches = db.get_rows('matches', neg_match_ids)
    # Spacify the match examples


if __name__ == '__main__':
    socketio.run(app)
