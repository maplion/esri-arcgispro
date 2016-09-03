#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import urllib.request
import arcpy


class Toolbox(object):
    def __init__(self):
        self.label = u'General ArcGIS Pro Tools From MapLion'
        self.alias = ''
        self.tools = [GetElevationsFromPoints]


# Tool implementation code
class GetElevationsFromPoints(object):
    """Utilizes Google API to acquire Elevations from a point feature layer's latitudes and longitudes"""

    def __init__(self):
        self.label = u"Get Elevations from Points"
        self.description = u"Utilizes Google API to acquire Elevations from a point " \
                           u"feature layer's latitudes and longitudes"
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Input: Point Shapefile Feature Layer
        param_1 = arcpy.Parameter()
        param_1.name = u'Point_Features'
        param_1.displayName = u'Point Features'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'Feature Layer'
        param_1.value = u''
        param_1.filter.list = []

        # Output: Projected Shapefile Name
        param_2 = arcpy.Parameter()
        param_2.name = u'Projected_File_Name'
        param_2.displayName = u'Projected File Name'
        param_2.parameterType = 'Required'
        param_2.direction = 'Input'
        param_2.datatype = u'String'

        # Output: Projected Shapefile Location
        param_3 = arcpy.Parameter()
        param_3.name = u'Projected_File_Location'
        param_3.displayName = u'Projected File Location'
        param_3.parameterType = 'Required'
        param_3.direction = 'Input'
        param_3.datatype = u'Folder'

        return [param_1, param_2, param_3]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
            return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
            return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        """
        Created on August 30th, 2016
        Note: Because this uses Google API, it is limited to 2500 service calls a day.
		That is about 125,000 points to elevation per day at 50 points per service call.
		Calls are limited in length by the url character limit.

        @author: Ryan Dammrose aka MapLion
        """
        try:
			# Comment these parameters out if running standalone
            input_feature = parameters[0].valueAsText
            output_feature_name = parameters[1].valueAsText
            output_feature_location = parameters[2].valueAsText

            arcpy.env.overwriteOutput = "True"

            # Test Variables -- uncomment if running standalone
            # input_feature = r"C:\Users\dammrosr\Desktop\castford\castford.shp"
            # output_feature_name = "test"
            # output_feature_location = r"C:\TEMP"

            output_feature = os.path.join(output_feature_location, output_feature_name + ".shp")
            output_spatial_reference = arcpy.SpatialReference("WGS 1984")

            # Project into WGS 1984
            messages.AddMessage("Projecting to WGS 1984. Output File: " + output_feature)
            arcpy.Project_management(input_feature, output_feature, output_spatial_reference)

            # Add XY Coordinates to Projected Features
            messages.AddMessage("Adding XY Coordinates to Projected Features.")
            arcpy.AddXY_management(output_feature)

            # Add Elevation Column
            messages.AddMessage("Adding Elevation Column.")
            arcpy.AddField_management(output_feature, "Elevation", "DOUBLE")
            arcpy.AddField_management(output_feature, "Resolution", "DOUBLE")

            # Build URLs
            fields = ["POINT_X", "POINT_Y"]
            with arcpy.da.SearchCursor(output_feature, fields) as cursor:
                count = 0
                urls = []
                url = ""
                for row in cursor:
                    if count == 0:
                        url = "http://maps.googleapis.com/maps/api/elevation/json?locations=" + str(row[1]) + "," \
                          + str(row[0])
                    elif count == 50:  # This is designed to prevent the url from exceeding 2083 characters
                        url = url + "|" + str(row[1]) + "," + str(row[0]) + "&sensor=true_or_false"
                        urls.append(url)
                        url = ""
                        count = -1
                    else:
                        url = url + "|" + str(row[1]) + "," + str(row[0])
                    count += 1
            urls.append(url)
            datas = []
            for url in urls:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req) as response:
                    google_response = response.read()
                    data = json.loads(google_response.decode('utf-8'))
                    messages.AddMessage(data)
                    datas.append(data)

            fields = ["POINT_X", "POINT_Y", "Elevation", "Resolution"]
            with arcpy.da.UpdateCursor(output_feature, fields) as cursor:
                for results in datas:
                    count = 0
                    result_length = len(data["results"])
                    for row in cursor:
                        elevation_meters = float(data["results"][count]["elevation"])
                        elevation_feet = 3.28084 * elevation_meters  # Convert Meters to Feet
                        resolution_meters = float(data["results"][count]["resolution"])
                        resolution_feet = 3.28084 * resolution_meters  # Convert Meters to Feet
                        row[2] = elevation_feet
                        row[3] = resolution_feet
                        messages.AddMessage(row)
                        cursor.updateRow(row)
                        count += 1
                        if count == result_length:
                            break

            # Add layer to map -- comment out if running standalone
            messages.AddMessage("Adding Projected Layer to Map.")
            layer = arcpy.MakeFeatureLayer_management(output_feature, output_feature_name +
                                                      "_elevation")[0]
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            m = aprx.listMaps("Map")[0]
            m.addLayer(layer, "TOP")

        except Exception as err:
            messages.AddMessage(err)


def main():
    """This is for testing and debugging in IDE"""
    elevation_from_points = GetElevationsFromPoints()
    elevation_from_points.execute(elevation_from_points.getParameterInfo(), arcpy)

if __name__ == "__main__":
    sys.exit(main())
