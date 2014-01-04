"""
/***************************************************************************
ImprovedPolygonCapturing
A QGIS plugin
Improved polygon capturing - add linesegments with preset length.
                             -------------------
begin                : 2010-06-28 
copyright            : (C) 2010 by Adrian Weber
email                : adrian.weber@cde.unibe.ch 
contributor          : Olivier Dalang ( olivier.dalang@gmail.com )
git repo             : https://github.com/olivierdalang/improvedpolygoncapturing2
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
    def __init__(self, iface, relBox, spinBoxDist, spinBoxAngle, lockBoxDist, lockBoxAngle, isPolygon):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.relBox = relBox
        self.spinBoxDist = spinBoxDist
        self.spinBoxAngle = spinBoxAngle
        self.lockBoxDist = lockBoxDist
        self.lockBoxAngle = lockBoxAngle
        self.isPolygon = isPolygon
        # Create an empty rubber band
        if self.isPolygon:
            self.rubberBand = QgsRubberBand(self.canvas, QGis.Polygon) # BMF for reference: Polygon > rubberband interior is filled in
        else:
            self.rubberBand = QgsRubberBand(self.canvas, QGis.Line) #BMF Line > interior not filled (what we want for EntryLines)
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

        # Get the settings for the digitizing rubberband
        settings = QSettings()
        red = settings.value("/qgis/digitizing/line_color_red", 255)
        green = settings.value("/qgis/digitizing/line_color_green", 0)
        blue = settings.value("/qgis/digitizing/line_color_blue", 0)
        alpha = settings.value("/qgis/digitizing/line_color_alpha", 150)
        rubberBandColor = QColor(red, green, blue, alpha)
        self.rubberBand.setColor(rubberBandColor)
        # Get also the line width from the settings
        lineWidth = settings.value("/qgis/digitizing/line_width", 1)
        self.rubberBand.setWidth(lineWidth)
        #self.rubberBand.show()
        
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
        # BMF added try block > getting error on QGIS close
        try:
            self.emit(SIGNAL("deactivated()"))
        except:
            pass
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
    
        # Get the values from the UI
        relBox = self.relBox.isChecked()
        distance = self.spinBoxDist.value()
        angle = self.spinBoxAngle.value()
        distanceLock = self.lockBoxDist.isChecked()
        angleLock = self.lockBoxAngle.isChecked()

        # Coordinates of mouse click
        newPt = None

        # If the capture list contains already vertices, then calculate the new position based on the distance (and considering snapping)
        if len(self.captureList) > 0:
            newPt = self.calculatePointPos(pt, relBox, distance, angle, distanceLock, angleLock)
        # If this is the first point add a new point to the capture list at the current mouse position considering the default snapping behaviour.
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
        self.spinBoxDist.setFocus()
        self.spinBoxDist.selectAll()

    def moveVertex(self, pt):
        """
        Moves the last vertex in the rubberband according to the
        mouse pointer. This method is used to provide the interactive
        polygon preview.
        @param {QgsPoint} pt Mouse pointer position in map coordinates
        """
        # Get the values from the UI
        relBox = self.relBox.isChecked()
        distance = self.spinBoxDist.value()
        angle = self.spinBoxAngle.value()
        distanceLock = self.lockBoxDist.isChecked()
        angleLock = self.lockBoxAngle.isChecked()

        # Coordinates of mouse move
        cursorPt = QgsPoint(pt.x(), pt.y())
        newPt = None

        

        nbrVertices = self.rubberBand.numberOfVertices()
        if nbrVertices > 1:
            newPt = self.calculatePointPos(cursorPt, relBox, distance, angle, distanceLock, angleLock)
            # Move the last point to create an interactive movement
            self.rubberBand.movePoint(newPt)

    def finishFeature(self, pt):
        """
        Creates a new feature from the coordinates of the rubberband and adds
        it the current layer
        @param {QgsPoint} pt The last point to add to the polygon in map coordinates
        """
 
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
        pr=self.layer.dataProvider()
        attrib_tmp=[]
		
        # Add the fields from the current layer to the feature
        for at in pr.fields():
            attrib_tmp.append(at)

        # Open the feature form to edit the attributes. If the user cancels the
        # feature form, openFeatureForm returns false and the feature is not added
        # to the layer.
        # Since I'm not sure when QgisInterface.openFeatureForm has been added
        # to the QGIS API proper exception handling is needed.
        feature.setAttributes(attrib_tmp)
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

    def calculatePointPos(self, pt, relBox, inputDistance, inputAngle, distanceLock, angleLock):
        """
        Calculate a new point based on the distance from the spin box and the snapping
        properties. Snapping has priority over actual mouse position but NOT over locked numerical values.
        The distance calculation is done with plain trigonometry! Thus it is not recommended
        to use it with unprojected systems like EPSG:4326!
        @param {QgsPoint} pt Mouse pointer in map coordinates
        @param {double} distance Preset length of the new edge in map units
        """

        # Actual input point
        pt = self.snapToBackgroundLayers(pt)    #Sthe actual input point is the snapped point
        # Last input point
        lastPt = self.rubberBand.getPoint(0, self.rubberBand.numberOfVertices()-2) # Take the second last point, since the last one is just for the interactive movement
        
        newAngle = 0 # This will store the computed angle
        newDist = 10 # This will store the computed distance

       
        if relBox:
            # If the angle is not absolute, we have to compute the angle of the last entered line segment
            if self.rubberBand.numberOfVertices() > 2:
                secondLastPt = self.rubberBand.getPoint(0, self.rubberBand.numberOfVertices()-3)
                lastAngle = math.atan2(lastPt.y() - secondLastPt.y(), lastPt.x() - secondLastPt.x())
            else:
                #If there is no last entered line segment, we start we a 0 angle
                lastAngle = 0

        
        if angleLock:
            # If the angle is locked
            if not relBox:
                newAngle = inputAngle/180.0*math.pi # We compute the new angle based on the input angle (ABSOLUTE)
            else:
                newAngle = lastAngle + inputAngle/180.0*math.pi # We compute the new angle based on the input angle (RELATIVE)
        else:
            # If the angle is not locked
            newAngle = math.atan2((pt.y()-lastPt.y()), pt.x()-lastPt.x()) # We simply set the new angle to the current angle
            if not relBox:
                self.spinBoxAngle.setValue(newAngle/math.pi*180.0) # Update the spinBox to reflect the current distance
            else:
                self.spinBoxAngle.setValue( (newAngle-lastAngle)/math.pi*180.0  ) # Update the spinBox to reflect the current distance


        if distanceLock:
            # If the distance is locked
            newDist = inputDistance # We simply set the new distance to the input distance
        else:
             # If the distance is not locked
            if angleLock:
                newDist = self.projectedDistance( lastPt, pt, newAngle ) # We simply set the new distance to the current distance
            else:
                newDist = math.sqrt( (pt.x()-lastPt.x())*(pt.x()-lastPt.x()) + (pt.y()-lastPt.y())*(pt.y()-lastPt.y()) ) # Or to its projection if the angle is locked
            
            self.spinBoxDist.setValue(newDist) # Update the spinBox to reflect the current distance


        if distanceLock or angleLock:
            # We only need to do some calulation if either the distance or the angle is locked
            a = math.cos(newAngle) * newDist
            b = math.sin(newAngle) * newDist
            return QgsPoint(lastPt.x() + a, lastPt.y() + b)
        else:
            return pt

    def projectedDistance(self, lastPt, mousePt, angle):


        ang = angle#/180.0*math.pi

        projVect = QVector2D(math.cos(ang), math.sin(ang))
        #projVect.normalize()
        mouseVect = QVector2D(mousePt.x()-lastPt.x(),mousePt.y()-lastPt.y())

        return QVector2D.dotProduct(mouseVect,projVect)


        #pa = lastPt
        #pb = QPoint( lastPt.x()+math.cos(ang), lastPt.y()+math.sin(ang))

        #m = (pb.y() - pa.y()) / (pb.x() - pa.x())
        #b = pa.y() - (m * pa.x())
    
        #x = (m * mousePt.y() + mousePt.x() - m * b) / (m * m + 1)
        #y = (m * m * mousePt.y() + m * mousePt.x() + b) / (m * m + 1)

        #return math.sqrt( (x-pa.x())*(x-pa.x()) + (y-pa.y())*(y-pa.y()) )



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

        # Create an empty rubber band
        if self.isPolygon:
            self.rubberBand.reset(QGis.Polygon)
        else:
            self.rubberBand.reset(QGis.Line)

        # Delete also all vertex markers
        for marker in self.vertexMarkers:
            self.canvas.scene().removeItem(marker)
            del marker
  
        self.canvas.refresh()
