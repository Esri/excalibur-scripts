import json
import requests

# Flag to not verify SSL certificate when making https request.
# Change to True to verify SSL certificates
VERIFY_SSL = False

class CalFireCreator:
  def __init__(self, username, password, portalSharingUrl, videoServerUrl):
    """
    Constructor for the CalFireCreator class

    Parameters:
        username (string): The username of a portal member who has permissions to create content
        password (string): The password for the user
        portalSharingUrl (string): The url to the 'sharing' endpoint that is the base url for REST calls.
            Format is https://<domain>/<webadaptor>/sharing/rest
        videoServerUrl (string): The url to the video server endpoint. Format is https://<domain>/<webadaptor>
    """
    if not username or not password or not portalSharingUrl or not videoServerUrl:
        raise Exception("Missing argument(s). Supply username, password, portalSharingUrl, and videoServerUrl")

    # Urls and other info to access and create items in portal
    # and to create a video service
    self.portalSharingUrl = portalSharingUrl.rstrip("/")
    self.videoServerUrl = videoServerUrl.rstrip("/")
    self.username = username
    self.password = password

    self.contentUrl = self.portalSharingUrl + "/content/users/" + username
    self.videoServerRestUrl = self.videoServerUrl + "/rest/services"

    # portal token
    self.token = self._getToken()

  def createService(self, serviceName, urlToStream):
    """
    Method that creates the video service. An exception is raised if a service with the same name exists

    Parameters:
        serviceName (string): The name of the service to create
        urlToStream (string): The url to the video stream

    Returns:
        string: The itemId of the created service.
    """

    # Check if service is available
    serviceExists = self._videoServiceNameExists(serviceName)
    if (serviceExists):
       raise Exception("Service name is not available")

    # Create the service on the portal
    print("Creating service")
    serviceItemId = self._createService(serviceName=serviceName, urlToStream=urlToStream)
    print("Service created - itemId: {0}".format(serviceItemId))
    return serviceItemId


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


  def _createService(self, serviceName, urlToStream):
    """
    Method creates the video service and adds a layer to it

    Returns:
        string: item id of service
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
    serviceUrl = createServiceresponse["serviceurl"] + "/addLayer"

    r = requests.post(serviceUrl, data=data, verify=VERIFY_SSL)
    if (r.status_code != 200):
      raise Exception("Error creating service on portal. Bad status code: {0}".format(r.status_code))

    addLayerResponse = r.json()
    if "error" in addLayerResponse:
      message = "Error creating service on portal: {!s}".format(
        addLayerResponse["error"])
      raise Exception(message)

    return createServiceresponse["itemId"]


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