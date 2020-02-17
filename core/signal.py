# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2017-07-14
        git sha              : $Format:%H$
        copyright            : (C) 2016 Ville de Lausanne
        author               : Christophe Gusthiot
        email                : cgusthiott@gmail.com
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

from builtins import object


class Signal(object):
    """
    Class for safely disconnect a signal
    """

    @staticmethod
    def safelyDisconnect(signal, handler):
        """
        To safely disconnect a signal
        :param signal: signal to disconnect
        :param handler: object from which we want to disconnect the signal
        """
        while True:
            try:
                if handler is not None:
                    signal.disconnect(handler)
                else:
                    signal.disconnect()
            except TypeError:
                break
