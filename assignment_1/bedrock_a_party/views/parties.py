from flakon import JsonBlueprint
from flask import abort, jsonify, request

from bedrock_a_party.classes.party import CannotPartyAloneError, NotExistingFoodError, \
     NotInvitedGuestError, Party

parties = JsonBlueprint('parties', __name__)

_LOADED_PARTIES = {}  # dict of available parties
_PARTY_NUMBER = 0  # index of the last created party


'''
    Handles the parties.

    GET:  Retrieves all scheduled parties.
    POST: Creates a new party and gets the party identifier back.
'''
@parties.route('/parties', methods=['GET', 'POST'])
def all_parties():
    result = ''

    if request.method == 'POST':
        try:
            result = create_party(request)
        except CannotPartyAloneError:
            result = jsonify({'error': 'you cannot party alone'})
            return result, 400

    elif request.method == 'GET':
        result = get_all_parties()

    return result


'''
    GET: Returns the number of parties currently loaded in the system.
'''
@parties.route('/parties/loaded')
def loaded_parties():
    return jsonify({'loaded_parties': len(_LOADED_PARTIES)})


'''
    Modifies a party.

    GET:    Retrieves the party identified by <id>.
    DELETE: Deletes the party identified by <id> from the system.
'''
@parties.route('/party/<id>', methods=['GET', 'DELETE'])
def single_party(id):
    global _LOADED_PARTIES
    result = ''

    exists_party(id)

    if 'GET' == request.method:
        serialized_party = _LOADED_PARTIES[id].serialize()
        result = jsonify(serialized_party)

    elif 'DELETE' == request.method:
        del _LOADED_PARTIES[id]
        result = jsonify({'msg': 'Party deleted!'})

    return result


'''
    Returns a foodlist.

    GET: Retrieves the current foodlist of the party identified by <id>.
'''
@parties.route('/party/<id>/foodlist')
def get_foodlist(id):
    global _LOADED_PARTIES
    result = ''

    exists_party(id)

    if 'GET' == request.method:
        foodlist = _LOADED_PARTIES[id].get_food_list()
        result = jsonify({'foodlist': foodlist.serialize()})

    return result


'''
    Manages food within a foodlist.

    POST:   Adds the <item> brought by <user> to the food- list of the party <id>.
    DELETE: Removes the given <item> brought by <user> from the food-list of the party <id>
'''
@parties.route('/party/<id>/foodlist/<user>/<item>', methods=['POST', 'DELETE'])
def edit_foodlist(id, user, item):
    global _LOADED_PARTIES

    exists_party(id)
    
    party = _LOADED_PARTIES[id]
    result = ''

    if 'POST' == request.method:
        food = None
        try:
            food = party.add_to_food_list(item, user)
        except NotInvitedGuestError:
            result = jsonify({'error': f'{user} is not invited to this party'})
            return result, 401
        except ItemAlreadyInsertedByUser:
            result = jsonify({'error': f'{user} already committed to bring {food}'})
            return result, 400
        
        serialized_food = food.serialize()
        result = jsonify(serialized_food)

    if 'DELETE' == request.method:
        try:
            party.remove_from_food_list(item, user)
        except NotExistingFoodError:
            result = jsonify({'error': f'{user} has not added {food} to this party foodlist'})
            return result, 400
        
        result = jsonify({'msg': 'Food deleted!'})

    return result


#
# These are utility functions. Use them, DON'T CHANGE THEM!!
#

def create_party(req):
    global _LOADED_PARTIES, _PARTY_NUMBER

    # get data from request
    json_data = req.get_json()

    # list of guests
    try:
        guests = json_data['guests']
    except:
        raise CannotPartyAloneError('you cannot party alone!')

    # add party to the loaded parties lists
    _LOADED_PARTIES[str(_PARTY_NUMBER)] = Party(_PARTY_NUMBER, guests)
    _PARTY_NUMBER += 1

    return jsonify({'party_number': _PARTY_NUMBER - 1})


def get_all_parties():
    global _LOADED_PARTIES

    return jsonify(loaded_parties=[party.serialize() for party in _LOADED_PARTIES.values()])


def exists_party(_id):
    global _PARTY_NUMBER
    global _LOADED_PARTIES

    if int(_id) > _PARTY_NUMBER:
        abort(404)  # error 404: Not Found, i.e. wrong URL, resource does not exist
    elif not(_id in _LOADED_PARTIES):
        abort(410)  # error 410: Gone, i.e. it existed but it's not there anymore
