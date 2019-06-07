import requests


def get_row(table, id_):
    query = '{0}/?id={1}'.format(table, id_)
    query_url = build_query_url(query)
    records = get_response_json(query_url)
    row = records[0]
    return row


def post_row(table, payload):
    query = 'patterns'
    query_url = build_query_url(query)
    response = requests.post(query_url, payload)
    return response


def build_query_url(query):
    query_url = '{0}{1}'.format(url, query)
    return query_url


def get_response_json(query_url):
    response = requests.get(query_url)
    try:
        json = response.json()
    except Exception as e:
        raise e
    return json
