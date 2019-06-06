from flask_socketio import send, emit
from api import app, socketio


class TestApi:

    def setup_method(self):
        client = socketio.test_client(app)
        self.client = client

    def test_connect(self):
        client = self.client
        assert client.is_connected()
        received = client.get_received()
        assert received[0]['args'] == 'connected'

    def test_build_pattern(self):
        client = self.client
        event_name = 'build_pattern'
        data = {
            'pos_match_id': 1,
        }
        client.get_received()
        client.emit(event_name, data)
        received = client.get_received()
        print(received)

    def test_find_matches(self):
        client = self.client
        event_name = 'find_matches'
        data = {
            'pattern_id': 2,
        }
        client.get_received()
        client.emit(event_name, data)
        received = client.get_received()
        print(received)

    def test_refine_pattern(self):
        client = self.client
        event_name = 'refine_pattern'
        data = {
            'pattern_id': 2,
            'pos_match_id': 2,
            'neg_match_ids': [3],
        }
        client.get_received()
        client.emit(event_name, data)
        received = client.get_received()
        print(received)
