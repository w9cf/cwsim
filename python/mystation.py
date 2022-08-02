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

import numpy as np
import station
from station import StationMessage

class MyStation(station.Station):
   def __init__(self,rng,keyer,contest,myCall,pitch,wpm,bufsize=512,rate=11025):
      super().__init__(rng,keyer,bufsize=bufsize,rate=rate)
      self._contest = contest
      self.myCall = myCall
      self.nr = 1
      self._rst = 599
      self.pitch = pitch
      self.wpm = wpm
      self._amplitude = 1.0
      self._pieces = []
      self.app = None

   def processEvent(self,evt):
      if evt == station.StationEvent.MsgSent:
         self._contest.onMeFinishedSending()

   def abortSend(self):
      self._envelop = None
      self._sendpos = 0
      self.msgs = [StationMessage.Garbage]
      self._msgtext = ''
      self._pieces = []
      self.state = station.StationState.Listening
      self.processEvent(station.StationEvent.MsgSent)

   def sendText(self,msg):
      p = msg.find('<his>')
      while p >= 0:
         if p !=0:
            self._pieces.append(msg[0:p])
         self._pieces.append('@')
         msg = msg[p+5:]
         p = msg.find('<his>')
      if len(msg) > 0:
         self._pieces.append(msg)
      if self.state != station.StationState.Sending:
         self.sendNextPiece()
         self._contest.onMeStartedSending()

   def sendNextPiece(self):
      self._msgtext = ''
      if self._pieces[0] != '@':
         super().sendText(self._pieces[0])
      else:
         super().sendText(self.hisCall)

   def getBuffer(self):
      buf = super().getBuffer()
      if self._envelop is None:
         self._pieces.pop(0)
         if len(self._pieces) > 0:
            self.sendNextPiece()
            if not (self.app is None):
               self.app.advance()
      return buf

   def updateCallInMessage(self,call): #check if sound thread problem?
      if call == '':
         return False
      if len(self._pieces) > 0: 
         res = self._pieces[0] == '@'
      else:
         res = False
      if res:
         s = self._keyer.encode(call.lower())
         ne  = self._keyer.getenvelop(s,self.wpm)*self._amplitude
         res = len(ne) >= self._sendpos
         if res:
            res = np.array_equiv(self._envelop[0:self._sendpos]
              ,ne[0:self._sendpos])
      if res:
         self._envelop = ne
         self.hisCall = call
      else:
         tmp = list(self._pieces)
         if len(tmp) > 0:
            tmp.pop(0)
            if '@' in tmp:
               res = True
               self.hisCall = call
      return res
