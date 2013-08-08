# Improved Polygon Capturing 2 #

Improved Polygon Capturing is a [QGIS](http://www.qgis.org) [Python](http://www.python.org) plugin, that allows to digitize new polygons or lines with predefined edge lengths and angles, as you would do in a CAD program.

It is based upon Improved Polygon Capturing authored by Adrian Weber.


## How to use ##

The plugin adds a new icon to the digitizing toolbar.

Select a polygon or a line layer and toggle editing by clicking on the new icon.

A Dockable palette will appear.

From now on, you can enter the distance or the angle numerically in the edit fields. You have to check the "Lock" checkbox to actually lock the distance and/or the angle. Unlocked fields are entered using the mouse (which takes snapping into account).

You can also switch between absolute angle or relative angles (relatives angles are relative to the last line segment) by checking the "delta" icon.

Similar to the standard editing tools, left mouse clicks add new vertexes while right mouse clicks finish the geometry.

After finishing a new geometry the feature form opens and attributes can be entered.

### Shortcuts ###

The following shortcuts are available:

- alt+1 : focus the distance edit field
- alt+2 : focus the angle edit field
- alt+shift+1 : toggle the distance lock box
- alt+shift+2 : toggle the angle lock box
- alt+shift+3 : toggle the absolute angle box


## Caveats ##

The plugin calculates the distance in plain trigonometry. Thus **it is not recommended to use it in unprojected systems like EPSG:4326**.


## Feedback / bugs ##

Please send bugs and ideas on the issue tracker : [https://github.com/olivierdalang/improvedpolygoncapturing/issues](https://github.com/olivierdalang/improvedpolygoncapturing/issues)

Or send me some feedback at : olivier.dalang@gmail.com


## History ##

Improved polygon capturing plugin has been initially developed in June 2010 for a [land management and registration](http://www.gtz.de/en/weltweit/asien-pazifik/30296.htm) project in the Lao PDR by Adrian Weber.

It was used to digitize land parcels with known edge lengths from high-resolution satellite images. The parcel edges have been measured a priori in the field.


## Version history ##

- Version 0.8 (June 2010): first published version
- Version 0.9 (February 2011): added support for polyline layers and bug fixing
- Version 1.0 (July 2011): feature form opens in editing mode after finishing a new feature
- Version 1.1 (December 2012): added support for angle and updated interface
- Version 1.2 (August 2013): updated to work with QGIS 2.0 (thanks to Angelos Tzotsos), removed experimental flag

## Contribute ##

Help is welcome ! There's a serie of issues and ideas on the github repository : [https://github.com/olivierdalang/improvedpolygoncapturing.git](https://github.com/olivierdalang/improvedpolygoncapturing.git)

