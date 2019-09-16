from flask import Flask, request
from flask_socketio import SocketIO, send, emit
from pattern import build_pattern, refine_pattern
from match import find_matches, find_matches_all_patterns, delete_all_pattern_matches, refresh_pattern_matches
from visualise import visualise_sentence, visualise_pattern, visualise_match
from config import config


app = Flask(__name__)
# app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


@socketio.on('connect')
def on_connect():
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


event_map = {
    'build_pattern': build_pattern,
    'refine_pattern': refine_pattern,
    'find_matches': find_matches,
    'find_matches_all_patterns': find_matches_all_patterns,
    'delete_all_pattern_matches': delete_all_pattern_matches,
    'refresh_pattern_matches': refresh_pattern_matches,
    'visualise_sentence': visualise_sentence,
    'visualise_pattern': visualise_pattern,
    'visualise_match': visualise_match,
}

for event, func in event_map.items():
    decorator = socketio.on(event)
    decorator(func)


if __name__ == '__main__':
    socketio.run(app, debug=True, port=config['port'])
