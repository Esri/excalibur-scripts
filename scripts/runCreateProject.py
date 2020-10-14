"""
A script that uses the ProjectCreator class to create an Excalibur Imagery Project in a Portal.

Information about parameters can be viewed by running the script with the -h flag
"""

from os import path

import logging
import logging.config

import argparse
import getpass
import json

from createProject import ProjectCreator

# Path to directory that holds files with configuration info
APP_CONFIG_DIR = r"..\config"

# Path to log file configuration
LOG_CONFIG_FILE_NAME = path.join(APP_CONFIG_DIR, "logging.conf")

# Set up expected arguments
parser = argparse.ArgumentParser(
    description="Create an imagery project from a json config file")
parser.add_argument(
    "configFileName", help="name of file containing imagery project configuration")
parser.add_argument("-s", "--sharingurl",
                    help="portal sharing url. if not specified, the 'SHARING_URL' property of 'config/paths.json' is used")
parser.add_argument("-o", "--orgshare",
                    help="flag to share the project with the organization. The default is False.", type=bool, default=False)
parser.add_argument("-u", "--user", help="portal user name")
parser.add_argument("-p", "--password", help="password for portal user")

if __name__ == "__main__":
    # Parse arguments and prompt user for missing ones
    args = parser.parse_args()

    logging.config.fileConfig(LOG_CONFIG_FILE_NAME)
    logger = logging.getLogger("imageProject.start")

    projectConfigDir = None
    sharingUrlFromPaths = None

    filePath = path.join(APP_CONFIG_DIR, "paths.json")
    with open(filePath) as pathsFile:
        pathsJson = pathsFile.read()
        pathsJson = json.loads(pathsJson)
        projectConfigDir = pathsJson["PROJECT_CONFIG_DIR"]
        sharingUrlFromPaths = pathsJson["SHARING_URL"]

    # Check if the project json file exists - add .json extension if needed
    fileName = args.configFileName
    if (fileName.endswith(".json") != True):
        fileName = fileName + ".json"

    filePath = path.join(projectConfigDir, fileName)
    if not path.exists(filePath):
        message = "Project config file not found: {0}".format(filePath)
        raise Exception(message)

    username = args.user
    password = args.password
    portalUrl = args.sharingurl
    shareWithOrg = args.orgshare

    print("orgshare argument: {}".format(args.orgshare))
    print("shareWithOrg variable: {}".format(shareWithOrg))

    projectJson = None
    questionJson = None

    try:
        # open projectJson to get portal sharing url
        with open(filePath) as projectFile:
            projectJson = projectFile.read()

        projectJson = json.loads(projectJson)

        portalUrl = portalUrl or sharingUrlFromPaths

        if not portalUrl:
            raise Exception(
                "Missing portal url. The portal sharing url must be in the --sharingurl argument or in the project config's SHARING_URL property")

        # Ask for admin user name and password if needed
        print("Portal sharing url is {0}".format(portalUrl))
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

        print("Creating project!!!!")
        theCreator = ProjectCreator(
            username, password, portalUrl, shareWithOrg)
        itemId = theCreator.makeProject(projectJson)

        print("Project successfully created. Item ID is: {0}".format(itemId))
        logger.info(
            "Project successfully created. Item ID is: {0}".format(itemId))

    except Exception as e:
        logger.error("Error creating project: {0}".format(e))
        print("Error creating project: {0}".format(e))