#  Copyright (c) 2010 AtTask, Inc.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
#  documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
#  Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
#  WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#  COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import urllib.request, urllib.error, urllib.parse
import json
import codecs


class StreamClient(object):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'

    PATH_LOGIN = "/login"
    PATH_LOGOUT = "/logout"

    def __init__(self, url, api_key):
        """
        url -- the full url to the attask api
            (http://yourdomain.attask-ondemand.com:8080/attask/api)
        """
        self.url = url if not url.endswith('/') else url[:-1]
        self.handle = None
        self.session_id = None
        self.user_id = None
        self.api_key = api_key

    def login(self, username, password):
        """
        logs into attask with username and password
        """
        params = {'username': username,
                  'password': password}
        data = self.request(StreamClient.PATH_LOGIN, params, StreamClient.GET)
        self.session_id = data['sessionID']
        self.user_id = data['userID']

    def logout(self):
        "logs out of attask"
        self.request(StreamClient.PATH_LOGOUT, None, StreamClient.GET)
        self.session_id = self.user_id = None

    def get_list(self, objcode, ids, fields=None):
        """
        Returns each object by id, similar to calling get for each id individually
        objcode -- object type ie. ObjCode.PROJECT
        ids -- list of ids to lookup
        [fields] -- list of field names to return for each object
        """
        path = '/%s' % objcode
        return self.request(path, {'ids': ','.join(ids)}, fields)

    def put(self, objcode, objid, params, fields=None):
        """
        Updates an existing object, returns the updated object
        objcode -- object type ie. ObjCode.PROJECT
        objid -- id of object to update
        params -- fields to update
        [fields] -- list of field names to return for the object
        """
        path = '/%s/%s' % (objcode, objid)
        return self.request(path, params, StreamClient.PUT, fields)

    def action(self, objcode, action, params, fields=None, objid=None):
        """
        Updates an existing object, returns the updated object
        :param objcode: object type ie. ObjCode.PROJECT
        :param objid: id of object to update
        :param action: action to execute
        :param params: -- fields to update
        :param fields: -- list of field names to return for the object
        """
        if objid:
            path = '/{objcode}/{objid}'.format(objcode=objcode, objid=objid, action=action)
        else:  # for some bulk operations you don't want to pass an obj ID in
            path = '/{objcode}'.format(objcode=objcode, action=action)

        params['action'] = action

        return self.request(path, params, StreamClient.PUT, fields)

    def bulk(self, objcode, updates, fields=None):
        path = '/%s' % objcode
        params = {'updates': updates}
        return self.request(path, params, StreamClient.PUT, fields)

    def post(self, objcode, params, fields=None):
        """
        Creates a new object, returns the new object
        objcode -- object type ie. ObjCode.PROJECT
        params -- values for object fields
        [fields] -- list of field names to return for the object
        """
        path = '/%s' % objcode
        return self.request(path, params, StreamClient.POST, fields)

    def get(self, objcode, objid, fields=None):
        """
        Lookup an object by id
        objcode -- object type ie. ObjCode.PROJECT
        objid -- id to lookup
        [fields] -- list of field names to return for each object
        """
        path = '/%s/%s' % (objcode, objid)
        return self.request(path, None, StreamClient.GET, fields)

    def delete(self, objcode, objid, force=False):
        """
        Deletes object with id objid
        objcode -- object type ie. ObjCode.PROJECT
        objid -- id of object to delete
        [force=False] -- force delete objects with relationships,
          ie. projects with task
        """
        path = '/%s/%s' % (objcode, objid)
        return self.request(path, {'force': force}, StreamClient.DELETE)

    def search(self, objcode, params, fields=None):
        """
        Search for objects
        objcode -- object type ie. ObjCode.PROJECT
        params -- name value keys to search for
        [fields] -- fields to return for each search result
        """
        path = '/%s/%s' % (objcode, 'search')
        return self.request(path, params, StreamClient.GET, fields)

    def report(self, objcode, params, agg_func):
        """
        Create aggregate reports
        :param objcode: Object type
        :param params: list of dict entries to use as criteria
        :param agg_func: Type of function (sum, avg, etc)
        :return: dict with the results
        """
        path = "/{objcode}/report".format(objcode=objcode)
        return self.request(path, params, StreamClient.GET)

    def request(self, path, params, method, fields=None, raw=False):
        """
        Basic api request
        path -- api url to open
        params -- parameters for request
        method -- a request method, StreamClient.GET,POST,PUT,DELETE
        [fields] -- added to params as fields to return for request
        [raw=False] -- returns the full json object, otherwise returns
          the contents of the data json data field
        """
        if not params:
            params = {}

        # params['sessionID'] = self.session_id
        params['method'] = method
        params['apiKey'] = self.api_key

        if fields:
            params['fields'] = ','.join(fields)

        dest = self.url + path

        data = urllib.parse.urlencode(params)
        bin_data = data.encode('ascii')

        try:
            response = urllib.request.urlopen(dest, bin_data)
        except urllib.error.URLError as e:
            error_msg = e.read().decode("utf8", 'ignore')
            error_msg = json.loads(error_msg)
            print(json.dumps(error_msg, indent=4, sort_keys=True))
            raise StreamAPIException(e)

        reader = codecs.getreader("utf-8")
        data = json.load(reader(response))

        return data if raw else data['data']


class StreamAPIException(Exception):
    """Raised when a request fails"""


class StreamNotModifiedException(Exception):
    """Raised when saving an object that has not been modified"""


class StreamClientNotSet(Exception):
    """Raised when calling an api method on an object without an
    attached StreamClient object
    """


# CRUD wrapper for basic modifications
class AtTaskObject(object):
    def __init__(self, data, streamclient=None):
        self.__dict__['streamclient'] = streamclient
        self.__dict__['data'] = data
        self.__dict__['_dirty_fields'] = {}

    def __getattr__(self, item):
        return self.__dict__['data'][item]

    def __setattr__(self, key, value):
        self._dirty_fields[key] = True
        self.data[key] = value

    def __str__(self):
        return json.dumps(self.data, indent=4)

    def is_modified(self):
        "Determines if object has been modified after creation"
        return bool(len(m))

    def save(self):
        """
        Persists changes to streamclient instance
        raises -- StreamClientNotSet if stream client was not passed in constructor
               -- StreamNotModifiedException if no fields have changed
               -- StreamAPIException if api call fails
        """
        if not self.streamclient:
            raise StreamClientNotSet()

        params = dict([(key, self.data[key])
                       for key, val in self._dirty_fields.items() if val])
        if not len(params):
            raise StreamNotModifiedException("No fields were modified.")

        if 'ID' in self.data:
            self.__dict__['data'] = self.streamclient.put(self.objCode, self.ID, params, list(self.data.keys()))
        else:
            self.__dict__['data'] = self.streamclient.post(self.objCode, params, list(self.data.keys()))

        self.__dict__['_dirty_fields'] = {}

    def delete(self, streamclient, force=False):
        """
        Deletes the current object by id
        raises -- StreamClientNotSet if stream client was not passed in constructor
        """
        if not self.streamclient:
            raise StreamClientNotSet()
        return self.streamclient.delete(self.objCode, self.ID, force)


# Supported object codes
class ObjCode:
    PROJECT = 'proj'
    TASK = 'task'
    ISSUE = 'optask'
    TEAM = 'team'
    HOUR = 'hour'
    TIMESHEET = 'tshet'
    USER = 'user'
    ASSIGNMENT = 'assgn'
    USER_PREF = 'userpf'
    CATEGORY = 'ctgy'
    CATEGORY_PARAMETER = 'ctgypa'
    PARAMETER = 'param'
    PARAMETER_GROUP = 'pgrp'
    PARAMETER_OPTION = 'popt'
    PARAMETER_VALUE = 'pval'
    ROLE = 'role'
    GROUP = 'group'
    NOTE = 'note'
    DOCUMENT = 'docu'
    DOCUMENT_VERSION = 'docv'
    EXPENSE = 'expns'
    CUSTOM_ENUM = 'custem'
    PROGRAM = 'prgm'
