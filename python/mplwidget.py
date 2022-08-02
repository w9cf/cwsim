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
   from PyQt6 import QtWidgets
   from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as Canvas
except ImportError:
   from PyQt5 import QtWidgets
   from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas

from matplotlib.figure import Figure
import matplotlib
import numpy as np

class MplCanvas(Canvas):
   def __init__(self):
      scale = 1
      self.fig = Figure(figsize=(5*scale,4*scale),dpi=100)
      self.fig.set_tight_layout(True)
      Canvas.__init__(self, self.fig)
      self.ax = self.fig.add_subplot()
      Canvas.updateGeometry(self)

   def setaxes(self,nbin,dt,maxrate):
      self.ax.clear()
      self.ax.set_xlabel("Minutes")
      self.ax.set_ylabel("QS0s/Hour")
      self.nbin = nbin
      self.dt = dt
      self.maxrate = maxrate
      self.ax.set_xlim(0,dt*self.nbin)
      self.ax.set_ylim(0,self.maxrate)
      self.ax.grid()
      self.t = np.arange(self.nbin)*self.dt+0.5*dt
      rate = np.zeros(self.nbin)
      self.bar = self.ax.bar(self.t,rate,width=0.8*self.dt,color='blue')
      self.fig.canvas.draw()

   def newData(self,rate):
      for i in range(self.nbin):
         self.bar.patches[i].set_height(rate[i])
      self.fig.canvas.draw()

class MplWidget(QtWidgets.QFrame):
   def __init__(self, parent=None):
      QtWidgets.QWidget.__init__(self,parent)
      self.canvas = MplCanvas()
      self.vbl = QtWidgets.QVBoxLayout()
      self.vbl.addWidget(self.canvas)
      self.setLayout(self.vbl)

   def setTitle(self,t):
      pass
