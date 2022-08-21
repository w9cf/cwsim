#
# Copyright (C) 2022 Kevin E. Schmidt. All rights reserved.
#
# This file is part of cwsim <https://github.com/w9cf/cwsim/>
#
# cwsim is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the
# Free Software Foundation and appearing in the file LICENSE included in the
# packaging of this file.
#
# cwsim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See https://www.gnu.org/licenses/ for GPL licensing information.
#
try:
   from PyQt6 import QtWidgets, QtCore
except ImportError:
   from PyQt5 import QtWidgets, QtCore

class TrLineEdit(QtWidgets.QLineEdit):

   def keyPressEvent(self,event):
      if ((event.key() == QtCore.Qt.Key.Key_A) and
         event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
         self.cursorWordBackward(False)
      elif ((event.key() == QtCore.Qt.Key.Key_S) and
         event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
         self.cursorBackward(False)
      elif ((event.key() == QtCore.Qt.Key.Key_D) and
         event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
         self.cursorForward(False)
      elif ((event.key() == QtCore.Qt.Key.Key_F) and
         event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
         self.cursorWordForward(False)
      elif ((event.key() == QtCore.Qt.Key.Key_G) and
         event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
         self.del_()
      elif ((event.key() == QtCore.Qt.Key.Key_W) and
         event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
         self.clear()
      elif ((event.key() == QtCore.Qt.Key.Key_Y) and
         event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
         self.clear()
      else:
         super(TrLineEdit,self).keyPressEvent(event)

