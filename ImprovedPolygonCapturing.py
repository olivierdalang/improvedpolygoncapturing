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

# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from QgsMapToolCapturePolygon import QgsMapToolCapturePolygon
from qgis.core import *
from qgis.gui import *
import resources

class ImprovedPolygonCapturing: 
    def __init__(self, iface):

        # Initialise the translation environment
        pluginPath = QFileInfo(__file__).absolutePath()
        # Extract the locale
        localeName = QSettings().value("locale/userLocale").toString()

        if QFileInfo(pluginPath).exists():
            # Check first if the locale including the country exists
            localePath = pluginPath + "/i18n/improvedpolygoncapturing_" + localeName + ".qm"
            if not QFileInfo(localePath).exists():
                # Else try to take a translation with just the language
                localePath = pluginPath + "/i18n/improvedpolygoncapturing_" + localeName[0:2] + ".qm"

            # Check if locale path exists and install the new translator
            if QFileInfo(localePath).exists():
                self.translator = QTranslator()
                self.translator.load(localePath)

                if qVersion() > '4.3.3':
                    QCoreApplication.installTranslator(self.translator)

        # Save reference to the QGIS interface
        self.iface = iface
        # Reference to the QGIS map canvas
        self.canvas = iface.mapCanvas()
        self.tool = None
        self.isPolygon = True

    def initGui(self):
        """
        Creates the necessary actions
        """
        # Create an action to start capturing polygons and add it to the digitize toolbar
        self.capturePolygonAction = QAction(QIcon(":/plugins/improvedpolygoncapturing/mActionCapturePolygon.png"), QCoreApplication.translate("ImprovedPolygonCapturing", "Capture Polygon with preset Edge Lengths"), self.iface.mainWindow())
        self.capturePolygonAction.setCheckable(True)
        self.capturePolygonAction.setEnabled(False)
        self.iface.digitizeToolBar().addAction(self.capturePolygonAction)

        # Create a spin box to enter the distance and add it the to digitize toolbar
        self.absBox = QCheckBox(self.iface.mainWindow())
        self.spinBox = QDoubleSpinBox(self.iface.mainWindow())
        self.spinBoxAngle = QDoubleSpinBox(self.iface.mainWindow())
        self.lockBox = QCheckBox(self.iface.mainWindow())
        self.lockBoxAngle = QCheckBox(self.iface.mainWindow())
        # The inital value is 10
        self.spinBox.setValue(10.00)
        self.spinBoxAngle.setValue(0.00)
        # Set the minimum to zero, zero means that the distance is not considered
        self.spinBox.setDecimals(8)
        self.spinBox.setMinimum(0.000)
        self.spinBox.setMaximum(9999.999)
        self.spinBoxAngle.setDecimals(8)
        self.spinBoxAngle.setMinimum(-360.0)
        self.spinBoxAngle.setMaximum(360.0)
        self.iface.digitizeToolBar().addWidget( QLabel('dist') )
        self.spinBoxAction = self.iface.digitizeToolBar().addWidget(self.spinBox)
        self.lockBoxAction = self.iface.digitizeToolBar().addWidget(self.lockBox)
        self.spinBoxAction.setEnabled(False)
        self.lockBoxAction.setEnabled(False)
        self.iface.digitizeToolBar().addWidget( QLabel('angle') )
        self.spinBoxAction2 = self.iface.digitizeToolBar().addWidget(self.spinBoxAngle)
        self.lockBoxAction2 = self.iface.digitizeToolBar().addWidget(self.lockBoxAngle)
        self.iface.digitizeToolBar().addWidget( QLabel('abs') )
        self.absBoxAction = self.iface.digitizeToolBar().addWidget(self.absBox)
        self.spinBoxAction2.setEnabled(False)
        self.lockBoxAction2.setEnabled(False)
        self.absBoxAction.setEnabled(False)

        # Connect to signals for button behaviour
        QObject.connect(self.capturePolygonAction, SIGNAL("triggered()"), self.start)
        QObject.connect(self.iface, SIGNAL("currentLayerChanged(QgsMapLayer*)"), self.toggle)
    
        # This is the coordinates capture tool
        self.tool = QgsMapToolCapturePolygon(self.iface, self.absBox, self.spinBox, self.spinBoxAngle, self.lockBox, self.lockBoxAngle, self.isPolygon)

    def unload(self):
        """
        Remove the plugin menu item and icon from the toolbar
        """
        self.iface.digitizeToolBar().removeAction(self.capturePolygonAction)
        self.iface.digitizeToolBar().removeAction(self.absBoxAction)
        self.iface.digitizeToolBar().removeAction(self.spinBoxAction)
        self.iface.digitizeToolBar().removeAction(self.spinBoxAction2)
        self.iface.digitizeToolBar().removeAction(self.lockBoxAction)
        self.iface.digitizeToolBar().removeAction(self.lockBoxAction2)

    def toggle(self):
        layer = self.canvas.currentLayer()
         
        # Decide whether the plugin button/menu is enabled or disabled
        # Check first if the layer is not null and a vector layer
        if layer <> None and layer.type() == QgsMapLayer.VectorLayer:
            # Doesn't make sense for Points
            if layer.geometryType() == QGis.Polygon or layer.geometryType() == QGis.Line:
                if layer.isEditable():
                    self.capturePolygonAction.setEnabled(True)
                    self.absBoxAction.setEnabled(True)
                    self.spinBoxAction.setEnabled(True)
                    self.spinBoxAction2.setEnabled(True)
                    self.lockBoxAction.setEnabled(True)
                    self.lockBoxAction2.setEnabled(True)
                    QObject.connect(layer, SIGNAL("editingStopped()"), self.toggle)
                    QObject.disconnect(layer, SIGNAL("editingStarted()"), self.toggle)

                    if layer.geometryType() == QGis.Polygon:
                        self.capturePolygonAction.setIcon(QIcon(":/plugins/improvedpolygoncapturing/mActionCapturePolygon.png"))
                        self.capturePolygonAction.setToolTip(QCoreApplication.translate("ImprovedPolygonCapturing", "Capture Polygon with preset Edge Lengths"))
                        self.isPolygon = True
                    elif layer.geometryType() == QGis.Line:
                        self.capturePolygonAction.setIcon(QIcon(":/plugins/improvedpolygoncapturing/mActionCaptureLine.png"))
                        self.capturePolygonAction.setToolTip(QCoreApplication.translate("ImprovedPolygonCapturing", "Capture Line with preset Edge Lengths"))
                        self.isPolygon = False

                else:
                    self.capturePolygonAction.setEnabled(False)
                    self.absBoxAction.setEnabled(False)
                    self.spinBoxAction.setEnabled(False)
                    self.spinBoxAction2.setEnabled(False)
                    self.lockBoxAction.setEnabled(False)
                    self.lockBoxAction2.setEnabled(False)
                    self.stop()
                    QObject.connect(layer, SIGNAL("editingStarted()"), self.toggle)
                    QObject.disconnect(layer, SIGNAL("editingStopped()"), self.toggle)
         
    def start(self):
        """
        Starts capturing a new polygon. The current map tool is set to
        QgsMapToolCapturePolygon, the focus is given to the spin box and the
        capture polygon action is checked. Connect to the deactivate signal.
        """
        # This is the coordinates capture tool
        self.tool = QgsMapToolCapturePolygon(self.iface, self.absBox, self.spinBox, self.spinBoxAngle, self.lockBox, self.lockBoxAngle, self.isPolygon)

        # Save the previous selected tool and set the new capture coordinate tool
        self.previous = self.canvas.mapTool()
        self.canvas.setMapTool(self.tool)

        # Set focus to double spin box to convienient data entry
        self.spinBox.setFocus()
        self.spinBox.selectAll()

        self.capturePolygonAction.setChecked(True)

        # Stop the tool as soon as the QgsMapToolCapturePolygon is deactivated
        QObject.connect(self.tool, SIGNAL("deactivated()"), self.stop)

    def stop(self):
        """
        Stops the tool, i.e. the action in the toolbar is unchecked and the
        map canvas is cleared from the temporary markers and rubberband.
        """
        self.capturePolygonAction.setChecked(False)
        self.tool.clearMapCanvas()
        QObject.disconnect(self.tool, SIGNAL("deactivated()"), self.stop)
