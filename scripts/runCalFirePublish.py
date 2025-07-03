from os import path

import argparse
import getpass
import json

from calFire import CalFireCreator

# Path to directory that holds files with configuration info
APP_CONFIG_DIR = r"..\config"

# Path to directory with GeoJson data files


# Set up expected arguments
parser = argparse.ArgumentParser(
    description="Publish a GeoJson service")
parser.add_argument("fileName", help="name of GeoJson file")
parser.add_argument("webmapId", help="item id of web map")
parser.add_argument("-s", "--sharingurl", help="portal sharing url. If not specified, the url in the paths.json is used")
parser.add_argument("-u", "--user", help="portal user name")
parser.add_argument("-p", "--password", help="password for portal user")

if __name__ == "__main__":
  try:
    # Parse arguments and prompt user for missing ones
    args = parser.parse_args()

    fileName = args.fileName
    webmapId = args.webmapId
    if not fileName:
      raise Exception("file name must be supplied")
    if not webmapId:
      raise Exception("webmapId is required")

    if (fileName.endswith(".geojson") != True):
        fileName = fileName + ".geojson"

    sharingUrlFromPaths = None
    dataDirFromPaths = None

    filePath = path.join(APP_CONFIG_DIR, "paths.json")
    with open(filePath) as pathsFile:
        pathsJson = pathsFile.read()
        pathsJson = json.loads(pathsJson)
        sharingUrlFromPaths = pathsJson["SHARING_URL"]
        dataDirFromPaths = pathsJson["GEOJSON_DATA_DIR"]

    username = args.user
    password = args.password
    portalUrl = args.sharingurl

    geoJsonPath = path.join(dataDirFromPaths, fileName)

    # Check if all urls are set
    portalUrl = portalUrl or sharingUrlFromPaths
    if not portalUrl:
      raise Exception("Missing portal url. The portal sharing url must be in the --sharingurl argument or in the paths.json's SHARING_URL property")

    # Prompt for user name and password if needed
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
    theCreator = CalFireCreator(username=username, password=password, portalSharingUrl=portalUrl)

    # Publish GeoJson and add layer to web map
    print("Publishing GeoJson and updating web map")
    itemId = theCreator.publishGeoJsonAndUpdateWebmap(path=geoJsonPath, webmapId=webmapId)
    print("Published GeoJson and updated web map - service itemId: {0}".format(itemId))

  except Exception as e:
    print("Error publishing GeoJson and updating web map: {0}".format(e))
