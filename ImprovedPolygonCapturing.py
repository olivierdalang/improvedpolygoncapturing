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

        # Create a dock widget for the input fields (note that the dockwidget is only added to the mainWindow when the tool is activated)
        self.dockWidget = QDockWidget("Improved Polygon Capturing")
        self.dockWidget.setFeatures(QDockWidget.DockWidgetMovable|QDockWidget.DockWidgetFloatable)
        self.dockLayout = QGridLayout()
        self.dockLayout.setColumnStretch( 1, 10 )
        self.dockLayout.setRowStretch( 3, 10 )
        dockWidgetMainWidget = QWidget()
        self.dockWidget.setWidget( dockWidgetMainWidget )
        dockWidgetMainWidget.setLayout(self.dockLayout)
        self.iface.mainWindow().addDockWidget(Qt.LeftDockWidgetArea, self.dockWidget)
        self.dockWidget.hide()

        # Create and setup the input elements
        self.spinBoxDist = QDoubleSpinBox()
        self.spinBoxDist.setValue(10.00)
        self.spinBoxDist.setDecimals(8)
        self.spinBoxDist.setMinimum(-9999999.999)
        self.spinBoxDist.setMaximum(9999999.999)
        self.lockBoxDist = QCheckBox()

        self.spinBoxAngle = QDoubleSpinBox()
        self.spinBoxAngle.setValue(0.00)
        self.spinBoxAngle.setDecimals(8)
        self.spinBoxAngle.setMinimum(-360.0)
        self.spinBoxAngle.setMaximum(360.0)
        self.spinBoxAngle.setSuffix(unichr(176))
        self.lockBoxAngle = QCheckBox()
        self.absBox = QCheckBox()

        # Layout the input elements
        self.dockLayout.addWidget( QLabel('Lk'),0,2 )
        self.dockLayout.addWidget( QLabel('Abs'),0,3 )
        self.dockLayout.addWidget( QLabel('Distance'),1,0 )
        self.dockLayout.addWidget(self.spinBoxDist,1,1)
        self.dockLayout.addWidget(self.lockBoxDist,1,2)
        self.dockLayout.addWidget( QLabel('Angle'),2,0 )
        self.dockLayout.addWidget(self.spinBoxAngle,2,1)
        self.dockLayout.addWidget(self.lockBoxAngle,2,2)
        self.dockLayout.addWidget(self.absBox,2,3)

        # Create tooltips
        self.spinBoxDist.setToolTip('Distance (alt+1)')
        self.spinBoxAngle.setToolTip('Angle (alt+2)')
        self.lockBoxDist.setToolTip('Lock distance (shift+alt+1)')
        self.lockBoxAngle.setToolTip('Lock angle (shift+alt+2)')
        self.absBox.setToolTip('Absolute angle (shift+alt+3')

        # Create shortcuts
        QObject.connect( QShortcut(QKeySequence("alt+1"), self.iface.mapCanvas()), SIGNAL("activated()"), self.focusDist)
        QObject.connect( QShortcut(QKeySequence("alt+2"), self.iface.mapCanvas()), SIGNAL("activated()"), self.focusAngle)
        QObject.connect( QShortcut(QKeySequence("shift+alt+1"), self.iface.mapCanvas()), SIGNAL("activated()"), self.toggleLockDist)
        QObject.connect( QShortcut(QKeySequence("shift+alt+2"), self.iface.mapCanvas()), SIGNAL("activated()"), self.toggleLockAngle)
        QObject.connect( QShortcut(QKeySequence("shift+alt+3"), self.iface.mapCanvas()), SIGNAL("activated()"), self.toggleAbsAngle)

        # Connect to signals for button behaviour
        QObject.connect(self.capturePolygonAction, SIGNAL("triggered()"), self.start)
        QObject.connect(self.iface, SIGNAL("currentLayerChanged(QgsMapLayer*)"), self.toggle)
    
        # This is the coordinates capture tool
        self.tool = QgsMapToolCapturePolygon(self.iface, self.absBox, self.spinBoxDist, self.spinBoxAngle, self.lockBoxDist, self.lockBoxAngle, self.isPolygon)

    def focusAngle(self):
        """
        Gives the focus to angle input (used for by the shortcut action)
        """
        self.spinBoxAngle.setFocus()
        self.spinBoxAngle.selectAll()
    def focusDist(self):
        """
        Gives the focus to distance input (used for by the shortcut action)
        """
        self.spinBoxDist.setFocus()
        self.spinBoxDist.selectAll()
    def toggleLockAngle(self):
        """
        Toggles the angle lock (used for by the shortcut action)
        """
        self.lockBoxAngle.toggle()
    def toggleLockDist(self):
        """
        Toggles the distance lock (used for by the shortcut action)
        """
        self.lockBoxDist.toggle()
    def toggleAbsAngle(self):
        """
        Toggles the distance lock (used for by the shortcut action)
        """
        self.absBox.toggle()

    def unload(self):
        """
        Remove the plugin menu item and icon from the toolbar
        """
        self.dockWidget = None
        self.iface.digitizeToolBar().removeAction(self.capturePolygonAction)

    def toggle(self):
        layer = self.canvas.currentLayer()
         
        # Decide whether the plugin button/menu is enabled or disabled
        # Check first if the layer is not null and a vector layer
        if layer <> None and layer.type() == QgsMapLayer.VectorLayer:
            # Doesn't make sense for Points
            if layer.geometryType() == QGis.Polygon or layer.geometryType() == QGis.Line:
                if layer.isEditable():
                    self.capturePolygonAction.setEnabled(True)
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
                    self.stop()
                    QObject.connect(layer, SIGNAL("editingStarted()"), self.toggle)
                    QObject.disconnect(layer, SIGNAL("editingStopped()"), self.toggle)
         
    def start(self):
        """
        Starts capturing a new polygon. The current map tool is set to
        QgsMapToolCapturePolygon, the dockwidget is shown focus is given to the spin box and the
        capture polygon action is checked. Connect to the deactivate signal.
        """
        # This is the coordinates capture tool
        self.tool = QgsMapToolCapturePolygon(self.iface, self.absBox, self.spinBoxDist, self.spinBoxAngle, self.lockBoxDist, self.lockBoxAngle, self.isPolygon)

        # Save the previous selected tool and set the new capture coordinate tool
        self.previous = self.canvas.mapTool()
        self.canvas.setMapTool(self.tool)

        # Show the dockWidget, give it the focus, and display the tool as checked
        self.dockWidget.show()
        self.focusDist()
        self.capturePolygonAction.setChecked(True)

        # Stop the tool as soon as the QgsMapToolCapturePolygon is deactivated
        QObject.connect(self.tool, SIGNAL("deactivated()"), self.stop)

    def stop(self):
        """
        Stops the tool, i.e. the action in the toolbar is unchecked, the dockwidget is hidden and the
        map canvas is cleared from the temporary markers and rubberband.
        """

        self.dockWidget.hide()

        self.capturePolygonAction.setChecked(False)

        self.tool.clearMapCanvas()
        QObject.disconnect(self.tool, SIGNAL("deactivated()"), self.stop)
