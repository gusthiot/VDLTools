# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin
 Tools needed by the Ville de Lausanne
                             -------------------
        begin                : 2016-04-05
        copyright            : (C) 2016 by Christophe Gusthiot
        email                : christophe.gusthiot@lausanne.ch
        git sha              : $Format:%H$
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


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load VDLTools class from file VDLTools.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .vdl_tools import VDLTools
    return VDLTools(iface)
