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

The scripts require Python 3 to be installed on your machine. The scripts were developed using Python version 3.8.6. Python 3 is already installed on your machine if you are running ArcGIS Pro. To see if Python is installed, open a terminal and run the command `python`. If installed, you will see the version of Python displayed and be at a command prompt for entering Python commands.

If Python is not installed on your machine, you can download the version for your OS from the [Python download site](https://www.python.org/downloads/). It is recommended to add the path to the Python executable to the `Paths` on your machine. Once installed, open a terminal and run the command `python` and make sure it runs without errors.

### ArcGIS API for Python

Connections to the portal and content creation are handled via the ArcGIS API for Python. You can get information about it at the [API site](https://developers.arcgis.com/python/). Detailed instructions for installing the API are [here](https://developers.arcgis.com/python/guide/install-and-set-up/).
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
Contains the two Python scripts that write the project to the portal and the script that connects to the portal using the supplied credentials.


## Creating a project

### Set up portal url
* Make a copy of `config/paths-sample.json` and name it **paths.json**.
* Update the `SHARING_URL` property to point to your portal. Make sure the url ends in `sharing/rest`.

**NOTE: In `config/paths-sample.json` there is a property named 'VERIFY_SSL'. This is used to turn on/off SSL verification for http requests made by the 'requests' library. If running the script in a development environment, it might be necessary to set the flag to `false`**

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

## Project definition schema

### Imagery Project

The properties for an imagery project. The `focusImageLayer` and `observationLayers` property are objects and their schema is described below.

| Name   | Description  | Type  | Required  | Default |
| ------ | -----------  | ----- | -------   | ------  |
| title  | The main display title for the project | string | Yes | |
| summary | A short summary of the project | string | No | There is no default so it is suggested to supply a summary |
| description | A more detailed description of the project | string | No | No default |
| instructions | Instructions for the person who is going to be working with the project | string | Yes | |
| webmapId | The item id of a webmap in the portal | string | No | If the webmapId is not specified, the user's default basemap is used |
| focusImageLayer | The descriptor for an imagery layer. See below for the schema | *Focus Image Layer* | Yes | |
| observationLayers | Array of descriptors for Feature Layers used to collect observations. | *Observation Layer[]* See below for the schema | No | |

### Focus Image Layer

Supported service types at versions of Excalibur
* ArcGIS Image Service - as of `v1.0`
* WMS Service - as of `v2.1`
* WMTS Service - as of `v2.1`

The properties for the `focusImageLayer` object.

| Name   | Description  | Type  | Required  | Default |
| ------ | -----------  | ----- | --------  | ------- |
| serviceType | The type of service used for the layer. The options are `arcgis` for an ArcGIS Image Service, `wms` for an OGC WMS Service, `wmts` for an OGC WMTS Service | Yes | |
| serviceUrl | Url to the service | string | Yes | |
| rasterIds | These are the ids of images in an ArcGIS Image Service. If specified, the layer will be configured to show only the specified images. Only valid when serviceType is `arcgis` | number[] | No | [] |
| layerNames | An array of strings. These are the sublayer names in a WMS or WMTS Service. If specified, the layer will be configured to show only the specified sublayers. Only valid when serviceType is `wms` or `wmts`. *WMTS* layers only support displaying ONE sublayer. | string[] | No | [] |

### Observation Layer

* *Observation Layer* supported since `v1.0`
* *enrichmentDefinition* supported since `v2.3`

The properties for the objects in the `observationLayers` array.

| Name   | Description  | Type  | Required  | Default |
| ------ | -----------  | ----- | --------  | ------- |
| itemId | The id of a Feature Layer item in the same portal where the project is stored. | string | Yes | |
| layerId | The id of the layer in a multiple layer feature service | number | No | 0 |
| url    | The url to an ArcGIS Feature Service layer. | string | No | |
| enrichmentDefinition | An object describing how enrichment fields are populated. The geometry type of the Observation Layer must be *Point* | *Enrichment Definition* See below for schema | No |  |

### Enrichment Definition

| Name   | Description  | Type  | Required  | Default |
| ------ | -----------  | ----- | --------  | ------- |
| description | A short description of the enrichment definition | string | Yes | |
| layers | The Enrichment Layers that are part of this definition | *Enrichment Layer Definition[]* See below for schema | Yes | |

### Enrichment Layer Definition

| Name   | Description  | Type  | Required  | Default |
| ------ | -----------  | ----- | --------  | ------- |
| fields | Information on source and destination fields | *Enrichment Field Definition[]* See below for schema | Yes | |
| sourceItemId  | The itemId of a layer in the portal hosting the application. The geometry type of the service layer must be *Polygon* and the layer must be in the WebMap of the project. This or `sourceUrl` must be set. | string | No | |
| sourceUrl  | The url to the service. The geometry type of the service layer must be *Polygon* and the layer must be in the WebMap of the project. This or `sourceItemId` must be set.  | string | No | |
| layerId | The id of the layer in a multiple layer feature service | number | No | 0 |

### Enrichment Field Definition

| Name   | Description  | Type  | Required  | Default |
| ------ | -----------  | ----- | --------  | ------- |
| source | Name of the field in the enrichment source service. This is the name of the field, NOT THE ALIAS | string | Yes | |
| destination | Name of the field in the observation layer. This is the name of the field, NOT THE ALIAS | string | Yes | |

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

#### WMTS Service

NOTE: WMTS service layers are cached and **ONLY ONE** can be displayed as the focus image layer in a project. So the `layerNames` property can only have one layer name.
```
{
  "title": "A simple imagery project",
  "summary": "A simple project with a WMTS layer",
  "description": "",
  "instructions": "Look for weather",
  "focusImageLayer": {
    "serviceType": "wmts",
    "serviceUrl": "https://server/service-name",
    "rasterIds": []
    "layerNames": ["radar-base-reflectivity"]
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
      "itemId": "123456789abcdefg"
    }
  ]
}
```

#### Multiple observation layers (one with layerId set)

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
      "itemId": "123456789abcdefg"
    },
    {
      "itemId": "hijklmnop9876543",
      layerId: 2
    }
  ],
  "webmapId": "12345678"
}
```

#### Observation layer with enrichment definition

```
{
  "title": "Imagery project with observations getting data from another layer",
  "summary": "A project with an observation layer that gets its 'parcelid' field calculated from the parcel boundary polygon layer's 'id' field",
  "description": "",
  "instructions": "Add a point on top of anything of interest and enter comments",
  "webmapId": "12345678",
  "focusImageLayer": {
    "serviceType": "arcgis",
    "serviceUrl": "https://server/service-name/ImageServer",
    "rasterIds": [
      1,
      2,
      3
    ],
    "layerNames": []
  },
  "observationLayers": [
    {
      "itemId": "ead6deb3d93848c4a7fd58025cc2cdaa",
      "enrichmentDefinition": {
        "description": "Building Parcel Info",
        "layers": [
          {
            "sourceUrl": "https://path/to/parcel/boundaries/FeatureServer",
            "fields": [
              {
                "source": "id",
                "destination": "parcelid"
              }
            ]
          }
        ]
      }
    }
  ]
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
