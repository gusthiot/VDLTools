#/***************************************************************************
# VDLTools
#
# Tools needed by the Ville de Lausanne
#-------------------
#	begin				: 2016-04-05
#	git sha				: $Format:%H$
#	copyright			: (C) 2016 by Christophe Gusthiot
#	email				: christophe.gusthiot@lausanne.ch
# ***************************************************************************/
#
#/***************************************************************************
# *									    *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or	    *
# *   (at your option) any later version.				    *
# *									    *
# ***************************************************************************/


LN_SOURCES=$(wildcard *.ts) $(wildcard **/*.ts)
LN_FILES=$(join $(dir $(LN_SOURCES)), $(notdir $(LN_SOURCES:%.ts=%.qm)))

default: compile

compile: resources.py $(LN_FILES)

$(LN_FILES): %.qm: %.ts
	lrelease $<

resources.py: resources.qrc
	pyrcc4 -o resources.py  resources.qrc

clean:
	rm -f resources.py i18n/*.qm *.pyc */*.pyc

prepare:
	rm -f *.pyc */*.pyc

update:
	lupdate i18n/VDLTools.pro
