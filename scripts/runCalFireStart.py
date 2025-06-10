from os import path

import argparse
import getpass
import json

from calFire import CalFireCreator

# Path to directory that holds files with configuration info
APP_CONFIG_DIR = r"..\config"

# Set up expected arguments
parser = argparse.ArgumentParser(
    description="Start a livestream video service")
parser.add_argument("serviceUrl", help="url to video service to start")
parser.add_argument("-s", "--sharingurl",
                    help="portal sharing url. If not specified, the url in the paths.json is used")
parser.add_argument("-u", "--user", help="portal user name")
parser.add_argument("-p", "--password", help="password for portal user")

if __name__ == "__main__":
  try:
    # Parse arguments and prompt user for missing ones
    args = parser.parse_args()

    if not args.serviceUrl:
      raise Exception("service url must be supplied")

    sharingUrlFromPaths = None

    filePath = path.join(APP_CONFIG_DIR, "paths.json")
    with open(filePath) as pathsFile:
        pathsJson = pathsFile.read()
        pathsJson = json.loads(pathsJson)
        sharingUrlFromPaths = pathsJson["SHARING_URL"]

    username = args.user
    password = args.password
    portalUrl = args.sharingurl

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

    # Start service
    print("Starting service")
    theCreator.startService(serviceUrl=args.serviceUrl)
    print("Started service")

  except Exception as e:
    print("Error starting service: {0}".format(e))
