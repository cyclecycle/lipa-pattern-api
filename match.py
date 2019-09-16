import json
from flask_socketio import send, emit
import db
import util


def find_matches(data):
    # Look for matches in all sentences
    # Load the role pattern class
    send('Find matches request received')
    send('Loading pattern')
    pattern_id = data['pattern_id']
    role_pattern = db.load_role_pattern(pattern_id)
    send('Finding matches')
    # Init a minimal vocab to save on deserialisation and memory
    vocab = util.init_vocab()
    sentence_ids = db.get_ids('sentences')
    match_ids = []
    for sentence_id in sentence_ids:
        doc = db.load_sentence_doc(sentence_id, vocab)
        for token in doc:
            print(token, token._.valence)
        matches = role_pattern.match(doc)
        for match in matches:
            slots, match_tokens = db.despacify_match(match, sentence_id)
            match_row = {
                'sentence_id': sentence_id,
                'data': json.dumps({'slots': slots, 'match_tokens': match_tokens})
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


def find_matches_all_patterns():
    pattern_ids = db.get_ids('patterns')
    for pattern_id in pattern_ids:
        find_matches_data = {'pattern_id': pattern_id}
        find_matches(find_matches_data)


def delete_all_pattern_matches():
    query = 'delete from pattern_matches'
    db.db_query(query, fetch='none')


def refresh_pattern_matches():
    send('Refresh pattern matches request received')
    delete_all_pattern_matches()
    find_matches_all_patterns()
    send('Refresh pattern matches done')
    emit('refresh_pattern_matches_success')

