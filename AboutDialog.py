# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LiveStats
                                 A QGIS plugin
 Display live statistics about vector selections
                              -------------------
        begin                : 2012-12-30
        copyright            : (C) 2012 by Olivier Dalang
        email                : olivier.dalang@gmail.com
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
from qgis.core import *

class AboutDialog(QDialog):

    def __init__(self):
        QDialog.__init__(self)

        self.setMinimumWidth(600)
        self.setMinimumHeight(450)

        self.helpFile = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "python/plugins/improvedpolygoncapturing/README.html"
        
        self.setWindowTitle('Improved Polygon Capturing')

        txt = QTextBrowser()
        txt.setOpenExternalLinks(True)
        txt.setReadOnly(True)
        txt.setText( open(self.helpFile, 'r').read() )

        cls = QPushButton('Close')

        QObject.connect(cls,SIGNAL("pressed()"),self.accept)

        lay = QVBoxLayout()
        lay.addWidget(txt)
        lay.addWidget(cls)

        self.setLayout(lay)

        self.show()
