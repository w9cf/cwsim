#!/usr/bin/env python3
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
import os
try:
   from PyQt6 import QtCore, QtGui, QtWidgets
   from PyQt6.QtWidgets import QApplication, QTableWidgetItem
   from PyQt6.QtGui import QShortcut
   from PyQt6.uic import compileUi
except ImportError:
   from PyQt5 import QtCore, QtGui, QtWidgets
   from PyQt5.QtWidgets import QApplication, QTableWidgetItem, QShortcut
   from PyQt5.uic import compileUi

try:
   uifilename = os.path.join(os.path.dirname(__file__),"cwsimgui.ui")
   pyfilename = os.path.join(os.path.dirname(__file__),"cwsimgui.py")
   if os.path.getmtime(uifilename) > os.path.getmtime(pyfilename):
      with open(pyfilename,"w") as py:
         compileUi(uifilename,py,indent=3)
   import cwsimgui
except FileNotFoundError:
   uifilename = os.path.join(os.path.dirname(__file__),"cwsimgui.ui")
   pyfilename = os.path.join(os.path.dirname(__file__),"cwsimgui.py")
   with open(pyfilename,"w") as py:
      compileUi(uifilename,py,indent=3)
   import cwsimgui

import re
import sys
import csv
import xdg.BaseDirectory
import numpy as np
import time
from contest import Contest, RunMode
from station import StationMessage
from station import StationState
from prefix import Prefix

class ToUpperRegularExpressionValidator(QtGui.QRegularExpressionValidator):
   def __init__(self,re,spacefn=None,*args,**kwargs):
      super().__init__(re,*args,**kwargs)

   def validate(self,string,pos):
      acceptable, string , pos =  super().validate(string,pos)
      return (acceptable, string.upper(), pos)

class RunApp(QtWidgets.QMainWindow,cwsimgui.Ui_CwsimMainWindow):

   advancesig = QtCore.pyqtSignal()
   qsysig = QtCore.pyqtSignal()
   lastqsosig = QtCore.pyqtSignal()
   contestendedsig = QtCore.pyqtSignal()


   def __init__(self,parent=None):
      super(RunApp,self).__init__(parent)
      self.setupUi(self)
      _translate = QtCore.QCoreApplication.translate
      self.tr = self.entryTabs.currentIndex() == 1
      self.re1 = re.compile(r"^[A-Z]{1,3}[0-9]+[A-Z]+$")
      self.re2 = re.compile(r"^[2-9][A-Z][0-9]+[A-Z]+$")
      self.re3 = re.compile(r"^[0-9A-Z]+[0-9]/[0-9A-Z]+$")
      self.re4 = re.compile(r"^[0-9A-Z]/[0-9A-Z]*[0-9][0-9A-Z]*$")
      self.started = False
      self.configpath = xdg.BaseDirectory.save_config_path("cwsim")
      os.makedirs(self.configpath,exist_ok=True)
      self.defaultini = os.path.join(self.configpath,"cwsim.ini")
      self.contest = Contest(np.random.default_rng(),inifile=self.defaultini)
      self.contest.me.app = self
      self.syncGui()
      self.advancesig.connect(self.advanceslot)
      self.qsysig.connect(self.qsyslot)
      self.lastqsosig.connect(self.lastQsoslot)
      self.contestendedsig.connect(self.contestEndedslot)
      self._mustAdvance = False
      self._hiscall = ""
      self._rst = ""
      self._nr = ""
      callval = ToUpperRegularExpressionValidator(
         QtCore.QRegularExpression(r'^[a-zA-Z0-9/?]*$'),self)
      nrval = QtGui.QRegularExpressionValidator(
         QtCore.QRegularExpression(r'^[0-9]*$'),self)
      trexval = ToUpperRegularExpressionValidator(
         QtCore.QRegularExpression(r'^\ *[0-9]*\ *[0-9]*\ *[a-zA-Z0-9/?]*$'),self)
      self.callLine.setValidator(callval)
      self.callEntry.installEventFilter(self)
      self.callEntry.setValidator(callval)
      self.trCallEntry.setValidator(callval)
      self.trCallEntry.installEventFilter(self)
      self.trExchangeEntry.setValidator(trexval)
      self.trExchangeEntry.installEventFilter(self)
      self.rstEntry.setValidator(nrval)
      self.rstEntry.installEventFilter(self)
      self.nrEntry.setValidator(nrval)
      self.nrEntry.installEventFilter(self)
      self.action_About.triggered.connect(self.about)
      self.actionKeyboard_Shortcuts.triggered.connect(self.shortcutHelp)
      self.action_Function_Key_CW.triggered.connect(self.FkeyHelp)
      self.callLine.textChanged.connect(self.mycall)
      self.callEntry.textChanged.connect(self.hiscall)
      self.trCallEntry.textChanged.connect(self.hiscall)
      self.trExchangeEntry.textChanged.connect(self.rcvdex)
      self.rstEntry.textChanged.connect(self.rcvdrst)
      self.nrEntry.textChanged.connect(self.rcvdnr)
      self.qskCheck.stateChanged.connect(self.qsk)
      self.cwReverseCheck.stateChanged.connect(self.cwreverse)
      self.wpmSpinBox.valueChanged.connect(self.wpm)
      self.pitchSpinBox.valueChanged.connect(self.pitch)
      self.bandwidthSpinBox.valueChanged.connect(self.bandwidth)
      self.monitorSlider.valueChanged.connect(self.monitor)
      self.ritSlider.valueChanged.connect(self.rit)
      self.qrnCheck.stateChanged.connect(self.qrn)
      self.qrmCheck.stateChanged.connect(self.qrm)
      self.qsyCheck.stateChanged.connect(self.qsyState)
      self.qsbCheck.stateChanged.connect(self.qsb)
      self.flutterCheck.stateChanged.connect(self.flutter)
      self.lidsCheck.stateChanged.connect(self.lids)
      self.startStopButton.clicked.connect(self.startStop)
      self.durationSpinBox.valueChanged.connect(self.duration)
      self.activitySpinBox.valueChanged.connect(self.activity)
      self.trF1Button.clicked.connect(self.f1)
      self.trF2Button.clicked.connect(self.f2)
      self.trF3Button.clicked.connect(self.f3)
      self.trF4Button.clicked.connect(self.f4)
      self.trF5Button.clicked.connect(self.f5)
      self.trF6Button.clicked.connect(self.f6)
      self.trF7Button.clicked.connect(self.f7)
      self.trF8Button.clicked.connect(self.f8)
      self.f1Button.clicked.connect(self.f1)
      self.f2Button.clicked.connect(self.f2)
      self.f3Button.clicked.connect(self.f3)
      self.f4Button.clicked.connect(self.f4)
      self.f5Button.clicked.connect(self.f5)
      self.f6Button.clicked.connect(self.f6)
      self.f7Button.clicked.connect(self.f7)
      self.f8Button.clicked.connect(self.f8)
      self.entryTabs.currentChanged.connect(self.entrytabs)
      self.action_Load_Configuration.triggered.connect(self.getFile)
      self.action_Save_Configuration.triggered.connect(self.putFile)
      self.action_Copy_Log.triggered.connect(self.saveLog)
      self.action_Update_Default_Configuration_on_Exit.triggered.connect(
         self.alwaysUpdate)
      self.action_Update_Default_Configuration.triggered.connect(
         self.updateFile)
      self.tqrmSpinBox.valueChanged.connect(self.tqrm)
      self.lidRstProbSpinBox.valueChanged.connect(self.lidRstProb)
      self.lidNrProbSpinBox.valueChanged.connect(self.lidNrProb)
      self.rptProbSpinBox.valueChanged.connect(self.rptProb)
      self.flutterProbSpinBox.valueChanged.connect(self.flutterProb)
      self.fastSpinBox.valueChanged.connect(self.fast)
      self.slowSpinBox.valueChanged.connect(self.slow)
      self.trExchangeEntry.setEnabled(False)
      self._callsent = False
      self._nrsent = False
      self._lastQso = [None,None,None]
      self._lastLog = [None,None,None]
      self._rawQsoCount = 0
      self._goodQsoCount = 0
      self._qtimes = []
      scdict = { "Alt+W":self.wipe, "Return":self.enter, "Escape":self.escape,
        "F1":self.f1, "F2":self.f2, "F3":self.f3, "F4":self.f4, "F5":self.f5,
        "F6":self.f6, "F7":self.f7, "F8":self.f8, "Shift+Up":self.ritup,
        "Shift+Down":self.ritdown, "Alt+C":self.ritclear, "Ctrl+Up":self.bwup,
        "Ctrl+Down":self.bwdown, "Alt+Up":self.pitchup,
        "Alt+Down":self.pitchdown, "PgUp":self.wpmup, "PgDown":self.wpmdown,
        "Up":self.uparrow, "Down":self.downarrow}
      self.sclist = []
      sc = QShortcut(QtGui.QKeySequence("Alt+X"),self)
      sc.activated.connect(self.startStop)
      for key, fun in scdict.items():
         sc = QShortcut(QtGui.QKeySequence(key),self)
         sc.activated.connect(fun)
         sc.setEnabled(False)
         self.sclist.append(sc)
      self.updateTime()
      self.clocktimer = QtCore.QTimer(self)
      self.clocktimer.timeout.connect(self.updateTime)
      self.ratetimer = QtCore.QTimer(self)
      self.ratetimer.timeout.connect(self.updateRate)
      nbin = self.contest.duration//5
      if nbin*5 < self.contest.duration: nbin += 1
      self.ratehist = np.zeros(nbin)
      self.ratePlot.canvas.setaxes(nbin,5,300)
      self.logTable.setHorizontalHeaderLabels(
         [_translate("RunApp","UTC"),_translate("RunApp","Call")
         ,_translate("RunApp","Recv"),_translate("RunApp","Sent")
         ,_translate("RunApp","Pref"),_translate("RunApp","Chk")])
      self.scoreTable.setHorizontalHeaderLabels(
         [_translate("RunApp","Points"),_translate("RunApp","Mults")
         ,_translate("RunApp","Score")])
      self.scoreTable.setVerticalHeaderLabels(
         [_translate("RunApp","Raw"),_translate("RunApp","Verified")])
      self._goodCalls = set()
      self._rawPfxs = set()
      self._goodPfxs = set()
      self.prefix = Prefix()

   def syncGui(self):
      self.action_Update_Default_Configuration_on_Exit.setChecked(
         self.contest.saveini != 0)
      self.callLine.setText(self.contest.call)
      self.wpmSpinBox.setValue(self.contest.wpm)
      self.bandwidthSpinBox.setValue(self.contest.bandwidth)
      self.pitchSpinBox.setValue(self.contest.pitch)
      self.qskCheck.setChecked(self.contest.qsk!=0)
      self.cwReverseCheck.setChecked(self.contest.cwreverse!=0)
      self.ritSlider.setValue(self.contest.rit)
      self.monitorSlider.setValue(int(self.contest.monitor*100))
      self.qrnCheck.setChecked(self.contest.qrn!=0)
      self.qrmCheck.setChecked(self.contest.qrm!=0)
      self.qsbCheck.setChecked(self.contest.qsb!=0)
      self.qsyCheck.setChecked(self.contest.qsy!=0)
      self.flutterCheck.setChecked(self.contest.flutter!=0)
      self.lidsCheck.setChecked(self.contest.lids!=0)
      self.activitySpinBox.setValue(self.contest.activity)
      self.durationSpinBox.setValue(self.contest.duration)
      self.tqrmSpinBox.setValue(self.contest.tqrm)
      self.lidRstProbSpinBox.setValue(self.contest.lidRstProb)
      self.lidNrProbSpinBox.setValue(self.contest.lidNrProb)
      self.rptProbSpinBox.setValue(self.contest.rptProb)
      self.flutterProbSpinBox.setValue(self.contest.flutterProb)
      self.fastSpinBox.setValue(self.contest.fast)
      self.slowSpinBox.setValue(self.contest.slow)
      if self.contest.mode == RunMode.pileup:
         self.contestComboBox.setCurrentIndex(0)
      elif self.contest.mode == RunMode.single:
         self.contestComboBox.setCurrentIndex(1)

   def getFile(self):
      _translate = QtCore.QCoreApplication.translate
      filename, filter  = QtWidgets.QFileDialog.getOpenFileName(self,
         caption=_translate("RunApp","Open Configuration")
         ,directory=self.configpath
         ,filter=_translate("RunApp","Configuration Files") + " (*.ini)")
      if filename != "":
         self.contest.readConfig(filename)
         self.syncGui()

   def putFile(self):
      filename, filter  = QtWidgets.QFileDialog.getSaveFileName(self,
         caption="Write Configuration",directory=self.configpath
         ,filter="Configuration Files (*.ini)")
      if filename != "":
         self.contest.writeConfig(filename)

   def updateFile(self):
      self.contest.writeConfig(self.defaultini)

   def saveLog(self):
      _translate = QtCore.QCoreApplication.translate
      filename, filter  = QtWidgets.QFileDialog.getSaveFileName(self,
         caption=_translate("RunApp","Save Log File")
         ,directory=os.getenv('HOME')
         ,filter=_translate("RunApp","csv") + " (*.csv)")
      if filename != "":
         columns = range(self.logTable.columnCount())
         header = []
         for i in columns:
            item = self.logTable.horizontalHeaderItem(i)
            if item is None:
               header.append("")
            else:
               header.append(item.text())
         with open(filename,'w') as f:
            writer = csv.writer(f,lineterminator='\n')
            writer.writerow(header)
            for i in range(self.logTable.rowCount()):
               row = []
               for j in columns:
                  item = self.logTable.item(i,j)
                  if item is None:
                     row.append("")
                  else:
                     row.append(item.text())
               writer.writerow(row)

   def alwaysUpdate(self,s):
      if s:
         self.contest.saveini = 1
      else:
         self.contest.saveini = 0

   def looksLikeCall(self,s):
      return (self.re1.match(s) is not None or
              self.re2.match(s) is not None or
              self.re3.match(s) is not None or
              self.re4.match(s) is not None)

   def eventFilter(self,source,event):
      if event.type() == QtCore.QEvent.Type.KeyPress:
         if " " in event.text():
            if not self.tr:
               self.space()
               return True
         elif "\t" in event.text() and self.started:
            self.tab()
            return True
      return super(RunApp,self).eventFilter(source,event)

   def hiscall(self,s):
      self._hiscall = s
      self._callsent = self.contest.me.updateCallInMessage(s)

   def rcvdnr(self,s):
      self._nr = s

   def rcvdrst(self,s):
      self._rst = s

   def rcvdex(self,s):
      s = s.split()
      for ss in s:
         if self.looksLikeCall(ss):
            self._hiscall = ss
#            self.trCallEntry.setText(ss)
            s.remove(ss)
      if len(s) == 0:
         self._nr = ""
         self._rst = ""
      elif len(s) == 1:
         if s[0].isdigit():
            self._nr = s[0]
            self._rst = "599"
      elif len(s) == 2:
         if len(s[0]) == 1 and s[0].isdigit():
            self._rst = '5'+s[0]+'9'
         self._nr = s[1]

   def resetCounters(self):
      self.contest.me.nr = 1
      self._lastQso = [None,None,None]
      self._lastLog = [None,None,None]
      self._rawQsoCount = 0
      self._goodQsoCount = 0
      self.logTable.setRowCount(0)
      self.scoreTable.clearContents()
      self.ratehist = np.zeros_like(self.ratehist)
      self.ratePlot.canvas.newData(self.ratehist)
      self._goodCalls.clear()
      self._rawPfxs.clear()
      self._goodPfxs.clear()
      self._qtimes = []

   def startStop(self):
      _translate = QtCore.QCoreApplication.translate
      if self.started:
         self.contest.stop()
         self.clocktimer.stop()
         self.ratetimer.stop()
         self.started = False
         self.startStopButton.setText(_translate("RunApp","Start"))
         for sc in self.sclist:
            sc.setEnabled(False)
      else:
         self.resetCounters()
         self.clocktimer.start(500)
         self.ratetimer.start(1000)
         i = self.contestComboBox.currentIndex()
         if i == 0:
            self.contest.mode = RunMode.pileup
         elif i==1:
            self.contest.mode = RunMode.single
         self.tr = self.entryTabs.currentIndex() == 1
         if self.tr:
            self.trCallEntry.setFocus()
         else:
            self.callEntry.setFocus()
         self.contest.start()
         self.startStopButton.setText(_translate("RunApp","Stop"))
         self.started = True
         for sc in self.sclist:
            sc.setEnabled(True)

   def about(self):
      version = "Testing version"
      msg = """
   Python CW Simulator {}
   Copyright 2022, Kevin E. Schmidt, W9CF, w9cf@arrl.net

   Based on and derivative of Morse Runner
   Copyright 2004-2006, Alex Shovkoplyas, VE3NEA
   ve3nea@dxatlast.com""".format(version)
      QtWidgets.QMessageBox.about(self,"CW Simulator",msg)

   def shortcutHelp(self):
      _translate = QtCore.QCoreApplication.transla
      msg = _translate("RunApp","""
   Keyboard Shortcuts:
      Alt+X = Start/Stop simulation run
   Only when simulation is running:
      Alt+W = Wipe
      Escape = Stop sending
      Enter = Enter sends message
      Up arrow = N1MM Tune RIT higher in frequency 25 Hz
      Down arrow = N1MM Tune RIT lower in frequency 25 Hz
      Shift+Up arrow = TR Tune RIT higher in frequency 25 Hz
      Shift+Down arrow = TR Tune RIT lower in frequency 25 Hz
      Alt+C = Clear RIT
      Ctrl+Up arrow  = Increase receive bandwidth 50 Hz
      Ctrl+Down arrow = Decrease receive bandwidth 50 Hz
      Alt+Up arrow = Increase pitch 50 Hz
      Alt+Down arrow = Decrease pitch 50 Hz
      Page Up = Increase cw speed 2 wpm
      Page Down = Decrease cw speed 2 wpm
      """)
      QtWidgets.QMessageBox.about(self,"Keyboard Shortcuts",msg)

   def FkeyHelp(self):
      _translate = QtCore.QCoreApplication.transla
      msg = _translate("RunApp","""
   Function Keys:
      F1 = Send CQ
      F2 = Send exchange
      F3 = Send TU to acknowledge receipt
      F4 = Send my call
      F5 = Send his call (Contents of the Call field)
      F6 = Send QSO B4
      F7 = Send a question mark
      F8 = Send Nil, not in log
      """)
      QtWidgets.QMessageBox.about(self,"Function key messages",msg)
      

   def mycall(self,s):
      self.contest.call = s

   def qsk(self,s):
      self.contest.qsk = (s // 2)

   def cwreverse(self,s):
      self.contest.cwreverse= (s // 2)

   def wpm(self,s):
      self.contest.wpm = s

   def pitch(self,s):
      self.contest.pitch = s

   def bandwidth(self,s):
      self.contest.bandwidth = s

   def monitor(self,s):
      self.contest.monitor = s/100.0

   def rit(self,s):
      self.contest.rit = s

   def qrn(self,s):
      self.contest.qrn = (s // 2)

   def qrm(self,s):
      self.contest.qrm = (s // 2)

   def qsyState(self,s):
      self.contest.qsy = (s // 2)

   def qsb(self,s):
      self.contest.qsb = (s // 2)

   def flutter(self,s):
      self.contest.flutter = (s // 2)

   def lids(self,s):
      self.contest.lids = (s // 2)


   def duration(self,s):
      self.contest.duration = s
      nbin = s//5
      if nbin*5 < s: nbin += 1
      h = np.zeros(nbin)
      if nbin > len(self.ratehist):
         h[:len(self.ratehist)] = self.ratehist[:]
      else:
         h[:] = self.ratehist[:nbin]
      self.ratehist = h
      self.ratePlot.canvas.setaxes(nbin,5,300)

   def activity(self,s):
      self.contest.activity = s

   def tqrm(self,s):
      self.contest.tqrm = s

   def lidRstProb(self,s):
      self.contest.lidRstProb = s
 
   def lidNrProb(self,s):
      self.contest.lidNrProb = s

   def rptProb(self,s):
      self.contest.rptProb = s

   def flutterProb(self,s):
      self.contest.flutterProb = s

   def fast(self,s):
      self.contest.fast = s
 
   def slow(self,s):
      self.contest.slow = s

   def updateTime(self):
      h,m,s = self.contest.time()
      tstr = '{:d}:{:02d}:{:02d}'.format(h,m,s)
      self.timeEntryLabel.setText(tstr)
      self.trTimeEntryLabel.setText(tstr)

   def updateRate(self):
      _translate = QtCore.QCoreApplication.translate
      rstr = _translate("RunApp","Rate")
      qstr = _translate("RunApp","QSOs/Hr (5m)")
      h,m,s = self.contest.time()
      s += 60*(m+60*h)
      tint = min(s,300)
      nt = len(self._qtimes)
      nq = 0
      for i in range(0,nt):
         if s-self._qtimes[nt-1-i] < 300:
            nq += 1
         else:
            break
      if nq == 0: return
      rate = int(round(nq*3600/tint))
      rateTitle = (rstr + " {:3d} " + qstr).format(rate)
      self.ratebox.setTitle(rateTitle)

   def f1(self):
      self.sendMsg(StationMessage.CQ)

   def f2(self):
      self.sendMsg(StationMessage.NR)

   def f3(self):
      self.sendMsg(StationMessage.TU)

   def f4(self):
      self.sendMsg(StationMessage.MyCall)

   def f5(self):
      self.sendMsg(StationMessage.HisCall)
      foc = QtWidgets.QApplication.focusWidget()
      if foc is self.callEntry:
         if self._rst == '':
            self.rstEntry.setText('599')
         else:
            self.rstEntry.setText('')

   def f6(self):
      self.sendMsg(StationMessage.B4)

   def f7(self):
      self.sendMsg(StationMessage.Qm)

   def f8(self):
      self.sendMsg(StationMessage.Nil)

   def entrytabs(self):
      self.tr = self.entryTabs.currentIndex() == 1

   def enter(self):
      if self.tr:
         self.trCallEntry.setText(self._hiscall)
      self._mustAdvance = False
      if self._hiscall == '':
         self.sendMsg(StationMessage.CQ)
      else:
         c = self._callsent
         n = self._nrsent
         r = self._nr != ""
         if (not c) or ((not n) and (not r)):
            self.sendMsg(StationMessage.HisCall)
         if not n:
            self.sendMsg(StationMessage.NR)
         if n and not r:
            self.sendMsg(StationMessage.Qm)
         if r and (c or n):
            self.sendMsg(StationMessage.TU)
            self.saveQso()
         else:
            self._mustAdvance = True

   def qsy(self):
      self.qsysig.emit()

   def qsyslot(self):
      try:
         call = self.contest.q.get_nowait()
         h,m,s = self.contest.time()
         tstr = '{:02d}:{:02d}:{:02d}'.format(h,m,s)
         r = self.logTable.rowCount()
         time.sleep(0) #yield
         self.logTable.insertRow(r)
         self.logTable.setItem(r,0,QTableWidgetItem(tstr))
         self.logTable.setItem(r,1,QTableWidgetItem(call))
         self.logTable.setItem(r,5,QTableWidgetItem("QSY"))
         QtCore.QTimer.singleShot(100,self.logTable.scrollToBottom)
      except:
         print("qsy call not found????")

   def advance(self):
      self.advancesig.emit()

   def advanceslot(self):
      if self._mustAdvance:
         if self.tr:
            self.trExchangeEntry.setEnabled(True)
            self.trExchangeEntry.setFocus()
         else:
            if self._rst == '':
               self.rstEntry.setText('599')
            else:
               self.rstEntry.deselect()
            if self._hiscall.find('?') == -1:
               self.nrEntry.setFocus()
            else:
               self.callEntry.setFocus()
         self._mustAdvance = False

   def lastQso(self):
      self.lastqsosig.emit()

   def lastQsoslot(self):
      try:
         (trueCall, trueRst, trueNr) = self.contest.q.get_nowait()
      except:
         print("Last q item not found????")
         return

      self._lastQso = [trueCall,trueNr,trueRst]
      goodPfx=self.prefix.getPrefix(trueCall)
      chk = self.checkQso()
      if chk == "NIL":
         return
      self._lastQso = [None,None,None]
      self._lastLog = [None,None,None]
      r = self.logTable.rowCount()-1
      if chk == "":
         if trueCall in self._goodCalls:
            self.logTable.item(r,5).setText("Dupe")
            return
         else:
            self._goodCalls.add(trueCall)

         if goodPfx not in self._goodPfxs:
            self._goodPfxs.add(goodPfx)
         else:
            goodPfx = ""
         self.logTable.item(r,5).setText("")
         self.logTable.item(r,4).setText(goodPfx)
         self._goodQsoCount += 1
         self.scoreTable.setItem(1,0,
            QTableWidgetItem(str(self._goodQsoCount)))
         self.scoreTable.setItem(1,1,QTableWidgetItem(
            str(len(self._goodPfxs))))
         score = str(self._goodQsoCount*len(self._goodPfxs))
         self.scoreTable.setItem(1,2,QTableWidgetItem(score))
      elif chk == "NR":
         self.logTable.item(r,5).setText("NR "+str(trueNr))
      elif chk == "RST":
         self.logTable.item(r,5).setText("RST "+str(trueRst))

   def contestEnded(self):
      self.contestendedsig.emit()

   def contestEndedslot(self):
      if self.started:
         self.startStop()
      self.started = False

   def sendMsg(self,msg):
      if msg == StationMessage.HisCall:
         if self._hiscall.strip() != '':
            self.contest.me.hisCall = self._hiscall.strip()
            self._callsent = True
         else:
            return
      self._nrsent = (msg == StationMessage.NR)
      self.contest.me.sendMsg(msg)

   def checkQso(self):
      if self._lastLog[0] != self._lastQso[0]: return "NIL"
      if self._lastLog[1] != self._lastQso[1]: return "NR"
      if self._lastLog[2] != self._lastQso[2]: return "RST"
      return ""
      

   def saveQso(self):
      time.sleep(0) #yield
      self._nrsent = False
      self._callsent = False
      self._rawQsoCount += 1
      h,m,s = self.contest.time()
      self._lastLog = [self._hiscall, int(self._nr), int(self._rst)]
      time.sleep(0) #yield
      rawPfx = self.prefix.getPrefix(self._hiscall)
      time.sleep(0) #yield
      goodPfx = rawPfx
      if rawPfx not in self._rawPfxs:
         self._rawPfxs.add(rawPfx)
      else:
         rawPfx = ""
      time.sleep(0) #yield
      chk = self.checkQso()
      time.sleep(0) #yield
      if chk == "":
         self._goodQsoCount += 1
         if goodPfx not in self._goodPfxs:
            self._goodPfxs.add(goodPfx)
         else:
            goodPfx = ""
         time.sleep(0) #yield
         self.scoreTable.setItem(1,0,QTableWidgetItem(str(self._goodQsoCount)))
         self.scoreTable.setItem(1,1,QTableWidgetItem(str(len(self._goodPfxs))))
         score = str(self._goodQsoCount*len(self._goodPfxs))
         self.scoreTable.setItem(1,2,QTableWidgetItem(score))
      time.sleep(0) #yield
      if chk in ["", "NR", "RST"]:
         self._lastLog = [None,None,None]
         self._lastQso = [None,None,None]
      tstr = '{:02d}:{:02d}:{:02d}'.format(h,m,s)
      rcvd = '{:03d} {:04d}'.format(int(self._rst),int(self._nr))
      sent = '{:03d} {:04d}'.format(599,self.contest.me.nr)
      time.sleep(0) #yield
      r = self.logTable.rowCount()
      time.sleep(0) #yield
      self.logTable.insertRow(r)
      self.logTable.setItem(r,0,QTableWidgetItem(tstr))
      self.logTable.setItem(r,1,QTableWidgetItem(self._hiscall))
      self.logTable.setItem(r,2,QTableWidgetItem(rcvd))
      self.logTable.setItem(r,3,QTableWidgetItem(sent))
      time.sleep(0) #yield
      if chk == "":
         self.logTable.setItem(r,4,QTableWidgetItem(goodPfx))
      else:
         self.logTable.setItem(r,4,QTableWidgetItem(rawPfx))
      time.sleep(0) #yield
      self.logTable.setItem(r,5,QTableWidgetItem(chk))
      time.sleep(0) #yield
      self.wipe()
      self.contest.me.nr += 1
      s += 60*m+3600*h
      i = int(s/300)
      if i >= len(self.ratehist): i -= 1
      self.ratehist[i] += 12
      time.sleep(0) #yield
      self.ratePlot.canvas.newData(self.ratehist)
      self.scoreTable.setItem(0,0,QTableWidgetItem(str(self._rawQsoCount)))
      self.scoreTable.setItem(0,1,QTableWidgetItem(str(len(self._rawPfxs))))
      time.sleep(0) #yield
      score = str(self._rawQsoCount*len(self._rawPfxs))
      self.scoreTable.setItem(0,2,QTableWidgetItem(score))
      time.sleep(0) #yield
      self._qtimes.append(s)
      time.sleep(0) #yield
      QtCore.QTimer.singleShot(100,self.logTable.scrollToBottom)

   def wipe(self):
      if self.tr:
         self.trCallEntry.setText("")
         self.trExchangeEntry.setText("")
         self.trCallEntry.setFocus()
         self.trExchangeEntry.setEnabled(False)
      else:
         self.callEntry.setText("")
         self.rstEntry.setText("")
         self.nrEntry.setText("")
         self.callEntry.setFocus()
      self._callsent = False
      self._nrsent = False

   def escape(self):
      if StationMessage.HisCall in self.contest.me.msgs:
         self._callsent = False
      if StationMessage.NR in self.contest.me.msgs:
         self._nrsent = False
      if self.contest.me.state == StationState.Sending:
         self.contest.me.abortSend()
      elif self.tr and self.trExchangeEntry.isEnabled():
         self.trExchangeEntry.clear()
         self.trExchangeEntry.setEnabled(False)
         self.trCallEntry.setFocus()
      else:
         self.wipe()

   def ritup(self):
      self.ritSlider.setValue(25*round(int((self.contest.rit+25)/25)))

   def ritdown(self):
      self.ritSlider.setValue(25*round(int((self.contest.rit-25)/25)))

   def ritclear(self):
      self.ritSlider.setValue(0)

   def bwup(self):
      self.bandwidthSpinBox.setValue(self.contest.bandwidth+50)

   def bwdown(self):
      self.bandwidthSpinBox.setValue(self.contest.bandwidth-50)

   def pitchup(self):
      self.pitchSpinBox.setValue(self.contest.pitch+50)

   def pitchdown(self):
      self.pitchSpinBox.setValue(self.contest.pitch-50)

   def wpmup(self):
      self.wpmSpinBox.setValue(self.contest.wpm+2)

   def wpmdown(self):
      self.wpmSpinBox.setValue(self.contest.wpm-2)

   def uparrow(self):
      if self.tr:
         foc = QtWidgets.QApplication.focusWidget()
         if foc is self.trExchangeEntry:
            self.trCallEntry.setFocus()
      else:
         self.ritup()

   def downarrow(self):
      if self.tr:
         foc = QtWidgets.QApplication.focusWidget()
         if foc is self.trCallEntry:
            self.trExchangeEntry.setEnabled(True)
            self.trExchangeEntry.setFocus()
      else:
         self.ritdown()

   def space(self):
      if self.tr: return
      self._mustAdvance = False
      foc = QtWidgets.QApplication.focusWidget()
      if foc in [self.callEntry, self.rstEntry]:
         if self._rst == '':
            self.rstEntry.setText('599')
         else:
            self.rstEntry.deselect()
         self.nrEntry.setFocus()
      else:
         self.callEntry.setFocus()

   def tab(self):
      foc = QtWidgets.QApplication.focusWidget()
      if foc is self.callEntry:
         self.rstEntry.setFocus()
         if len(self._rst) == 3:
            self.rstEntry.setSelection(1,1)
      elif foc == self.rstEntry:
         self.nrEntry.setFocus()
         self.nrEntry.deselect()
      elif foc == self.nrEntry:
         self.callEntry.setFocus()
         i = self._hiscall.find('?')
         if i>= 0:
            self.callEntry.setSelection(i,1)
         else:
            self.callEntry.deselect()
            self.callEntry.end(False)
      elif foc is self.trCallEntry:
         self.trExchangeEntry.setFocus()
      elif foc is self.trExchangeEntry:
         self.trCallEntry.setFocus()

   def close(self):
      if not os.path.exists(self.defaultini) or self.contest.saveini != 0:
         self.contest.writeConfig(self.defaultini)
      super().close()
      

if __name__ == "__main__":
   app = QApplication(sys.argv)
   translator = QtCore.QTranslator()
   if getattr(sys,'frozen',False):
      tdir = os.path.dirname(sys.executable)
   else:
      tdir = os.path.dirname(__file__)
   tfile = QtCore.QLocale.system().name() + '.qm'
   tdir = os.path.join(tdir,'translate')
   translator.load(tfile,tdir)
   app.installTranslator(translator)
   form = RunApp()
   form.show()
   app.exec()
