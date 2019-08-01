import pickle
import json
from flask_socketio import send, emit
from role_pattern_nlp import RolePatternBuilder
import db

DEFAULT_BUILD_PATTERN_FEATURE_DICT = {'DEP': 'dep_', 'TAG': 'tag_'}
DEFAULT_REFINE_PATTERN_FEATURE_DICT = {'DEP': 'dep_', 'TAG': 'tag_', 'LOWER': 'lower_'}


def build_pattern(data):
    send('Build pattern request received')
    pos_match_id = data['pos_match_id']
    feature_dict = data.get('feature_dict')
    if not feature_dict:
        feature_dict = DEFAULT_BUILD_PATTERN_FEATURE_DICT
    pos_match_row = db.fetch_row('matches', pos_match_id, return_type='dict')
    sentence_id = pos_match_row['sentence_id']
    send('Preparing training data')
    pos_match = json.loads(pos_match_row['data'])['slots']
    pos_match = db.spacify_match(pos_match, sentence_id)
    send('Calculating pattern')
    role_pattern_builder = RolePatternBuilder(feature_dict)
    role_pattern = role_pattern_builder.build(pos_match, validate_pattern=True)
    token_labels = role_pattern.token_labels
    role_pattern_bytes = pickle.dumps(role_pattern)
    pattern_row = {
        'role_pattern_instance': role_pattern_bytes,
        'data': json.dumps({'token_labels': token_labels}),
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


def refine_pattern(data):
    send('refine pattern request received')
    send('Loading pattern')
    pattern_id = data['pattern_id']
    feature_dict = data.get('feature_dict')
    if not feature_dict:
        feature_dict = DEFAULT_REFINE_PATTERN_FEATURE_DICT
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
        role_pattern, pos_match, neg_matches
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
            'role_pattern_instance': pickle.dumps(role_pattern),
        }
        pattern_id = db.insert_row('patterns', pattern_row)
        send('pattern saved: {}'.format(pattern_id))
    else:
        send('pattern refinement unsuccessful')
    emit('refine_pattern_success')
