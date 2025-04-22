# Copyright 2020 Esri
#
# Licensed under the Apache License Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" A module that creates an Excalibur Imagery Project in a Portal using a JSON configuration file.
It uses the ArcGIS API for Python

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
DEFAULT_PROJECT_VERSION = "4.0"

# Default type of project
DEFAULT_PROJECT_TYPE = "BaseProject"

class ProjectCreator:
    def __init__(self, gis, shareWithOrg=False, verifySSL=True):
        """
        Constructor for the ProjectCreator class

        Parameters:
            gis (GIS): A GIS made using the arcgis.gis module of the ArcGIS API for Python. See https://developers.arcgis.com/python/api-reference/arcgis.gis.toc.html#gis
            shareWithOrg (boolean): Flag to share the project item with the organization
            verifySSL (boolean): Flag to verify SSL certificate when making https request
        """

        logging.config.fileConfig(LOG_CONFIG_FILE_NAME)
        self._logger = logging.getLogger("imageProject.start")

        self._logger.info(
            "### INITIALIZING PROJECT CREATOR FOR NEW PROJECT ###")
        if not gis:
            raise Exception(
                "Missing argument(s). Supply gis")

         # Urls and other info to access and create items in portal
        self._gis = gis
        self.username = gis.properties["user"]["username"]
        self.shareWithOrg = shareWithOrg
        self.verifySSL = verifySSL

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

        # project object holds all info needed to create the portal item
        itemObject = {"title": title}
        projectObject = {"instructions": "", "version": DEFAULT_PROJECT_VERSION}

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
        self._folderName = folderName

        if folderResponse["new"] == False:
            existingProject = self._getProjectFromFolder(
                folderResponse["id"], title)
            if existingProject:
                raise Exception(
                    "Cannot create project. One with the same name already exists")

        self._logger.info(
            "Created folder. Folder Id: {0}".format(self._folderId))

        # populate the common properties for observation and basic project
        if "instructions" in projectConfig:
            projectObject["instructions"] = projectConfig["instructions"]

        if "primaryLayers" in projectConfig:
            projectObject["primaryLayers"] = projectConfig["primaryLayers"]
        elif "focusImageLayer" in projectConfig:
            projectObject["primaryLayers"] = [projectConfig["focusImageLayer"]]
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
        item = self._createItem()
        self._logger.info("Created item. Item id: {0}".format(item.id))

        # share items with organization
        if self.shareWithOrg:
            self._shareItems(item)

        return item.id


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
        userManager = self._gis.users
        userInfo = userManager.get(self.username)
        for f in userInfo.folders:
            if f["title"] == name:
                return {"new": False, "id": f["id"]}

        # if we made it here a new folder needs to be created
        createFolderResponse = self._gis.content.create_folder(name)
        return {"new": True, "id": createFolderResponse["id"]}


    def _createItem(self):
        """
        Private method that adds the Imagery Project item to the portal.

        Returns:
            item: An arcgis.gis.Item object
        """

        item = {"title": self._itemObject["title"]}
        item["snippet"] = self._itemObject["snippet"]
        item["type"] = "Excalibur Imagery Project"
        item["typeKeywords"] = "{0}".format(
            self._itemObject["status"])
        item["tags"] = "Image Project"
        item["text"] = json.dumps(self._projectObject)

        addItemResponse = self._gis.content.add(item, folder=self._folderName)
        return addItemResponse


    def _getProjectFromFolder(self, folderId, projectName):
        """
        Private method that queries the portal to find an Imagery Project item in a folder.

        Parameters:
            folderId (string): The id of the folder to search
            projectName (string): Name of the Imagery Project

        Returns:
            item: An arcgis.gis.Item object
        """

        queryString = "ownerfolder:{0} title:\"{1}\"".format(
            folderId, projectName)

        searchResults = self._gis.content.search(queryString, item_type="Excalibur Imagery Project")

        if len(searchResults):
            return searchResults[0].id
        else:
            return None


    def _shareItems(self, projectItem):
        """
        Private method that shares the project item with the portal organization

        Parameters:
            projectItem (arcgis.gis.Item): The Imagery Project item
        """

        return projectItem.share(org=True)
