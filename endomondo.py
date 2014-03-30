#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

""" Simple API for accessing Endomondo data.

Provides Endomondo API wrapper, which uses Endomondo mobile API
instead of HTML scrapping. Only some features are currently implemented,
but as Endomondo app uses HTTP, it's somewhat easy to implemented rest.
To retrieve network stream from from andoid, run on adb shell:
	>>> tcpdump -n -s 0 -w -| nc -l -p 11233

and on Linux:
	>>> adb forward tcp:11233 tcp:11233
	>>> nc 127.0.0.1 11233 | wireshark -k -S -i -

To use, first authenticat client. Currently it seems that auth_token is
never changed, so only once is necessary and storing auth_toke somewhere
should be sufficient:

	>>> sports_tracker = Endomond('user@email.com', 'password')
	>>> for workout in sports_tracker.workout_list():
	>>>	print workout.summary

OR

	>>> sports_tracker = Endomond()
	>>> sports_tracker.auth_token = '***blahblah***'


This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 2.1 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import requests
# For deviceId generation
import uuid, socket

from datetime import datetime, timedelta, tzinfo

class Endomondo:
	# Some parameters what Endomondo App sends.
	country = 'GB'
	device_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, socket.gethostname()))
	os = "Android"
	app_version="7.1"
	app_variant="M-Pro"
	os_version="2.3.7"
	model="HTC Vision"

	# Auth token - seems to stay same, even when disconnecting - Security flaw in Endomondo side, but easy to fix on server side.
	auth_token = None

	# Using session - provides keep-alive in urllib3
	Requests = requests.session()

	'''Well known urls.

	Well known urls for retrieving workout data from Endomondo. Thease are currently implementing version seven (:attribute:`Endomondo.app_version` ) of Endomondo App api, and those has been changed for version eight.

	Version 8 urls:
	http://api.mobile.endomondo.com/mobile/api/workout/get?authToken=<token>&fields=device,simple,basic,motivation,interval,hr_zones,weather,polyline_encoded_small,points,lcp_count,tagged_users,pictures,feed&workoutId=215638526&deflate=true&compression=deflate
	http://api.mobile.endomondo.com/mobile/api/workouts?authToken=<token>&fields=device,simple,basic,lcp_count&maxResults=20&deflate=true&compression=deflate

	:attribute:`Endomondo.URL_AUTH` Url for requesting authentication token.
	:attribute:`Endomondo.URL_WORKOUTS` Workouts (later in app called as "history" page) listing page.
	:attribute:`Endomondo.URL_TRACK` Running track
	:attribute:`Endomondo.URL_PLAYLIST` Music tracks

	'''
	URL_AUTH		= 'https://api.mobile.endomondo.com/mobile/auth?v=2.4&action=PAIR'
	URL_WORKOUTS	= 'http://api.mobile.endomondo.com/mobile/api/workout/list?'
	URL_TRACK	= 'http://api.mobile.endomondo.com/mobile/readTrack'
	URL_PLAYLIST	= 'http://api.mobile.endomondo.com/mobile/api/workout/playlist'

	sports_map = {
		2: 'Cycling, sport',
		1: 'Cycling, transport',
		14: 'Fitness walking',
		15: 'Golfing',
		16: 'Hiking',
		21: 'Indoor cycling',
		9: 'Kayaking',
		10: 'Kite surfing',
		3: 'Mountain biking',
		17: 'Orienteering',
		19: 'Riding',
		5: 'Roller skiing',
		11: 'Rowing',
		0: 'Running',
		12: 'Sailing',
		4: 'Skating',
		6: 'Skiing, cross country',
		7: 'Skiing, downhill',
		8: 'Snowboarding',
		20: 'Swimming',
		18: 'Walking',
		13: 'Windsurfing',
		22: 'Other',
		23: 'Aerobics',
		24: 'Badminton',
		25: 'Baseball',
		26: 'Basketball',
		27: 'Boxing',
		28: 'Climbing stairs',
		29: 'Cricket',
		30: 'Elliptical training',
		31: 'Dancing',
		32: 'Fencing',
		33: 'Football, American',
		34: 'Football, rugby',
		35: 'Football, soccer',
		49: 'Gymnastics',
		36: 'Handball',
		37: 'Hockey',
		48: 'Martial arts',
		38: 'Pilates',
		39: 'Polo',
		40: 'Scuba diving',
		41: 'Squash',
		42: 'Table tennis',
		43: 'Tennis',
		44: 'Volleyball, beach',
		45: 'Volleyball, indoor',
		46: 'Weight training',
		47: 'Yoga',
		50: 'Step counter',
		87: 'Circuit Training',
		88: 'Treadmill running',
		89: 'Skateboarding',
		90: 'Surfing',
		91: 'Snowshoeing',
		92: 'Wheelchair',
		93: 'Climbing',
		94: 'Treadmill walking'
	}

	def __init__(self, email=None, password=None):
		
		self.Requests.headers['User-Agent'] = "Dalvik/1.4.0 (Linux; U; %s %s; %s Build/GRI40)" % (self.os, self.os_version, self.model)

		if email and password:
			self.auth_token = self.request_auth_token(email, password)

	def get_auth_token(self):
		'''Return authentication token.
		If token is not defined, requests new. This token can be saved between sessions.
		'''

		if self.auth_token:
			return self.auth_token
		self.auth_token = self.request_auth_token()
		return self.auth_token

	def request_auth_token(self, email, password):
		''' Request new authentication token from Endomondo server

		:param email: Email for login.
		:param password: Password for login.
		'''
		params = {
			'email':			email,
			'password':		password,
			'country':		self.country,
			'deviceId':		self.device_id,
			'os'	:			self.os,
			'appVersion':	self.app_version,
			'appVariant':	self.app_variant,
			'osVersion':		self.os_version,
			'model':			self.model
		}

		r = self.Requests.get(self.URL_AUTH, params=params)

		lines = r.text.split("\n")
		if lines[0] != "OK":
			raise ValueError("Could not authenticate with Endomondo, Expected 'OK', got '%s'" % lines[0])

		lines.pop(0)
		for line in lines:
			key, value = line.split("=")
			if key == "authToken":
				return value
		
		return False

	def make_request(self, url, params={}):
		''' Helper for generating requests - can't be used in athentication.

		:param url: base url for request. Well know are currently defined in :attribute:`Endomondo.URL_WORKOUTS` and :attribute:`Endomondo.URL_TRACK`.
		:param params: additional parameters to be passed in GET string.
		'''
		params.update({
			'authToken':	self.get_auth_token(),
			'language':	'EN'
		})

		r = self.Requests.get(url, params=params)

		if r.status_code != requests.codes.ok:
			print("Could not retrieve URL %s" % r.url)
			r.raise_for_status()

		return r


	def workout_list(self, max_results=40, before=None):
		""" Retrieve workouts.

		:param before: datetime object or iso format date string (%Y-%m-%d %H:%M:%S UTC)
		:param max_results: Maximum number of workouts to be returned.
		"""

		params = {
			'maxResults': max_results
		}

		if before != None:
			if type(before) is datetime:
				## Endomondo _really_ needs timezone
				if before.tzinfo != None:
					before = before.astimezone(tzinfo('UTC'))

				params['before'] = before.strftime('%Y-%m-%d %H:%M:%S UTC')
			elif type(before) is str:
				params['before'] = before
			else:
				raise ValueError("param 'before needs to be datetime object or iso formatted string.")

		r = self.make_request(self.URL_WORKOUTS, params)

		workouts = []
		for entry in r.json()['data']:
			workout = Workout(entry)
			workouts.append(workout)

		return workouts

""" Workout class. Bad design. """

class Workout:

	def __init__(self, entry):
		self.data = entry
