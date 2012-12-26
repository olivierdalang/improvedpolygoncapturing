"""
/***************************************************************************
ImprovedPolygonCapturing
A QGIS plugin
Improved polygon capturing - add linesegments with preset length.
                             -------------------
begin                : 2010-06-28 
copyright            : (C) 2010 by Adrian Weber
email                : adrian.weber@cde.unibe.ch 
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""
def name(): 
  return "Improved Polygon Capturing" 
def description():
  return "Add linesegments with preset length and angle while digitizing polygons or lines"
def version(): 
  return "Version 1.1"
def qgisMinimumVersion():
  return "1.0"
def classFactory(iface): 
  # load AddVertexOnRadius class from file AddVertexOnRadius
  from ImprovedPolygonCapturing import ImprovedPolygonCapturing 
  return ImprovedPolygonCapturing(iface)


