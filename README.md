# excalibur-scripts

Here are Python scripts and sample configuration files that can be used to automate the creation of Excalibur Imagery Projects.

For more information about Excalibur and Imagery Projects see the [Resources section](#resources).

## Included

* Sample JSON files that define an Imagery Project
* Sample JSON files that define overall configuration definitions for running the scripts
* Python scripts that create an Imagery Project in a portal

## Instructions

1. Fork and then clone this repository to your machine. Or download it as a zip file and extract the contents to your machine.
2. Make sure you have all the [requirements](#requirements).
3. Copy and edit the configuration files.
4. Run the script to create the project.

Detailed instructions are in the [Creating a project](#creating-a-project) section.

## Requirements

### Python 3

The scripts require Python 3 to be installed on your machine. The scripts were developed using Python version 3.8.6. Python 3 is already installed on your machine if you are running ArcGIS Pro. To see if Python is installed, open a terminal and run the command `python`. To see if Python is installed, open a terminal and run the command `python`. If installed, you will see the version of Python displayed and be at a command prompt for entering Python commands.

If Python is not installed on your machine, you can download the version for your OS from the [Python download site](https://www.python.org/downloads/). It is recommended to add the path to the Python executable to the `Paths` on your machine. Once installed, open a terminal and run the command `python` and make sure it runs without errors.

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

### Imagery Project

The properties for an imagery project. The `focusImageLayer` and `observationLayers` property are objects and their schema is described below.

| Name   | Description  | Required  | Default |
| ------ | -----------  | -------   | ------  |
| title  | The main display title for the project | Yes | |
| summary | A short summary of the project | No | There is no default so it is suggested to supply a summary |
| description | A more detailed description of the project | No | No default |
| instructions | Instructions for the person who is going to be working with the project | Yes | |
| webmapId | The item id of a webmap in the portal | No | If the webmapId is not specified, the user's default basemap is used |
| focusImageLayer | The descriptor for an imagery layer. See below for the schema | Yes | No default |
| observationLayers | Array of descriptors for Feature Layers used to collect observations | No | No default |

### Focus Image Layer

The properties for the `focusImageLayer` object.

| Name   | Description  | Required  | Default |
| ------ | -----------  | -------   | ------  |
| serviceType | The type of service used for the layer. The options are `arcgis` for an ArcGIS Image Service or `wms` for an OGC WMS Service | Yes | |
| serviceUrl | Url to the service | Yes | |
| rasterIds | An array of numbers. These are the ids of images in an ArcGIS Image Service. If specified, the layer will be configured to show only the specified images. Only valid when serviceType is `arcgis` | No | [] |
| layerNames | An array of strings. These are the sublayer names in a WMS Service. If specified, the layer will be configured to show only the specified sublayers. Only valid when serviceType is `wms` | No | [] |

### Observation Layer

The properties for the objects in the `observationLayers` array.

| Name   | Description  | Required  | Default |
| ------ | -----------  | -------   | ------  |
| type   | The type of layer. For now the only option is `Feature Layer` | Yes | |
| itemId | The id of a Feature Layer item in the same portal where the project is stored. Either this or the `url` property must be supplied | No | |
| url    | The url to an ArcGIS Feature Service layer. Either this or the `itemId` property must be supplied | No | |

## Sample Project Configurations

### Project with just a focus image layer

#### ArcGIS Image Service and all images are displayed

```
{
  "title": "A simple imagery project",
  "summary": "A simple project with just a focus image layer",
  "description": "",
  "instructions": "Look for damage",
  "focusImageLayer": {
    "serviceType": "arcgis",
    "serviceUrl": "https://server/service-name/ImageServer",
    "rasterIds": [],
    "layerNames": []
  }
}
```

#### ArcGIS Image Service and a subset of images are displayed

```
{
  "title": "A simple imagery project",
  "summary": "A simple project with just a focus image layer",
  "description": "",
  "instructions": "Look for damage",
  "focusImageLayer": {
    "serviceType": "arcgis",
    "serviceUrl": "https://server/service-name/ImageServer",
    "rasterIds": [1, 2, 3],
    "layerNames": []
  }
}
```

#### WMS Service all layers are displayed

```
{
  "title": "A simple imagery project",
  "summary": "A simple project with a WMS layer",
  "description": "",
  "instructions": "Look for damage",
  "focusImageLayer": {
    "serviceType": "wms",
    "serviceUrl": "https://server/service-name",
    "rasterIds": [],
    "layerNames": []
  }
}
```

#### WMS Service and a subset of layers are displayed

```
{
  "title": "A simple imagery project",
  "summary": "A simple project with a WMS layer",
  "description": "",
  "instructions": "Look for damage",
  "focusImageLayer": {
    "serviceType": "wms",
    "serviceUrl": "https://server/service-name",
    "rasterIds": []
    "layerNames": ["damage0102", "damage0104"]
  }
}
```

### Project with observation layer(s)

#### Single observation layer

```
{
  "title": "Imagery project with observations",
  "summary": "A project with an observation layer",
  "description": "",
  "instructions": "Add a point on top of anything of interest and enter comments",
  "focusImageLayer": {
    "serviceType": "arcgis",
    "serviceUrl": "https://server/service-name/ImageServer",
    "rasterIds": [1, 2, 3],
    "layerNames": []
  },
  "observationLayers": [
    {
      "type": "Feature Layer",
      "itemId": "123456789abcdefg"
    }
}
```

#### Multiple observation layers (one by url, one by item id)

This also shows the `webmapId` property

```
{
  "title": "Imagery project with observations",
  "summary": "A project with an observation layer",
  "description": "",
  "instructions": "Add a point on top of anything of interest and enter comments",
  "focusImageLayer": {
    "serviceType": "arcgis",
    "serviceUrl": "https://server/service-name/ImageServer",
    "rasterIds": [1, 2, 3],
    "layerNames": []
  },
  "observationLayers": [
    {
      "type": "Feature Layer",
      "itemId": "123456789abcdefg"
    },
    {
      "type": "Feature Layer",
      "url": "url to Feature Service"
    }
  ],
  "webmapId": "12345678"
}
```

## Resources

* Getting started with [Excalibur](https://enterprise.arcgis.com/en/excalibur/latest/get-started/what-is-arcgis-excalibur.htm)
* Overview of [Excalibur Imagery Projects](https://enterprise.arcgis.com/en/excalibur/latest/get-started/what-is-an-imagery-project-.htm)

## Issues

Find a bug or want to request a new feature?  Please let us know by submitting an issue.

## Contributing

Esri welcomes contributions from anyone and everyone. Please see our [guidelines for contributing](https://github.com/esri/contributing).

## Licensing
Copyright 2020 Esri

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

A copy of the license is available in the repository's [License.txt]( https://github.com/Esri/excalibur-scripts/blob/master/License.txt) file.
