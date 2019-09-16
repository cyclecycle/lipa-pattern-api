from flask_socketio import send, emit
import json
import visualise_spacy_tree
from role_pattern_nlp import RolePatternMatch, role_pattern_vis
import db
from spacy.tokens import Token
from util import pprint


# DEFAULT_NODE_ATTRS = {
#     **role_pattern_vis.DEFAULT_NODE_ATTRS,
#     **role_pattern_vis.DEFAULT_STYLE_ATTRS,
# }
# Token.set_extension('plot', default=DEFAULT_NODE_ATTRS)
Token.set_extension('plot', default={})


def visualise_pattern(data):
    pattern_id = data['pattern_id']
    send('Loading pattern')
    role_pattern = db.load_role_pattern(pattern_id)
    pprint(role_pattern.spacy_dep_pattern)
    send('Generating DOT')
    node_attrs = role_pattern_vis.DEFAULT_NODE_ATTRS
    # for token in doc:
    #     token._.plot.update(node_attrs)
    #     token._.plot['label'] = '{0} [{1}]\n({2})'.format(token.orth_, token.i, token.tag_)
    graph, legend = role_pattern.to_pydot(legend=True)
    graph, legend = graph.to_string(), legend.to_string()
    dot_data = {
        'graph': graph,
        'legend': legend,
    }
    emit('visualise_pattern_success', dot_data)


def visualise_sentence(data):
    sentence_id = data['sentence_id']
    send('Loading sentence')
    doc = db.load_sentence_doc(sentence_id)
    node_attrs = role_pattern_vis.DEFAULT_NODE_ATTRS
    for token in doc:
        token._.plot.update(node_attrs)
        label = '{0} [{1}]\n({2})'.format(token.orth_, token.i, token.tag_)
        # for key, val in token._.items():
        #     if val:
        #         label += '\n{0}: {1}'.format(key, val)
        token._.plot['label'] = label
    graph = visualise_spacy_tree.to_pydot(doc)
    graph = graph.to_string()
    dot_data = {
        'graph': graph,
    }
    emit('visualise_sentence_success', dot_data)


def visualise_match(data):
    match_id = data['match_id']
    send('Loading data')
    match_row = db.fetch_row(
        'matches',
        match_id,
        return_type='dict',
    )
    print(match_row['data'])
    sentence_id = match_row['sentence_id']
    slots = json.loads(match_row['data'])['slots']
    match_tokens = json.loads(match_row['data'])['match_tokens']
    slots = db.spacify_match(slots, sentence_id)
    match_tokens = db.spacify_tokens(match_tokens, sentence_id)
    role_pattern_match = RolePatternMatch(slots)
    role_pattern_match.match_tokens = match_tokens
    graph, legend = role_pattern_match.to_pydot(legend=True)
    graph, legend = graph.to_string(), legend.to_string()
    dot_data = {
        'graph': graph,
        'legend': legend,
    }
    emit('visualise_match_success', dot_data)
