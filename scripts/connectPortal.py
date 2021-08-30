# Copyright 2021 Esri
#
# Licensed under the Apache License Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
A module that connects to a portal using different authentication methods. Built in users, IWA and PKI are supported
It uses the ArcGIS API for Python
"""

from pathlib import Path

from arcgis.gis import GIS

class ConnectPortal:

  def __init__(self, portalUrl) -> None:
    """
    Constructor for the ConnectPortal class

    Parameters:
        portalUrl (string): The url to the portal's sharing REST endpoint
    """
    if not portalUrl:
      raise Exception("Missing argument. Supply portalUrl")

    self.portalUrl = portalUrl


  def connectUsernamePassword(self, username, password, verifySSL=True) -> GIS:
    """
    Method for connecting to a portal that uses built-in users for authentication

    Parameters:
      username (string): log in name for the user. If not supplied, a prompt will be used to capture it.
      password (string): Password for the user. If not supplied, a prompt will be used to capture it.
      verifySSL (boolean): Flag for requiring a valid SSL certificate on the portal

    Returns:
      GIS: An argis.gis.GIS object
    """

    if not username or not password:
        raise Exception("username and password are required")

    try:
      gis = GIS(self.portalUrl, username, password, verify_cert=verifySSL)
      return gis
    except Exception as e:
      raise e


  def connectIWA(self, username=None, password=None, verifySSL=True) -> GIS:
    """
    Method for connecting to a portal that uses Integrated Windows Authentication

    Parameters:
      username (string): log in name for the user. If not supplied, it's assumed that user is can access the portal without them.
      password (string): Password for the user. If not supplied,  it's assumed that user is can access the portal without them.
      verifySSL (boolean): Flag for requiring a valid SSL certificate on the portal

    Returns:
      GIS: An argis.gis.GIS object
    """

    try:
      gis = GIS(self.portalUrl, username, password, verify_cert=verifySSL)
      return gis
    except Exception as e:
      raise e


  def connectPKI(self, certFile, keyFile=None, password=None, verifySSL=True) -> GIS:
    """
    Method for connecting to a portal that uses PKI for authentication

    Parameters:
      certfile (string): Path to a certificate file
      keyFile (string): Path to a key file.
      password (string): Password for the certfile
      verifySSL (boolean): Flag for requiring a valid SSL certificate on the portal

    Returns:
      GIS: An argis.gis.GIS object
    """

    if not certFile:
      raise Exception("certFile path is required for PKI")

    try:
      theCertPath = Path(certFile)
      if not theCertPath.is_file():
        raise Exception("cannot find certFile at {}. Make sure file exists".format(theCertPath.resolve()))

      if keyFile:
        theKeyPath = Path(keyFile)
        if not theKeyPath.is_file():
          raise Exception("cannot find keyFile at {}. Make sure file exists".format(theKeyPath.resolve()))

      gis = GIS(self.portalUrl, password=password, cert_file=certFile, key_file=keyFile, verify_cert=verifySSL)
      return gis
    except Exception as e:
      raise e
