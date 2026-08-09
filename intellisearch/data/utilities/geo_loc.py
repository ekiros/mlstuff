"""
 Copyright (c) 2024, Microproduct, inc.
 All rights reserved.
 SPDX-License-Identifier: BSD-3-Clause
 For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

 Description: Geolocation module used to map a given location to latitude, longitude; inversely the module can
 also be used to find name of a location given latitude, longitude
"""

from geopy.geocoders import Nominatim

'''
Do location mapping given lat, log coordinates
Do reverse - given location, find its closet lat, log, alt
'''

def main():
    coord_given_location('Santa Clara, California USA')
    #location_given_coord(37.3541,-121.9552)
    location_given_coord(9.0192,38.7525)

def coord_given_location(location):
 
    # calling the Nominatim tool
    loc = Nominatim(user_agent="microproduct.app")
    
    # entering the location name
    getLoc = loc.geocode("Santa Clara, California USA")
    
    # printing address
    print(getLoc.address)
    
    # printing latitude and longitude
    print("Latitude = ", getLoc.latitude, "\n")
    print("Longitude = ", getLoc.longitude)


def location_given_coord(latitude, longitude):
    # calling the nominatim tool
    geoLoc = Nominatim(user_agent="microproduct.app")
 
    # passing the coordinates
    locname = geoLoc.reverse(f"{latitude},{longitude}", addressdetails=True)
 
    # printing the address/location name
    print(f"The loaction: {locname.address}")


## RUN ##
if __name__ == '__main__':
    main()
