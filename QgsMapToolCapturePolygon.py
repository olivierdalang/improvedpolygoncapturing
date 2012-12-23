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
"""
import math

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

class QgsMapToolCapturePolygon(QgsMapTool):
    """
    QgsMapTool subclass to capture polygon with preset edge length and add
    it as new features to the current layer.
    """
    def __init__(self, iface, spinBox, isPolygon):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.spinBox = spinBox
        # If true the new geometry is a polygon else if false it's a line
        self.isPolygon = isPolygon
        # Create an empty rubber band
        self.rubberBand = QgsRubberBand(self.canvas, self.isPolygon)
        # Create an empty list for vertex marker
        self.vertexMarkers = []
        # Create an empty list to store the new vertices
        self.captureList = []
        # Get the current layer
        self.layer = self.canvas.currentLayer()
        # Create the mouse cursor
        self.cursor = QCursor(QPixmap(["16 16 3 1",
                              "      c None",
                              ".     c #000000",
                              "+     c #ffffff",
                              "                ",
                              "       +.+      ",
                              "      ++.++     ",
                              "     +.....+    ",
                              "    +.  .  .+   ",
                              "   +.   .   .+  ",
                              "  +.    .    .+ ",
                              " ++.    .    .++",
                              " ... ...+... ...",
                              " ++.    .    .++",
                              "  +.    .    .+ ",
                              "   +.   .   .+  ",
                              "   ++.  .  .+   ",
                              "    ++.....+    ",
                              "      ++.++     ",
                              "       +.+      "]))

        # Get the project property and check if new added geometries has to avoid intersections
        self.isAvoidingIntersection = False
        # Get the list with layer entries
        avoidIntersectionList = QgsProject.instance().readListEntry("Digitizing", "/AvoidIntersectionsList")
        # Loop over the list
        if self.layer is not None:
            for i in range(len(avoidIntersectionList[0])):
                # Compare the list entries with the current layer id
                if str(avoidIntersectionList[0][i]) == self.layer.getLayerID():
                    self.isAvoidingIntersection = True

    def canvasPressEvent(self, event):
        """
        Handle mouse clicks. With normal clicks new vertices are added
        to the current polygon, a right click set the last point and
        finish the new geometry.
        """
        # Captures the clicked coordinate and transform
        mapCoordinates = self.toMapCoordinates(event.pos())

        # Check if it's a normal or a right click
        if(event.button() == Qt.RightButton):
            self.finishFeature(mapCoordinates)
        else:
            self.addVertex(mapCoordinates)
  
    def canvasMoveEvent(self, event):
        """
        Listen to the mouse movement to provide the interactive polygon
        preview.
        """
        self.moveVertex(self.toMapCoordinates(event.pos()))
        pass

    def canvasReleaseEvent(self, event):
        pass
            
    def activate(self):
        QgsMapTool.activate(self)
        # Change the mouse cursor to the capture cursor symbol
        self.canvas.setCursor(self.cursor)
  
    def deactivate(self):
        """
        Deactivate this qgsmaptool and send a signal. This signal
        is used by the ImprovedPolygonCapturing class to disconnect
        all signal and disable the button in the toolbar
        """
        self.emit(SIGNAL("deactivated()"))
        pass
  
    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        """
        Yup, it is an edit tool
        """
        return True

    def addVertex(self, pt):
        """
        Add a new vertex to the current polygon.
        @param {QgsPoint} pt Position of the mouse click in map coordinates
        """
    
        # Get the distance from the UI
        distance = self.spinBox.value()

        # Coordinates of mouse click
        newPt = None

        # If the capture list contains already vertices, then calculate the new position
        # based on the distance (and considering snapping)
        if len(self.captureList) > 0:
            newPt = self.calculatePointPos(pt, distance)

        # If this is the first point add a new point to the
        # capture list at the current mouse position considering
        # the default snapping behaviour.
        else:
            snappedPt = self.snapToBackgroundLayers(pt)
            newPt = QgsPoint(snappedPt.x(), snappedPt.y())

        # Project the new point to the layer projection and add it to the capture list
        self.captureList.append(self.toLayerCoordinates(self.layer, newPt))

        # Add the new point also to the rubberband
        self.rubberBand.addPoint(newPt)
        # And add also a small marker to highlight the vertices
        m = QgsVertexMarker(self.canvas)
        m.setCenter(newPt)
        self.vertexMarkers.append(m)

        # Give the focus back to the spin box to allow a convenient distance
        # re-entry
        self.spinBox.setFocus()
        self.spinBox.selectAll()

    def moveVertex(self, pt):
        """
        Moves the last vertex in the rubberband according to the
        mouse pointer. This method is used to provide the interactive
        polygon preview.
        @param {QgsPoint} pt Mouse pointer position in map coordinates
        """
        # Get the distance from the UI
        distance = self.spinBox.value()

        # Coordinates of mouse move
        cursorPt = QgsPoint(pt.x(), pt.y())
        newPt = None

        nbrVertices = self.rubberBand.numberOfVertices()
        if nbrVertices > 1:
            newPt = self.calculatePointPos(cursorPt, distance)
            # Move the last point to create an interactive movement
            self.rubberBand.movePoint(newPt)

    def finishFeature(self, pt):
        """
        Creates a new feature from the coordinates of the rubberband and adds
        it the current layer
        @param {QgsPoint} pt The last point to add to the polygon in map coordinates
        """

        self.addVertex(pt)
 
        # Handle polygons
        if self.isPolygon:
            # A valid polygons requires at least three points. Throw
            # an error message if this is not the case.
            if not len(self.captureList) >= 3:
                QMessageBox.critical(self.canvas,
                                     QCoreApplication.translate("ImprovedPolygonCapturing", "Not enough vertices"),
                                     QCoreApplication.translate("ImprovedPolygonCapturing", "Cannot close a polygon feature until it has at least three vertices."))
                # Clear the canvas
                self.clearMapCanvas()
                return

            # Create a geometry from the point list considering the
            # layer geometry type.
            if self.layer.wkbType() == QGis.WKBMultiPolygon:
                geometry = QgsGeometry().fromMultiPolygon([[self.captureList]])
            elif self.layer.wkbType() == QGis.WKBPolygon:
                geometry = QgsGeometry().fromPolygon([self.captureList])

            # Handle avoiding intersections
            if self.isAvoidingIntersection:
                self.layer.removePolygonIntersections(geometry)

                # We need to check if the removePolygonIntersections method has changed the new
                # geometry to a multipolygon. If yes, we cannot add the new geometry to the
                # PostGIS layer, since this will break the geometry constraints in PostGIS
                if self.layer.wkbType() == QGis.WKBPolygon and geometry.isMultipart():
                    # Throw the same error like qgsmaptooladdfeature.cpp
                    QMessageBox.critical(self.canvas,
                                         QCoreApplication.translate("ImprovedPolygonCapturing", "Error"),
                                         QCoreApplication.translate("ImprovedPolygonCapturing", "The feature could not be added because removing the polygon intersections would change the geometry type"))
                    self.clearMapCanvas()
                    # Cancel the operation
                    return

        # Handle linestrings
        elif not self.isPolygon:
            # Check if there are enough vertices to create a line string
            if not len(self.captureList) >= 2:
                QMessageBox.critical(self.canvas,
                                     QCoreApplication.translate("ImprovedPolygonCapturing", "Not enough vertices"),
                                     QCoreApplication.translate("ImprovedPolygonCapturing", "Cannot close a line feature until it has at least two vertices."))
                self.clearMapCanvas()
                return

            # Create a geometry from the point list considering the
            # layer geometry type.
            if self.layer.wkbType() == QGis.WKBMultiLineString:
                geometry = QgsGeometry().fromMultiPolyline([self.captureList])
            elif self.layer.wkbType() == QGis.WKBLineString:
                geometry = QgsGeometry().fromPolyline(self.captureList)

        # Cancel the operation and clear the map canvas if the new geometry is not valid
        else:
            self.clearMapCanvas()
            return

        # print "New geometry is " + str(geometry.exportToWkt())

        # Add the new geometry to the layers topological point to ensure topological editing
        # see also the announcing for version 1.0 http://blog.qgis.org/node/123
        self.layer.addTopologicalPoints(geometry)

        # Create a new feature and set the geometry to it
        feature = QgsFeature()
        feature.setGeometry(geometry)

        # Add the fields from the current layer to the feature
        for index in self.layer.dataProvider().fields():
            feature.addAttribute(index, self.layer.dataProvider().fields()[index])

        # Open the feature form to edit the attributes. If the user cancels the
        # feature form, openFeatureForm returns false and the feature is not added
        # to the layer.
        # Since I'm not sure when QgisInterface.openFeatureForm has been added
        # to the QGIS API proper exception handling is needed.
        saveFeature = True
        try:
            saveFeature = self.iface.openFeatureForm(self.layer, feature, True)
        except AttributeError:
            pass

        # Add the new feature to the layer
        if saveFeature:
            self.layer.addFeature(feature)
    
        # Clear and refresh the canvas in any case
        self.clearMapCanvas()

    def calculatePointPos(self, pt, distance):
        """
        Calculate a new point based on the distance from the spin box and the snapping
        properties. Snapping has priority to the distance! That means first the new
        position is calculated, then the project snapping properties are considered.
        If the user enters zero in the spin box, then the new point is at the mouse
        pointer, i.e. this method is just considering the snapping properties.
        The distance calculation is done with plain trigonometry! Thus it is not recommended
        to use it with unprojected systems like EPSG:4326!
        @param {QgsPoint} pt Mouse pointer in map coordinates
        @param {double} distance Preset length of the new edge in map units
        """
        # If the distance is zero, do not calculate a point position based on the distance
        # but attach the new point to the mouse click resp. pointer
        if distance > 0:
            # Take the second last point, since the last one is just for the interactive movement
            lastPt = self.rubberBand.getPoint(0, self.rubberBand.numberOfVertices()-2)
            # Attention! The angle and new point are calculated in plain trigonmetry!
            # Depending on the projection this is not very accurate!
            diffX = pt.x() - lastPt.x()
            diffY = pt.y() - lastPt.y()
            # Calculate angle
            beta = math.atan2(diffY, diffX)
            # Calculate new point
            a = math.cos(beta) * distance
            b = math.sin(beta) * distance

            calcPt = QgsPoint(lastPt.x() + a, lastPt.y() + b)

        # Take the input point
        else:
            calcPt = pt

        # Snap the new calculated point to the background
        return self.snapToBackgroundLayers(calcPt);

    def snapToBackgroundLayers(self, qgspoint):
        """
        Provides the snapping to the background layers considering the
        current project snapping properties
        @param {QgsPoint} qgspoint The point to snap in map coordinates
        @returns {QgsPoint} Snapped point in map coordinates
        """
        # Transform it to pixel coordinates
        pixels = self.toCanvasCoordinates(qgspoint)
        # Snap to the background layers according to the project properties
        snapper = QgsMapCanvasSnapper(self.canvas)
        snapped = snapper.snapToBackgroundLayers(QPoint(pixels.x(), pixels.y()))
        # If the point snaps, return this point
        if len(snapped[1]) > 0:
            # It seems to be necessary to create a new QgsPoint from the snapping result
            return QgsPoint(snapped[1][0].snappedVertex.x(), snapped[1][0].snappedVertex.y())

        # If the point does not snap, return the input point
        return qgspoint

    def clearMapCanvas(self):
        """
        Clears the map canvas and in particular the rubberband.
        A warning is thrown when the markers are removed.
        """
        # Reset the capture list
        self.captureList = []

        # Reset the rubber band
        self.rubberBand.reset(self.isPolygon)

        # Delete also all vertex markers
        for marker in self.vertexMarkers:
            self.canvas.scene().removeItem(marker)
            del marker
  
        self.canvas.refresh()
