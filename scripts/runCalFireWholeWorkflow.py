from os import path

import argparse
import getpass
import json

from calFire import CalFireCreator

# Path to directory that holds files with configuration info
APP_CONFIG_DIR = r"..\config"

# Set up expected arguments
parser = argparse.ArgumentParser(
    description="Publish a GeoJson service")
parser.add_argument("geoJsonfileName", help="name of GeoJson file")
parser.add_argument("projectConfigFileName", help="name of file holding project config info")
parser.add_argument("-r", "--rtsp", help="url to the video stream. If not specified, the url in the paths.json is used")
parser.add_argument("-g", "--groupid", help="item id of group to share service and web map with")
parser.add_argument("-o", "--org", help="boolean flag to share service and web map with organization")

parser.add_argument("-u", "--user", help="portal user name")
parser.add_argument("-p", "--password", help="password for portal user")

if __name__ == "__main__":
  try:
    # Parse arguments and prompt user for missing ones
    args = parser.parse_args()

    geoJsonfileName = args.geoJsonfileName
    projectFileName = args.projectConfigFileName

    if not geoJsonfileName:
      raise Exception("geojson file name must be supplied")

    if not projectFileName:
      raise Exception("project file name must be supplied")

    # Name of the geojson file w/o the file extension is used to name
    # all pieces of the project
    baseGeoJsonFileName = geoJsonfileName
    if (geoJsonfileName.endswith(".geojson") != True):
      geoJsonfileName = geoJsonfileName + ".geojson"
    else:
      baseGeoJsonFileName = geoJsonfileName.replace(".geojson", "")

    groupId = args.groupid
    shareWithOrg = args.org

    sharingUrlFromPaths = None
    dataDirFromPaths = None
    videoServerUrlFromPaths = None
    videoStreamFromPaths = None
    projectConfigDir = None

    filePath = path.join(APP_CONFIG_DIR, "paths.json")
    with open(filePath) as pathsFile:
      pathsJson = pathsFile.read()
      pathsJson = json.loads(pathsJson)
      sharingUrlFromPaths = pathsJson["SHARING_URL"]
      dataDirFromPaths = pathsJson["GEOJSON_DATA_DIR"]
      videoServerUrlFromPaths = pathsJson["VIDEO_SERVER_URL"]
      videoStreamFromPaths = pathsJson["URL_TO_VIDEO_STREAM"]
      projectConfigDir = pathsJson["PROJECT_CONFIG_DIR"]

    # Check if all urls are set
    if not sharingUrlFromPaths:
      raise Exception("Missing portal url. The portal sharing url must be in the paths.json's SHARING_URL property")

    if not dataDirFromPaths:
      raise Exception("Missing data directory path. The path must be in the paths.json's GEOJSON_DATA_DIR property")

    if not videoServerUrlFromPaths:
      raise Exception("Missing video server url. The url must be in the paths.json's VIDEO_SERVER_URL property")

    if not videoStreamFromPaths:
      raise Exception("Missing video stream url. The url must be in the paths.json's URL_TO_VIDEO_STREAM property")

    if not projectConfigDir:
      raise Exception("Missing project config directory path. The path must be in the paths.json's PROJECT_CONFIG_DIR property")

    # Check if geojson file exists
    geoJsonPath = path.join(dataDirFromPaths, geoJsonfileName)
    if not path.exists(geoJsonPath):
      message = "Geo json file not found: {0}".format(geoJsonPath)
      raise Exception(message)

    # Check if the project json file exists - add .json extension if needed
    if (projectFileName.endswith(".json") != True):
        projectFileName = projectFileName + ".json"

    projectFilePath = path.join(projectConfigDir, projectFileName)
    if not path.exists(projectFilePath):
        message = "Project config file not found: {0}".format(projectFilePath)
        raise Exception(message)

    # Prompt for user name and password if needed
    username = args.user
    password = args.password

    if not username:
      username = input("Enter user name: ")
    if not username:
      print("username must be supplied")
      raise Exception("Username must be supplied")

    if not password:
      password = getpass.getpass(
        "Enter password for user {0}: ".format(username))
    if not password:
      print("password must be supplied")
      raise Exception("Password must be supplied")

    # Make new CalFireCreator
    theCreator = CalFireCreator(username=username, password=password, portalSharingUrl=sharingUrlFromPaths, videoServerUrl=videoServerUrlFromPaths)

    # Load project json
    projectJson = None
    with open(projectFilePath) as projectFile:
       projectJson = projectFile.read()
    projectJson = json.loads(projectJson)

    # Publish GeoJson and add layer to web map
    print("*** Publishing GeoJson and updating web map ***")
    webmapId = None
    if "webmapId" in projectJson:
      webmapId = projectJson["webmapId"]

    webmapItemId = theCreator.publishGeoJsonAndUpdateWebmap(path=geoJsonPath, webmapId=webmapId, groupIdToShareWith=groupId, shareWithOrg=shareWithOrg)
    print("*** Published GeoJson and updated web map - web map itemId: {0} ***".format(webmapItemId))

    # Make video service
    print("*** Publishing video service ***")
    serviceInfo = theCreator.createVideoService(serviceName=baseGeoJsonFileName, urlToStream=videoStreamFromPaths, groupIdToShareWith=groupId, shareWithOrg=shareWithOrg, startStream=False)
    print("*** Published video service ***")

    # Make project
    print("*** Creating project ***")

    projectItemId = theCreator.createProject(projectConfig=projectJson, videoLayerItemId=serviceInfo["serviceItemId"], videoLayerUrl=serviceInfo["serviceUrl"], webmapId=webmapItemId, groupIdToShareWith=groupId, shareWithOrg=shareWithOrg)
    print("project made - itemId: {0} ".format(projectItemId))
    print("service made - url: {0}".format(serviceInfo["serviceUrl"]))

  except Exception as e:
    print("Error publishing GeoJson and updating web map: {0}".format(e))
