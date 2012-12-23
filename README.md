improvedpolygoncapturing2
=========================

How it works
------------

# Distance #
Distance must be entered in the first editfield. The first checkbox must be checked so the distance is locked to the editfield's value.

# Angle #
Angle must be entered in the second editfield. The second checkbox must be checked so the angle is locked to the editfield's value.
The third checkbox must be checked if the angle is entered in absolute value (if it's unchecked, the angle is calculated in relation to the last point)

# Usage #
Use tab and shift-tab to navigate between the editfields and the checkboxes (and space to toggle the checkboxes).


Todo
----

# General #
Is it possible to use the same concept but for every tool ?
The same input method could be usefull also for points layers and for advanced digitizine (split, reshape, ...)
Maybe the plugin could become a general input assistance plugin instead of being a specific tool.


# Interface #
With the input boxes, it would be more elegant to have the plugin in a specific palette (dockable). Currently, it's acceptable only when the palette is horizontal


# Details #
When the angle is fixed, the length, when defined by the mouse, should be the projection on the line instead of the absolute distance of the mouse to the last point

# Shortcuts #
Is it possible to set shortcuts to give the focus to the right editfield ? (for instance : d for distance, a for angle, shift-d to lock the distance, shift-a to lock the angle)

# Known bugs #
- The relative angle calculation must be tested, i've had some bugs sometimes.
- There's an error message when quitting QGIS