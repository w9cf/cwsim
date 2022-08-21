# Copyright (C) 2022 Kevin E. Schmidt.
#
# This file is part of cwsim <https://github.com/w9cf/cwsim/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import numpy as np
import enum

NEVER = np.iinfo(np.int32).max

class StationMessage(enum.Enum):
   r'''
      Define messages that the station can receive
   '''
   NoMsg = enum.auto()
   CQ = enum.auto()
   NR = enum.auto()
   TU = enum.auto()
   MyCall = enum.auto()
   HisCall = enum.auto()
   B4 = enum.auto()
   Qm = enum.auto()
   Nil = enum.auto()
   Garbage = enum.auto()
   R_NR = enum.auto()
   R_NR2 = enum.auto()
   DeMyCall1 = enum.auto()
   DeMyCall2 = enum.auto()
   DeMyCallNr1 = enum.auto()
   DeMyCallNr2 = enum.auto()
   NrQm = enum.auto()
   LongCQ = enum.auto()
   MyCallNr2 = enum.auto()
   QRL = enum.auto()
   QRL2 = enum.auto()
   QSY = enum.auto()
   AGN = enum.auto()

class StationState(enum.Enum):
   r'''
   Define the states for the station state machine
   '''
   Listening = enum.auto()
   Copying = enum.auto()
   PreparingToSend = enum.auto()
   Sending = enum.auto()
   DeleteMe = enum.auto()

class StationEvent(enum.Enum):
   r'''
   Define station events that change state machine
   '''
   Timeout = enum.auto()
   MsgSent = enum.auto()
   MeStarted = enum.auto()
   MeFinished = enum.auto()

class Station():
   r'''
   Base class for stations.
   '''
   msg2txt = {
      StationMessage.CQ : 'TEST <my>',
      StationMessage.NR : '<#>',
      StationMessage.TU : 'TU',
      StationMessage.MyCall : '<my>',
      StationMessage.HisCall : '<his>',
      StationMessage.B4 : 'QSO B4',
      StationMessage.Qm : '?',
      StationMessage.Nil : 'NIL',
      StationMessage.R_NR: 'R <#>',
      StationMessage.R_NR2: 'R <#> <#>',
      StationMessage.DeMyCall1: 'DE <my>',
      StationMessage.DeMyCall2: 'DE <my> <my>',
      StationMessage.DeMyCallNr1: 'DE <my> <#>',
      StationMessage.DeMyCallNr2: 'DE <my> <my> <#>',
      StationMessage.MyCallNr2: '<my> <my> <#>',
      StationMessage.NrQm: 'NR?',
      StationMessage.LongCQ: 'CQ CQ TEST <my> <my> TEST',
      StationMessage.QRL: 'QRL?',
      StationMessage.QRL2: 'QRL?   QRL?',
      StationMessage.QSY: '<his> QSY QSY',
      StationMessage.AGN: 'AGN'
   }

   def __init__(self,rng,keyer,bufsize=512,rate=11025):
      """
          Arguments:
             rng: a numpy random number generator
             keyer: class that makes keying envelope
      """
      self._rng = rng
      self._keyer = keyer
      self._bufsize = bufsize
      self._rate = rate
      self.pitch = 500
      self.state = StationState.Listening
      self._envelop = None
      self._timeout = NEVER
      self._amplitude = 0.7
      self.wpm = 30
      self._rst = 599
      self.nr = 1
      self.nrWithError = False
      self.myCall = ''
      self.hisCall = ''
      self._msgtext = ''
      self._sendpos = 0
      self.msgs = []

   @property
   def pitch(self):
      return self._pitch

   @pitch.setter
   def pitch(self,f):
      self._pitch = f
      self._dphi = 2.0*np.pi*f/self._rate
      self._fbfo = 0.0

   def getBfo(self):
      bfo = np.arange(self._fbfo,self._fbfo+(self._bufsize-0.5)*self._dphi,
         self._dphi)
      self._fbfo = (self._fbfo+self._bufsize*self._dphi) % (2.0*np.pi)
      return bfo

   def getBuffer(self):
      buffer = self._envelop[self._sendpos:self._sendpos+self._bufsize]
      self._sendpos += self._bufsize
      if self._sendpos >= len(self._envelop):
         self._envelop = None
         self._sendpos = 0
      return buffer

   def sendText(self,msg):
      if msg.find('<#>') >= 0:
         msg = msg.replace('<#>',self.nrAsText(),1)
         msg = msg.replace('<#>',self.nrAsText())
      msg = msg.replace('<my>',self.myCall)
      msg = msg.replace('<his>',self.hisCall)
      if self._msgtext != '':
         self._msgtext = '{}{}{}'.format(self._msgtext,' ',msg)
      else:
         self._msgtext = msg
      s = self._keyer.encode(self._msgtext.lower())
      self._envelop = self._keyer.getenvelop(s,self.wpm)*self._amplitude
      self.state = StationState.Sending
      self._timeout = NEVER

   def sendMsg(self,stationmsg):
      if self._envelop is None:
         self.msgs = []
      if stationmsg == StationMessage.NoMsg:
         self.state = StationState.Listening
      else:
         self.msgs.append(stationmsg)
         self.sendText(Station.msg2txt[stationmsg])

   def tick(self):
      if self.state == StationState.Sending and self._envelop is None:
         self._msgtext = ''
         self.state = StationState.Listening
         self.processEvent(StationEvent.MsgSent)
      elif self.state != StationState.Sending:
         self._timeout -= 1
         if self._timeout < 0:
            self.processEvent(StationEvent.Timeout)

   def nrAsText(self):
      s = '{:d}{:03d}'.format(int(self._rst),int(self.nr))
      if self.nrWithError:
         if s[-1] in ['2','3','4','5','6','7']:
            if self._rng.random() < 0.5:
               s = '{:d}{:03d}{:s}{:03d}'.format(
                  self._rst,self.nr-1,'eeeee ',self.nr)
            else:
               s = '{:d}{:03d}{:s}{:03d}'.format(
                  self._rst,self.nr+1,'eeeee ',self.nr)
         elif s[-2] in ['2','3','4','5','6','7']:
            if self._rng.random() < 0.5:
               s = '{:d}{:03d}{:s}{:03d}'.format(
                  self._rst,self.nr-10,'eeeee ',self.nr)
            else:
               s = '{:d}{:03d}{:s}{:03d}'.format(
                  self._rst,self.nr+10,'EEEEE ',self.nr)
         self.nrWithError = False
      s = s.replace('599','5NN')
      s = s.replace('000','TTT')
      s = s.replace('00','TT')
      if self._rng.random() < 0.4:
         s = s.replace('0','O')
      elif self._rng.random() < 0.97:
         s = s.replace('0','T')
      if self._rng.random() < 0.97:
         s = s.replace('9','N')
      return s
