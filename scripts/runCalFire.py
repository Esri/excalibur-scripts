from os import path

import argparse
import getpass
import json

from calFire import CalFireCreator

# Path to directory that holds files with configuration info
APP_CONFIG_DIR = r"..\config"

# Set up expected arguments
parser = argparse.ArgumentParser(
    description="Create a video service and an imagery project using the service")
parser.add_argument(
    "configFileName", help="name of file containing imagery project configuration")
parser.add_argument("serviceName", help="name of video service to create")
parser.add_argument("-s", "--sharingurl",
                    help="portal sharing url. If not specified, the url in the paths.json is used")
parser.add_argument("-v", "--videoserverurl",
                    help="url to the video server. If not specified, the url in the paths.json is used")
parser.add_argument("-r", "--rtsp", help="url to the video stream. If not specified, the url in the paths.json is used")
parser.add_argument("-u", "--user", help="portal user name")
parser.add_argument("-p", "--password", help="password for portal user")

if __name__ == "__main__":
  try:
    # Parse arguments and prompt user for missing ones
    args = parser.parse_args()

    projectConfigDir = None
    sharingUrlFromPaths = None
    videoServerUrlFromPaths = None
    videoStreamFromPaths = None

    filePath = path.join(APP_CONFIG_DIR, "paths.json")
    with open(filePath) as pathsFile:
        pathsJson = pathsFile.read()
        pathsJson = json.loads(pathsJson)
        projectConfigDir = pathsJson["PROJECT_CONFIG_DIR"]
        sharingUrlFromPaths = pathsJson["SHARING_URL"]
        videoServerUrlFromPaths = pathsJson["VIDEO_SERVER_URL"]
        videoStreamFromPaths = pathsJson["URL_TO_VIDEO_STREAM"]

    # Check if the project json file exists - add .json extension if needed
    fileName = args.configFileName
    if (fileName.endswith(".json") != True):
        fileName = fileName + ".json"

    filePath = path.join(projectConfigDir, fileName)
    if not path.exists(filePath):
        message = "Project config file not found: {0}".format(filePath)
        raise Exception(message)

    # Check if the service name arg got set
    videoServiceName = args.serviceName
    if (not videoServiceName):
        raise Exception("serviceName argument is required")

    username = args.user
    password = args.password
    portalUrl = args.sharingurl
    videoServerUrl = args.videoserverurl
    videoStreamUrl = args.rtsp

    # Check if all urls are set
    portalUrl = portalUrl or sharingUrlFromPaths
    if not portalUrl:
      raise Exception("Missing portal url. The portal sharing url must be in the --sharingurl argument or in the paths.json's SHARING_URL property")

    videoServerUrl = videoServerUrl or videoServerUrlFromPaths
    if not videoServerUrl:
      raise Exception("Missing video server url. The video server url must be in the --videoserverurl argument or in the paths.json's VIDEO_SERVER_URL property")

    videoStreamUrl = videoStreamUrl or videoStreamFromPaths
    if not videoStreamUrl:
      raise Exception("Missing video stream url. The video stream url must be in the --rtsp argument or in the paths.json's URL_TO_VIDEO_STREAM property")

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
    theCreator = CalFireCreator(username=username, password=password, portalSharingUrl=portalUrl, videoServerUrl=videoServerUrl)

    # Make service
    serviceItemId = theCreator.createService(serviceName=videoServiceName, urlToStream=videoStreamUrl)
    print("Service created: {0}".format(serviceItemId))

  except Exception as e:
    print("Error creating project: {0}".format(e))
