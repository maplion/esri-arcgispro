# Esri ArcGIS Pro Scripts and Tools

---

These are just tools that I have written that I was able to open-source.

## General ArcGIS Pro Tools

### Getting Elevations from Point Latitude and Longitude using Google API

This tool utilizes Google Map's Elevation API to acquire elevations along with the resolution from a point shapefile.  

It assumes a projected shapefile that is not WGS 1984.  This is also a Python Toolbox and assumes you're running it from within ArcGIS Pro.  You can run it standalone, but you will need to comment out the portion where it attempts to load the layer into the map.

Inputs: 
	1. Point Shapefile/Feature Layer (Projected)
	2. Projected Point Shapefile Output Name
	3. Projected Point Shapefile Output Folder

Outputs:
	1. Copy of input Shapefile with POINT_X, POINT_Y, Elevation, and Resolution populated columns.


