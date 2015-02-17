"""
    Author: Tyler Lubeck
    Date: 2/16/2015
    Purpose: An abstraction from the RESTful interface for the server.
             Handles authentication and selecting the proper endpoint
"""
import requests
import json


class ServerInterface(object):
    LOCATION = 0
    ACCESS_POINT = 1
    FLOOR = 2

    def __init__(self, username, password):
        self.__resources = [ServerInterface.LOCATION,
                            ServerInterface.ACCESS_POINT,
                            ServerInterface.FLOOR]
        self.__username = username
        self.__password = password
        self.__auth = (self.__username, self.__password)
        self.__root_url = 'http://sirius-multi-user.herokuapp.com/api/v1/{}/'
        # self.__root_url = 'http://localhost:8000/api/v1/{}/'
        self.__location_url = self.__root_url.format('location')
        self.__access_point_url = self.__root_url.format('accesspoint')
        self.__floor_url = self.__root_url.format('floor')
        self.__resource_urls = [self.__location_url,
                                self.__access_point_url,
                                self.__floor_url]

    def __prep_data(self, resource, payload):
        """ Prepare the data to be in a clean format for posting.
            If resource is not a valid resource, then throw a ValueError
            If payload is not a dictionary, then throw a ValueError
            Otherwise, return the proper url and headers
        """

        if resource not in self.__resources:
            msg = 'Not a valid resource. Choices are LOCATION, FLOOR, or ACCESS_POINT'
            raise ValueError(msg)

        if not isinstance(payload, dict):
            msg = 'payload needs to be a dictionary'
            raise ValueError(msg)

        url = self.__resource_urls[resource]

        headers = {
            'content-type': 'application/json'
        }

        return url, headers

    def post(self, resource, payload, is_file=False, **kwargs):
        """ Post the payload to the proper resource """

        url, headers = self.__prep_data(resource, payload)

        r = requests.post(url,
                          data=json.dumps(payload),
                          headers=headers,
                          auth=self.__auth,
                          **kwargs)

        r.raise_for_status()
        return r.json()

    def post_with_files(self, resource, payload, files):
        """ Posts to the resource with both a payload and files.
            Check to make sure that the values in 'files' are indeed files.
            If not, raise a ValueError
        """

        if not isinstance(files, dict):
            raise ValueError('files needs to be a dictionary of files')

        # for key, value in files.iteritems():
        #     if not isinstance(value, file):
        #         raise ValueError('{} is not a file'.format(key))

        url, _ = self.__prep_data(resource, payload)

        r = requests.post(url,
                          data=payload,
                          auth=self.__auth,
                          files=files)
        print r.content
        r.raise_for_status()
        return r.json()

    def get_list(self, resource, parameters):
        """ Get data from the resource, with the specified parameters
            If any object is found, returns (True, data) where data is
                the dictionary all found items
            If the object is not found, returns (False, None)
            If something else went wrong, throws an Exception
        """
        url, headers = self.__prep_data(resource, parameters)
        r = requests.get(url,
                         params=parameters,
                         headers=headers,
                         auth=self.__auth)
        # If the object is not found, then return False to signify it
        if r.status_code == requests.codes.not_found:
            return False, None

        r.raise_for_status()
        response = r.json()
        if response['meta']['total_count'] > 0:
            return True, response['objects']

        else:
            return False, None

    def get_single_item(self, resource, parameters):
        """ Get data from the resource, with the specified parameters
            If any object is found, returns (True, data) where data is
                the dictionary of the FIRST item found
            If no object is found, returns (False, None)
            If something else went wrong, throws an Exception
        """

        found, items = self.get_list(resource, parameters)
        if found:
            return found, items[0]
        else:
            return found, items
