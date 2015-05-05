import os
import random
import sqlalchemy as sa

from hashlib import sha1
from pyramid_mailer import mailer
from pyramid_mailer.message import Message

systemmail = 'dbas@cs.uni-duesseldorf.de'


class PasswordGenerator(object):

	# http://interactivepython.org/runestone/static/everyday/2013/01/3_password.html
	def get_rnd_passwd(self):
		'''
		Generates a password with the length of 8 out of [a-z][A-Z][+-*/#!*?]
		:return: new secure password
		'''
		alphabet = 'abcdefghijklmnopqrstuvwxyz'
		upperalphabet = alphabet.upper()
		symbols= '+-*/#!*?'
		pw_len = 8
		pwlist = []

		for i in range(pw_len//3):
			pwlist.append(alphabet[random.randrange(len(alphabet))])
			pwlist.append(upperalphabet[random.randrange(len(upperalphabet))])
			pwlist.append(str(random.randrange(10)))
		for i in range(pw_len-len(pwlist)):
			pwlist.append(alphabet[random.randrange(len(alphabet))])

		pwlist.append(symbols[random.randrange(len(symbols))])
		pwlist.append(symbols[random.randrange(len(symbols))])

		random.shuffle(pwlist)
		pwstring = ''.join(pwlist)

		return pwstring


class PasswordHandler(object):

	def get_hashed_password(self, password):
		if isinstance(password, sa.Unicode):
			password_8bit = password.encode('UTF-8')
		else:
			password_8bit = password

		salt = sha1()
		salt.update(os.urandom(60))
		hash = sha1()
		hash.update(password_8bit + salt.hexdigest())
		hashed_password = salt.hexdigest() + hash.hexdigest()

		if not isinstance(hashed_password, sa.Unicode):
			hashed_password = hashed_password.decode('UTF-8')

		return hashed_password


	def send_password_to_email(request, password):
		'''
		Checks, for a valid email in the request, generats, sends and updates a new password
		:param request: current request
		:params password: the new password
		:return: message
		'''
		email = request.params['email']
		message = Message(subject='D-BAS Password Request',
		                  sender=systemmail,
		                  recipients =[email],
		                  body='Your new password is: ' + password
		                  )
		mailer.send(message)
		return 'A new password was send to ' + email