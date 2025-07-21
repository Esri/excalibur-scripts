from os import path

import json
import requests

import ntpath

# Flag to not verify SSL certificate when making https request.
# Change to True to verify SSL certificates
VERIFY_SSL = False

# Path to directory that holds files with configuration info
APP_CONFIG_DIR = r"..\config"

# Project version to use if none is specified in the project JSON
DEFAULT_PROJECT_VERSION = "4.0"

# Renderer for geo json polygon
GEOJSON_RENDERER = {
  "drawingInfo": {
    "renderer": {
      "type": "simple",
      "symbol": {
        "type": "esriSFS",
        "color": [
          235,
          21,
          21,
          38
        ],
        "outline": {
          "type": "esriSLS",
          "color": [
            235,
            21,
            21,
            255
          ],
          "width": 1.448,
          "style": "esriSLSDash"
        },
        "style": "esriSFSSolid"
      }
    }
  }
}

class CalFireCreator:
  def __init__(self, username, password, portalSharingUrl, videoServerUrl=""):
    """
    Constructor for the CalFireCreator class

    Parameters:
        username (string): The username of a portal member who has permissions to create content
        password (string): The password for the user
        portalSharingUrl (string): The url to the 'sharing' endpoint that is the base url for REST calls.
            Format is https://<domain>/<webadaptor>/sharing/rest
        videoServerUrl (string): The url to the video server endpoint. Format is https://<domain>/<webadaptor>
    """
    if not username or not password or not portalSharingUrl:
        raise Exception("Missing argument(s). Supply username, password, portalSharingUrl")

    # Urls and other info to access and create items in portal
    # and to create a video service
    self.portalSharingUrl = portalSharingUrl.rstrip("/")
    self.username = username
    self.password = password

    if videoServerUrl != "":
      videoServerUrl = videoServerUrl.rstrip("/")
      self.videoServerRestUrl = videoServerUrl + "/rest/services"

    self.contentUrl = self.portalSharingUrl + "/content/users/" + username

    # portal token
    self.token = self._getToken()

  #----------------------------
  # createProject
  #----------------------------
  def createProject(self, projectConfig, videoLayerItemId, videoLayerUrl, webmapId, groupIdToShareWith, shareWithOrg=False):
    """
    The function to create the portal item that represents the Excalibur Imagery Project.
    The project item gets shared with the organization

    Parameters:
        projectConfig (JSON object) The JSON describing the properties of the Excalibur Imagery Project.
        videoLayerItemId (string) The item id of the video analysis layer
        videoLayerUrl (string) The url to the video analysis layer
        webmapId (string) Item ID of web map to use for project
        groupIdToShareWith (string) Id of group to share project with
        shareWithOrg (boolean) Flag to share project with portal organization

    Returns:
        string: The itemid of the Excalibur Imagery Project portal item.
    """

    # Make local object with portal item info and object with item data info.
    title = projectConfig["title"]

    itemObject = {"title": title}
    projectObject = {"version": DEFAULT_PROJECT_VERSION}

    if "summary" in projectConfig:
      itemObject["snippet"] = projectConfig["summary"]

    if "instructions" in projectConfig:
      projectObject["instructions"] = projectConfig["instructions"]

    # add primary layer info to project object
    primaryLayer = {"itemId": videoLayerItemId, "serviceUrl": videoLayerUrl, "serviceType": "video"}
    projectObject["primaryLayers"] = [primaryLayer]

    # add webmapId to project object
    projectObject["webmapId"] = webmapId

    # create folder if needed
    folderResponse = self._createFolder(title)
    self.folderId = folderResponse["id"]

    # if folder already exists check if there is a project in it
    if folderResponse["new"] == False:
      existingProject = self._getProjectFromFolder(folderResponse["id"], title)
      if existingProject:
        raise Exception("Cannot create project. One with the same name already exists")

    # create the project portal item and share it
    projectItemId = self._createProjectItem(itemObject=itemObject, projectObject=projectObject)
    self._shareItem(projectItemId, groupId=groupIdToShareWith, shareWithOrg=shareWithOrg)

    return projectItemId

  #----------------------------
  # createVideoService
  #----------------------------
  def createVideoService(self, serviceName, urlToStream, groupIdToShareWith, shareWithOrg=False, startStream=False):
    """
    Method that creates the video service. An exception is raised if a service with the same name exists

    Parameters:
        serviceName (string): The name of the service to create
        urlToStream (string): The url to the video stream
        groupIdToShareWith (string): The id of the group to share the service with
        shareWithOrg (boolean): Flag to share the service with the organization

    Returns:
        object: The itemId of the created service and the url to the created service.
    """

    # Check if service is available
    serviceExists = self._videoServiceNameExists(serviceName)
    if (serviceExists):
       raise Exception("Service name is not available")

    if shareWithOrg == "True" or shareWithOrg == True:
      shareWithOrg = True

    # Create the service on the portal
    createServiceResponse = self._createVideoService(serviceName=serviceName, urlToStream=urlToStream)

    serviceItemId = createServiceResponse["itemId"]
    serviceUrl = createServiceResponse["url"]

    # Share the service item with the organization
    self._shareItem(itemId=serviceItemId, groupId=groupIdToShareWith, shareWithOrg=shareWithOrg)

    # Start the stream
    if (startStream):
      self.startService(serviceUrl=serviceUrl)

    return {"serviceItemId": serviceItemId, "serviceUrl": serviceUrl}

  #---------------------------------
  # publishGeoJsonAndUpdateWebmap
  #---------------------------------
  def publishGeoJsonAndUpdateWebmap(self, path, webmapId=None, groupIdToShareWith=None, shareWithOrg=False):
    """
    Method that makes a web map if needed, publishes a geojson file to the portal and makes
    a feature service. Then adds the service as a layer to the webmap
    and shares the geojson service with the group

    Parameters:
        path (string): Path to geojson file
        webmapId (string) Item id of web map item. A new web map gets created if this property is not supplied
        groupIdToShareWith (string): Id of group to share service with
        shareWithOrg (boolean): Flag to share service with organization

    Returns:
        string: The itemid of the Web Map portal item created.
    """
    if not path:
      raise Exception("path to file is required")

    if shareWithOrg == "True" or shareWithOrg == True:
      shareWithOrg = True

    filename = ntpath.basename(path)
    layerName = filename.replace(".geojson", "")

    # if 'webmapId' property not set make web map and share it
    if not webmapId or webmapId == "":
      webmapId = self._createWebMap(layerName)
    self._shareItem(webmapId, groupId=groupIdToShareWith, shareWithOrg=shareWithOrg)

    # upload and publish geo json
    serviceInfo = self._publishGeoJson(path=path)

    # share service with group
    self._shareItem(serviceInfo["serviceItemId"], groupId=groupIdToShareWith, shareWithOrg=shareWithOrg)

    # add service to webmap
    if webmapId:
      self._addServiceToWebMap(serviceInfo=serviceInfo, webmapId=webmapId, layerName=layerName)

    return webmapId


  #-------------------------
  # startService
  #-------------------------
  def startService(self, serviceUrl):
    startUrl = serviceUrl + "/0/start"
    data = {"stopOn": "request", "f": "json", "token": self.token}

    r = requests.post(startUrl, data=data, verify=VERIFY_SSL)
    if (r.status_code != 200):
      raise Exception("Error starting service. Bad status code: {0}".format(r.status_code))

    response = r.json()
    if "error" in response:
      message = "Error starting service: {!s}".format(
        response["error"])
      raise Exception(message)

    return

  #----------------------------
  # _addServiceToWebMap
  #----------------------------
  def _addServiceToWebMap(self, webmapId, serviceInfo, layerName):
    if not webmapId or not serviceInfo or not layerName:
      raise Exception("webmapId, serviceInfo and layerName are required")

    # get current web map data
    token = self.token
    requestData = {"f": "json"}
    requestData["token"] = token

    itemDataUrl = self.portalSharingUrl + "/content/items/" + webmapId + "/data"
    r = requests.get(itemDataUrl, params=requestData, verify=VERIFY_SSL)

    if (r.status_code != 200):
      raise Exception("Error publishing geo json - status code: {0}".format(r.status_code))

    response = r.json()
    if "error" in response:
      message = "Error publishing geo json: {0}".format(json.dumps(response["error"]))
      raise Exception(message)

    # add service to web map operational layers
    layerJson = {"id": layerName + "cal-fire"}
    layerJson["title"] = layerName
    layerJson["url"] = serviceInfo["serviceurl"]
    layerJson["itemId"] = serviceInfo["serviceItemId"]
    layerJson["layerType"] = "ArcGISFeatureLayer"
    layerJson["layerDefinition"] = GEOJSON_RENDERER

    response["operationalLayers"].insert(0, layerJson)

    # add layer to web map by updating web map item data
    updateUrl = self.contentUrl + "/items/" + webmapId + "/update"
    requestData = {"f": "json"}
    requestData["token"] = token
    requestData["text"] = json.dumps(response)

    r = requests.post(updateUrl, data=requestData, verify=VERIFY_SSL)

    if (r.status_code != 200):
      raise Exception("Error adding layer to map - status code: {0}".format(r.status_code))

    response = r.json()
    if "error" in response:
      message = "Error publishing geo json: {0}".format(json.dumps(response["error"]))
      raise Exception(message)
    elif not response["success"]:
      raise Exception("Adding layer was not successful")

    return True


  #----------------------------
  # _createFolder
  #----------------------------
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
    url = self.contentUrl
    data = {"f": "json", "token": self.token, "num": 1}

    r = requests.get(url, params=data, verify=VERIFY_SSL)

    if (r.status_code != 200):
      raise Exception("Error in htttp request to get existing folders: {0}".format(r.status_code))

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
    url = self.contentUrl + "/createFolder"

    data = {"f": "json", "token": self.token, "title": name}

    r = requests.post(url, data=data, verify=VERIFY_SSL)

    if r.status_code != 200:
      raise Exception("Error in http request to create folder: {0}".format(r.status_code))

    response = r.json()
    if not "success" in response or not response["success"]:
      message = "Error creating folder: {!s}".format(
          json.dumps(response["error"]["message"]))
      raise Exception(message)

    return {"new": True, "id": response["folder"]["id"]}


  #-----------------------------
  # _createProjectItem
  #-----------------------------
  def _createProjectItem(self, itemObject, projectObject):
    """
    Private method that adds the Imagery Project item to the portal.

    Returns:
        string: The id of the ImageryProject item
    """
    url = self.contentUrl + "/" + self.folderId + "/addItem"

    itemObject["f"] = "json"
    itemObject["token"] = self.token
    itemObject["type"] = "Excalibur Imagery Project"
    itemObject["text"] = json.dumps(projectObject)

    r = requests.post(url, data=itemObject, verify=VERIFY_SSL)
    if (r.status_code != 200):
      raise Exception("Error creating project object: {0}".format(r.status_code))

    response = r.json()
    if "error" in response:
      message = "Error creating project object: {0}".format(json.dumps(response["error"]))
      raise Exception(message)

    return response["id"]

  #-----------------------------
  # _getProjectFromFolder
  #-----------------------------
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
    data = {"f": "json", "token": self.token, "q": queryString}

    r = requests.get(url, params=data, verify=VERIFY_SSL)

    if r.status_code != 200:
      message = "Error searching for project: {0}".format(r.status_code)
      raise Exception(message)

    response = r.json()

    if response["total"] > 0:
      return response["results"][0]
    else:
      return


  #----------------------------
  # _getToken
  #----------------------------
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


  #----------------------------
  # _createVideoService
  #----------------------------
  def _createVideoService(self, serviceName, urlToStream):
    """
    Method creates the video service and adds a layer to it

    Returns:
        object: object with the service url and item id ofthe service portal item
    """

    # Create empty service
    createParameters = {}
    createParameters["serviceName"] = serviceName
    createParameters = json.dumps(createParameters)

    data = {"createParameters": createParameters, "outputType": "videoService", "f": "json", "token": self.token}
    url = self.contentUrl + "/createService"

    r = requests.post(url, data=data, verify=VERIFY_SSL)
    if (r.status_code != 200):
      raise Exception("Error creating service on portal. Bad status code: {0}".format(r.status_code))

    createServiceresponse = r.json()
    if "error" in createServiceresponse:
      message = "Error creating service on portal: {!s}".format(
        createServiceresponse["error"])
      raise Exception(message)

    # Add layer to service
    layerParameter = {"bufferSize": 10, "cameraInfo": None, "mode": "client"}
    layerParameter["name"] = serviceName
    layerParameter["recordStream"] = True
    layerParameter["start"] = "request"
    layerParameter["stop"] = "auto"
    layerParameter["streamAddress"] = urlToStream
    layerParameter["type"] = "livestream"
    layerParameter = json.dumps(layerParameter)

    data = {"layer": layerParameter, "f": "json", "token": self.token}
    addLayerUrl = createServiceresponse["serviceurl"] + "/addLayer"

    r = requests.post(addLayerUrl, data=data, verify=VERIFY_SSL)
    if (r.status_code != 200):
      raise Exception("Error creating service on portal. Bad status code: {0}".format(r.status_code))

    addLayerResponse = r.json()
    if "error" in addLayerResponse:
      message = "Error creating service on portal: {!s}".format(
        addLayerResponse["error"])
      raise Exception(message)

    serviceItemId = createServiceresponse["itemId"]
    serviceUrl = createServiceresponse["serviceurl"]
    return {"itemId": serviceItemId, "url": createServiceresponse["serviceurl"]}


  #----------------------------
  # _createWebMap
  #----------------------------
  def _createWebMap(self, title):
    if not title:
      raise Exception("_createWebMap::title is required")

    projectConfigDir = ""

    filePath = path.join(APP_CONFIG_DIR, "paths.json")
    with open(filePath) as pathsFile:
        pathsJson = pathsFile.read()
        pathsJson = json.loads(pathsJson)
        projectConfigDir = pathsJson["PROJECT_CONFIG_DIR"]

    webmapJson = None
    webmapFilePath = path.join(projectConfigDir, "base-webmap-sample.json")
    with open(webmapFilePath) as webmapFile:
      webmapJson = webmapFile.read()

    url = self.contentUrl + "/addItem"

    itemJson = {"title": title, "type": "Web Map"}
    itemJson["text"] = webmapJson
    itemJson["f"] = "json"
    itemJson["token"] = self.token

    r = requests.post(url, data=itemJson, verify=VERIFY_SSL)
    if (r.status_code != 200):
      raise Exception("Error creating webmap on portal. Bad status code: {0}".format(r.status_code))

    createMapResponse = r.json()
    if "error" in createMapResponse:
      message = "Error creating webmap on portal: {!s}".format(
        createMapResponse["error"])
      raise Exception(message)

    return createMapResponse["id"]


  #---------------------------
  # _publishGeoJson
  #---------------------------
  def _publishGeoJson(self, path):
    """
      Method that publishes a geojson file as a feature service

      Parameters:
          path (string): Path to geojson file
    """
    if not path:
      raise Exception("path to file is required")

    # upload file
    filename = ntpath.basename(path)
    serviceName = filename.replace(".geojson", "")

    token = self.token

    # Use multipart-encoded file params to make upload request
    # The geojson file gets uploaded first and then published as a service.
    files = {"file": (filename, open(path, "rb"))}
    files["title"] = (None, serviceName)
    files["type"] = (None, "GeoJson")
    files["f"] = (None, "json")
    files["token"] = (None, token)

    url = self.contentUrl + "/addItem"

    r = requests.post(url, files=files, verify=VERIFY_SSL)
    if (r.status_code != 200):
      raise Exception("Error publishing geo json - status code: {0}".format(r.status_code))

    response = r.json()
    if "error" in response:
      message = "Error publishing geo json: {0}".format(json.dumps(response["error"]))
      raise Exception(message)
    elif not response["success"]:
      raise Exception("Publishing GeoJson was not successful")

    # publish to make feature service
    publishParameters = {}
    publishParameters["name"] = serviceName

    publishItemParams = {"itemId": response["id"]}
    publishItemParams["publishParameters"] = json.dumps(publishParameters)
    publishItemParams["filetype"] = "geojson"
    publishItemParams["f"] = "json"
    publishItemParams["token"] = token

    url = self.contentUrl + "/publish"
    r = requests.post(url, data=publishItemParams, verify=VERIFY_SSL)
    if (r.status_code != 200):
      raise Exception("Error publishing geo json - status code: {0}".format(r.status_code))

    response = r.json()
    if "error" in response:
      message = "Error publishing geo json: {0}".format(json.dumps(response["error"]))
      raise Exception(message)

    return response["services"][0]

  #----------------------------
  # _shareItem
  #----------------------------
  def _shareItem(self, itemId, groupId, shareWithOrg=False):
    """
    Method that shares the an item with the group and optionally with portal organization

    Parameters:
        itemId (string): The id of the item
        groupId (string): The id of the group to share item with
        shareWithOrg: Boolean flag to share item with portal organization
    """

    url = self.contentUrl + "/shareItems"
    data = {"f": "json", "token": self.token}
    data["org"] = shareWithOrg
    data["items"] = itemId

    if groupId:
      data["groups"] = groupId

    r = requests.post(url, data=data, verify=VERIFY_SSL)

    if r.status_code != 200:
      message = "Error sharing items. Http code: {0}".format(r.status_code)
      raise Exception(message)

    response = r.json()
    if "error" in response:
      message = "Error sharing item: {!s}".format(response["error"])
      raise Exception(message)

    return response

  #----------------------------
  # _videoServiceNameExists
  #----------------------------
  def _videoServiceNameExists(self, serviceName):
    """
    Method that checks if a video service already exists with the input serviceName

    Parameters:
        serviceName (string): The name of the service

    Returns:
        boolean: True if the service name already exists, False if not
    """
    data = {"f": "json", "serviceName": serviceName, "token": self.token}
    url = self.videoServerRestUrl + "/isServiceNameAvailable"

    r = requests.get(url, params=data, verify=VERIFY_SSL)
    if (r.status_code != 200):
      raise Exception("Error in http request to find if service exists")

    response = r.json()
    if "error" in response:
      message = "Error making request to see if service exists: {!s}".format(
        response["error"])
      raise Exception(message)

    return not response["available"]