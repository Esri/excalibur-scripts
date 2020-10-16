/* Copyright 2020 Esri
*
* Licensed under the Apache License Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/

""" A script that creates an Excalibur Imagery Project in a Portal using a JSON configuration file

  Attributes
      username (string): The username of a portal member who has permissions to create content
      password (string): The password for the user
      portalSharingUrl (string): The url to the 'sharing' endpoint that is the base url for REST calls.
"""

from os import path

import logging
import logging.config

import json

import requests

# Path to directory that holds files with configuration info
APP_CONFIG_DIR = r"..\config"

# Path to log file configuration
LOG_CONFIG_FILE_NAME = path.join(APP_CONFIG_DIR, "logging.conf")

# Default folder name for storing imagery project items
# THIS IS ONLY USED IN THE FIRST RELEASE OF EXCALIBUR
PROJECT_FOLDER_NAME = "Excalibur Imagery Projects"

# Project version to use if none is specified in the project JSON
DEFAULT_PROJECT_VERSION = 2

# Default type of project
DEFAULT_PROJECT_TYPE = "BaseProject"

# Flag to not verify SSL certificate when making https request.
# Change to False to NOT verify SSL certificates.
VERIFY_SSL = True


class ProjectCreator:
    def __init__(self, username, password, portalSharingUrl, shareWithOrg=False):
        """
        Constructor for the ProjectCreator class

        Parameters:
            username (string): The username of a portal member who has permissions to create content
            password (string): The password for the user
            portalSharingUrl (string): The url to the 'sharing' endpoint that is the base url for REST calls.
                Format is https://<domain>/<webadaptor>/sharing/rest
            shareWithOrg (boolean): Flag to share the project item with the organization
        """

        logging.config.fileConfig(LOG_CONFIG_FILE_NAME)
        self._logger = logging.getLogger("imageProject.start")

        self._logger.info(
            "### INITIALIZING PROJECT CREATOR FOR NEW PROJECT ###")
        if not username or not password or not portalSharingUrl:
            raise Exception(
                "Missing argument(s). Supply username, password, and portalSharingUrl")

        # Urls and other info to access and create items in portal
        self.portalSharingUrl = portalSharingUrl.rstrip("/")
        self.username = username
        self.password = password
        self.shareWithOrg = shareWithOrg

        self._contentUrl = portalSharingUrl + "/content/users/" + username

        # portal token
        self._token = self._getToken()

    def makeProject(self, projectConfig):
        """
        The function to create the portal item that represents the Excalibur Imagery Project.

        Parameters:
            projectConfig (JSON object) The JSON describing the properties of the Excalibur Imagery Project.

        Returns:
            string: The id of the Excalibur Imagery Project portal item.
        """

        self._logger.info("### Making project ###")

        title = projectConfig["title"]

        # project object holds all info needed to create the portal items
        itemObject = {"title": title, "projectType": DEFAULT_PROJECT_TYPE}
        projectObject = {"instructions": "",
                         "rasterIds": [], "version": DEFAULT_PROJECT_VERSION}

        if "status" in projectConfig:
            itemObject["status"] = projectConfig["status"]
        else:
            itemObject["status"] = "StatusDraft"

        if "description" in projectConfig:
            itemObject["description"] = projectConfig["description"]
        else:
            itemObject["description"] = ""

        if "webmapId" in projectConfig:
            projectObject["webmapId"] = projectConfig["webmapId"]

        if "version" in projectConfig:
            projectObject["version"] = projectConfig["version"]

        if "summary" in projectConfig:
            itemObject["snippet"] = projectConfig["summary"]
        else:
            itemObject["snippet"] = ""

        self._itemObject = itemObject
        self._projectObject = projectObject

        # create folder if needed
        folderName = itemObject["title"]
        if projectObject["version"] == 1:
            folderName = PROJECT_FOLDER_NAME

        folderResponse = self._createFolder(folderName)

        self._folderId = folderResponse["id"]
        if folderResponse["new"] == False:
            existingProject = self._getProjectFromFolder(
                folderResponse["id"], title)
            if existingProject:
                raise Exception(
                    "Cannot create project. One with the same name already exists")

        self._logger.info(
            "Created folder. Folder Id: {0}".format(self._folderId))

        # set folderId property id project version is 2
        if projectObject["version"] != 1:
            projectObject["folderId"] = self._folderId

        # populate the common properties for observation and basic project
        if "instructions" in projectConfig:
            projectObject["instructions"] = projectConfig["instructions"]

        if "focusImageLayer" in projectConfig:
            projectObject["focusImageLayer"] = projectConfig["focusImageLayer"]
        else:
            if "serviceUrl" in projectConfig:
                projectObject["serviceUrl"] = projectConfig["serviceUrl"]

            if "rasterIds" in projectConfig:
                projectObject["rasterIds"] = projectConfig["rasterIds"]

        # populate properties for observation project if projectConfig has observationLayers
        if "observationLayers" in projectConfig:
            self._itemObject["projectType"] = "ObservationProject"
            projectObject["observationLayers"] = projectConfig["observationLayers"]

        # create Project item
        itemId = self._createItem()
        self._logger.info("Created item. Item id: {0}".format(itemId))

        # share items with organization
        if self.shareWithOrg:
            self._shareItems(itemId)

        return itemId

    def _getToken(self):
        """
        Private method that generates a token used to access the portal

        Returns:
            string: The token
        """
        data = {"username": self.username, "password": self.password,
                "referer": "clientIp", "f": "json"}
        url = self.portalSharingUrl + "/generateToken"

        r = requests.post(url, data=data, verify=VERIFY_SSL)

        if r.status_code != 200:
            message = "Error in htttp request to get token: Http status code: {0}".format(
                r.status_code)
            raise Exception(message)

        response = r.json()
        if "error" in response:
            message = "Error getting token for portal: {!s}".format(
                response["error"])
            raise Exception(message)

        return response["token"]

    def _createFolder(self, name):
        """
        Private method that creates a folder in the user's content where the Imagery Project item is stored.

        Parameters:
            name (string): The name of the folder to create

        Returns:
            object: Object with two properties:
                id (string) The id of the folder that already exists or that was created
                new (boolean) True if the folder was created, False if the folder already exists
        """

        # get existing folders to see if "name" exists
        url = self._contentUrl
        data = {"f": "json", "token": self._token, "num": 1}
        r = requests.get(url, params=data, verify=VERIFY_SSL)

        if (r.status_code != 200):
            raise Exception("Error in htttp request to get existing folders")

        response = r.json()
        if "error" in response:
            message = "Error getting current folders from portal: {0}".format(
                json.dumps(response["error"]))
            raise Exception(message)

        folders = response["folders"]

        # Check if folder already exists and return the id if it does
        for f in folders:
            if f["title"] == name:
                return {"new": False, "id": f["id"]}

        # if we made it here a new folder needs to be created
        url = self._contentUrl + "/createFolder"

        data = {"f": "json", "token": self._token, "title": name}

        r = requests.post(url, data=data, verify=VERIFY_SSL)

        if r.status_code != 200:
            raise Exception("Error in http request to create folder")

        response = r.json()
        if not "success" in response or not response["success"]:
            message = "Error creating folder: {!s}".format(
                json.dumps(response["error"]["message"]))
            raise Exception(message)

        return {"new": True, "id": response["folder"]["id"]}

    def _createItem(self):
        """
        Private method that adds the Imagery Project item to the portal.

        Returns:
            string: The id of the ImageryProject item
        """

        url = self._contentUrl + "/" + self._folderId + "/addItem"

        item = {"f": "json", "token": self._token}
        item["title"] = self._itemObject["title"]
        item["snippet"] = self._itemObject["snippet"]
        item["type"] = "Excalibur Imagery Project"
        item["typeKeywords"] = "{0}, {1}".format(
            self._itemObject["status"], self._itemObject["projectType"])
        item["tags"] = "Image Project"
        item["text"] = json.dumps(self._projectObject)

        errMsg = None

        r = requests.post(url, data=item, verify=VERIFY_SSL)

        if r.status_code != 200:
            raise Exception("Error in http request to create the portal item")

        response = r.json()
        if not "success" in response or not response["success"]:
            errMsg = "Error creating the portal item. {!s}".format(json.dumps(
                response["error"]))
            raise Exception(errMsg)

        itemId = response["id"]
        return itemId

    def _getProjectFromFolder(self, folderId, projectName):
        """
        Private method that queries the portal to find an Imagery Project item in a folder.

        Parameters:
            folderId (string): The id of the folder to search
            projectName (string): Name of the Imagery Project

        Returns:
            string: Id of the project that was found. If no project is found, nothing is returned
        """

        queryString = "ownerfolder:{0} title:\"{1}\"".format(
            folderId, projectName)

        url = self.portalSharingUrl + "/search"
        data = {"f": "json", "token": self._token, "q": queryString}

        r = requests.get(url, params=data, verify=VERIFY_SSL)

        if r.status_code != 200:
            message = "Error searching for project. Http code: {!s}".format(
                r.status_code)
            raise Exception(message)

        response = r.json()

        if response["total"] > 0:
            return response["results"][0]
        else:
            return

    def _shareItems(self, projectId):
        """
        Private method that shares the project item with the portal organization

        Parameters:
            projectId (string): The id of the Imagery Project item
        """

        url = self._contentUrl + "/shareItems"

        # share project with org
        items = projectId

        data = {"f": "json", "token": self._token}
        data["org"] = True
        data["items"] = items

        r = requests.post(url, data=data, verify=VERIFY_SSL)

        if r.status_code != 200:
            message = "Error sharing items. Http code: {!s}".format(
                r.status_code)
            raise Exception(message)

        response = r.json()
        return response
