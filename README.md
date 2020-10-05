# Scripted Excalibur Imagery Project Creation

## Description
This repository contains Python scripts and sample configuration files that can be used to create Excalibur Imagery Projects outside of the Excalibur application.

To get the scripts and configuration files clone this repository or download it as a zip file and extract the contents to your machine.

Included:
* Sample JSON files that define an Imagery Project
* Sample JSON files that define overall configuration definitions for running the scripts
* Python scripts that create an Imagery Project in a portal

## Requirements

### Python 3

The scripts require Python 3 to be installed on your machine. The scripts were developed using Python version 3.8.6. Python 3 is already installed on your machine if you are running ArcGIS Pro. To see if Python is installed, open a terminal and run the command `python`. You should see the version of Python displayed and be at a command prompt for entering Python commands.

If Python is not installed on your machine, you can download the version for your OS from the [Python download site](https://www.python.org/downloads/). It is recommended to add the path to the Python executable to the `Paths` on your machine. Once installed, open a terminal and run the command `python`. You should see the version of Python displayed and be at a command prompt for entering Python commands.

### Requests library

**Requests** is a Python library that simplifies making http requests. To install it, in a terminal run the command `python -m pip install requests`

### ArcGIS Enterprise Instance

Excalibur is a Portal application that is supported on ArcGIS Enterprise version 10.7 and higher. To run the scripts, you must be a user on an ArcGIS Enterprise instance and you must have permissions to create new items.

## Explanation of directory structure

### config directory
* **logging.conf**: This is the configuration file for the logger. You do not need to update it.
* **paths-sample.json**: This holds the path to the directory where the project configuration files are stored and also the url to your portal. You will need to make a copy of it and name it **paths.json**

### logs directory
This is where the logs are written. The current log file is named `excalibur.log`. Logs are set to rotate when a log file reaches 500k and 2 backups are kept.

### projects directory
This is where the JSON files defining a project are stored. Samples are provided. You will need to make new JSON files and follow the samples to define your own projects

### scripts directory
Contains the two Python scripts that write the project to the portal.


## Creating a project

### Set up portal url
* Make a copy of `config/paths-sample.json` and name it **paths.json**.
* Update the `SHARING_URL` property to point to your portal. Make sure the url ends in `sharing/rest`.

### Make project definition
* Copy one of the JSON files in the `projects` directory and name it anything.
* Update the JSON to describe your project. See the [Project definition schema](#project-definition-schema) section for details about the JSON schema.

### Run the script to create a project
* Open a terminal and go to the directory where you cloned the repository or extracted the zip file contents, and then go to the scripts directory.
* From the scripts directory, run `python runCreateProject.py -h`. This shows the arguments. They are
  * The name of the project JSON file. **This must be the first argument**
  * Optional arguments:
    * **-s** or **--sharingurl**: The url to the portal's REST endpoint. If the argument is not specified, the url in the `SHARING_URL` property of `config/paths.json` is used.
    * **-u** or **--user**: Your portal username. If the argument is not specified you get prompted for it.
    * **-p** or **--password**: Your portal user's password. If the argument is not specified you get prompted for it.
    * **-o** or **--orgshare**: `True`/`False` flag for sharing the project item with the organization. Default is `False` (do not share it).
* If the script runs successfully, you will see a console log in the terminal that has the item id of the Excalibur Imagery Project's portal item.

**NOTE: In the scripts/createProject.py script there is a constant named 'VERIFY_SSL'. This is used to turn on/off SSL verification for http requests made by the 'requests' library. If running the script in a development environment, it might be necessary to set the flag to `False`**

## Project definition schema


