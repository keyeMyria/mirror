# Introducing an API to enable external discussions
#
# @author Christian Meter, Tobias Krauthoff
# @email {meter, krauthoff}@cs.uni-duesseldorf.de

import binascii
import json
import logging
import os

from cornice import Service
from dbas.views import Dbas
from webob import Response, exc

log = logging.getLogger()
log.setLevel(logging.DEBUG)

# CORS configuration
cors_policy = dict(enabled=True,
				   headers=('Origin', 'X-Requested-With', 'Content-Type', 'Accept'),
				   origins=('*',),
				   # credentials=True,  # TODO: how can i use this?
				   max_age=42)


# =============================================================================
# SERVICES - Define services for several actions of DBAS
# =============================================================================

dump       = Service(name='api_dump',
					 path='/dump',
					 description="Database Dump",
					 cors_policy=cors_policy)
users      = Service(name='login',
                     path='/login',
                     description="User management of external discussion system",
                     cors_policy=cors_policy)
news       = Service(name='api_news',
 					 path='/get_news',
 					 description="News app",
 					 cors_policy=cors_policy)
reaction   = Service(name='api_reaction',
 					 path='/{slug}/reaction/{arg_id_user}/{mode}*arg_id_sys',
 					 description="Discussion Reaction",
 					 cors_policy=cors_policy)
justify    = Service(name='api_justify',
					 path='/{slug}/justify/{statement_or_arg_id}/{mode}*relation',
					 description="Discussion Justify",
					 cors_policy=cors_policy)
attitude   = Service(name='api_attitude',
					 path='/{slug}/attitude/*statement_id',
					 description="Discussion Attitude",
					 cors_policy=cors_policy)
# Prefix with 'z' so it is added as the last route
zinit      = Service(name='api_init',
					 path='/{slug}',
					 description="Discussion Init",
					 cors_policy=cors_policy)
zinit_blank = Service(name='api_init_blank',
					  path='/',
					  description="Discussion Init",
					  cors_policy=cors_policy)


@news.get()
def get_news(request):
	"""
	Returns news from DBAS in JSON.
	:param request: request
	:return: Dbas(request).get_news()
	"""
	return Dbas(request).get_news()


##############################
# Discussion-related functions

@reaction.get()
def discussion_reaction(request):
	"""
	Return data from DBas discussion_reaction page
	:param request: request
	:return: Dbas(request).discussion_reaction(True)
	"""
	return Dbas(request).discussion_reaction(True)


@justify.get()
def discussion_justify(request):
	"""
	Return data from DBas discussion_justify page
	:param request: request
	:return: Dbas(request).discussion_justify(True)
	"""
	return Dbas(request).discussion_justify(True)


@attitude.get()
def discussion_attitude(request):
	"""
	Return data from DBas discussion_attitude page
	:param request: request
	:return: Dbas(request).discussion_attitude(True)
	"""
	return Dbas(request).discussion_attitude(True)


@zinit.get()
def discussion_init(request):
	"""
	Return data from DBas discussion_init page
	:param request: request
	:return: Dbas(request).discussion_init(True)
	"""
	return Dbas(request).discussion_init(True)


@zinit_blank.get()
def discussion_init(request):
	"""
	Return data from DBas discussion_init page
	:param request: request
	:return: Dbas(request).discussion_init(True)
	"""
	return Dbas(request).discussion_init(True)


##########
# Database

@dump.get()
def discussion_init(request):
	"""
	Return database dump
	:param request: request
	:return: Dbas(request).get_database_dump(True)
	"""
	return Dbas(request).get_database_dump()


# =============================================================================
# POST / GET EXAMPLE
# =============================================================================

hello = Service(name='api', path='/hello', description="Simplest app", cors_policy=cors_policy)
values = Service(name='foo', path='/values/{value}', description="Cornice Demo", cors_policy=cors_policy)

_VALUES = {}


@hello.get()
def get_info(request):
	"""

	:param request:
	:return:
	"""
	return {'Hello': 'World'}


@values.get()
def get_value(request):
	"""

	:param request:
	:return:
	"""
	key = request.matchdict['value']
	return _VALUES.get(key)


@values.post()
def set_value(request):
	"""Set the value.

	Returns *True* or *False*.
	"""
	key = request.matchdict['value']
	try:
		# json_body is JSON-decoded variant of the request body
		_VALUES[key] = request.json_body
	except ValueError:
		return False
	return True


# =============================================================================
# LOGIN
# =============================================================================
_USERS = {}


#########
# Helpers

def _create_token():
	"""
	Use the system's urandom function to generate a random token and convert it to ASCII.
	:return:
	"""
	return binascii.b2a_hex(os.urandom(20))


class _401(exc.HTTPError):
	"""
	Return a 401 HTTP Error message if user is not authenticated
	:return:
	"""
	def __init__(self, msg='Unauthorized'):
		body = {'status': 401, 'message': msg}
		Response.__init__(self, json.dumps(body))
		self.status = 401
		self.content_type = 'application/json'


def valid_token(request):
	"""
	Validate the submitted token. Checks if a user is logged in.
	:param request:
	:return:
	"""
	header = 'X-Messaging-Token'
	htoken = request.headers.get(header)
	if htoken is None:
		log.error("htoken is None")
		raise _401()
	try:
		user, token = htoken.split('-', 1)
	except ValueError:
		log.error("ValueError")
		raise _401()

	log.debug("API Login Attempt: %s: %s" % (user, token))

	valid = user in _USERS and _USERS[user] == token

	if not valid:
		log.error("API Invalid token")
		raise _401()

	log.debug("API Remote login successful")
	request.validated['user'] = user


def validate_credentials(request):
	"""
	Parse credentials from POST request and validate it against DBAS' database
	:param request:
	:return:
	"""
	# Decode received data
	data = request.body.decode('utf-8')
	data = json.loads(data)
	nickname = data['nickname']
	password = data['password']

	# Check in DBAS' database, if the user's credentials are valid
	logged_in = Dbas(request).user_login(nickname, password, for_api=True)

	try:
		if logged_in['status'] == 'success':
			user = {'nickname': nickname, 'token': _create_token()}
			request.validated['user'] = user
	except TypeError:
		log.error('API Not logged in: %s' % logged_in)
		request.errors.add(logged_in)


############################
# Services - User Management

# TODO sample function, remove it
@users.get(validators=valid_token)
def get_users(request):
	"""
	Returns a list of all users
	"""
	return {'users': _USERS}


@users.post(validators=validate_credentials)
def user_login(request):
	"""
	Check provided credentials and return a token, if it is a valid user.
	The function body is only executed, if the validator added a request.validated field.
	:param request:
	:return: token
	"""
	user = request.validated['user']

	# Convert bytes to string
	if type(user['token']) == bytes:
		token = user['token'].decode('utf-8')
	else:
		token = user['token']

	_USERS[user['nickname']] = token
	return {'token': '%s-%s' % (user['nickname'], token)}
