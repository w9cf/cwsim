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
import enum
import sys
from station import StationMessage

class Mc(enum.Enum):
   """
      My call is correct enumeration.
   """
   Yes = enum.auto()
   No = enum.auto()
   Almost = enum.auto()

class Os(enum.Enum):
   """
      States for operator state machine.
   """
   NeedPrevEnd = enum.auto()
   NeedQso = enum.auto()
   NeedNr = enum.auto()
   NeedCall = enum.auto()
   NeedCallNr = enum.auto()
   NeedEnd = enum.auto()
   Done = enum.auto()
   Failed = enum.auto()

class DxOperator():
   """
      Class for the state machine for an operator of a dxstation.
   """
   FULL_PATIENCE = 5
   def __init__(self,rng,minutes=0,cqstn=None,call=None,skills=2,
      s2bfac=11025/512,lids=True,rptProb=0.1,wpm=40,fast=1.1,slow=0.9,
      isSingle=False,state=Os.NeedPrevEnd):
      """
         Arguments
            rng: numpy random number generator
         Keyword arguments
            minutes: elapsed contest minutes -- for nr selection
            cqstn: The cq station we are answering
            call: My station's call
            skills: My skills
            isSingle: True if RunMode is single calls
            state: Initial operator state
      """
      self._rng = rng
      self.myCall = call
      self.cqstn = cqstn
      self.call = call
      self.skills = skills
      self.state = state
      self.patience = None
      self.repeatCnt= None
      self._minutes = minutes
      self._isSingle = isSingle
      self._lids = lids
      self._wpm = wpm
      self._slow = slow
      self._fast = fast
      self._rptProb = rptProb
      self._s2bfac = s2bfac

   def getSendDelay(self):
      """
         How long to wait to begin sending
      """
      if self.state == Os.NeedPrevEnd:
         return sys.maxsize
      else:
         return self._s2bfac*(0.1+0.5*self._rng.random())

   def getWpm(self):
      """
         Calculate my code speed.
      """
      return np.rint(self._wpm*(self._slow+(self._fast-self._slow)
         *self._rng.random()))

   def getNr(self):
      """
         Calculate my number.
      """
      return int(np.rint(1+self._rng.random()*self._minutes*self.skills))

   def getReplyTimeout(self):
      """
         Time to wait for a reply to me.
      """
      b = self._s2bfac*(6-self.skills)
      return np.clip(self._rng.standard_normal(1)*0.25*b+b,0.5*b,1.5*b)

   def decPatience(self):
      """
         Decrement patience and give up if zero
      """
      if self.state != Os.Done:
         self.patience -= 1
         if self.patience < 1:
            self.state = Os.Failed
         
   def setState(self,state):
      """
         Set operator state with side effects for patience and repeat count.
      """
      self.state = state
      if state == Os.NeedQso:
         self.patience = np.rint(self._rng.rayleigh(3.191538,1)) #4*sqrt(2/pi)
      else:
         self.patience = DxOperator.FULL_PATIENCE
      if (state == Os.NeedQso and (not self._isSingle) and
         self._rng.random() < 0.1):
         self.repeatCnt = 2
      else:
         self.repeatCnt = 1

   def ismycall(self):
      """
         Calculate edit distance from cq station's reply to my call,
         and decide if it is yes, no, or maybe. Lids make mistakes.
      """
      c0 = self.myCall
      c = self.cqstn.hisCall
      m = np.zeros([len(c)+1,len(c0)+1])
      m[:,0] = np.arange(len(c)+1)
      for x in range(1,len(c)):
         if c[x-1] != '?':
            for y in range(1,len(c0)+1):
               d = m[x-1,y-1]
               if c[x-1] != c0[y-1]: d += 1
               m[x,y] = np.min([m[x,y-1]+1,m[x-1,y]+1,d])
         else:
            for y in range(1,len(c0)+1):
               m[x,y] = np.min([m[x,y-1],m[x-1,y],m[x-1,y-1]])
      x = len(c)
      if c[x-1] != '?':
         for y in range(1,len(c0)+1):
            d = m[x-1,y-1]
            if c[x-1] != c0[y-1]: d += 1
            m[x,y] = np.min([m[x,y-1],m[x-1,y]+1,d])
      else:
         for y in range(1,len(c0)+1):
            m[x,y] = np.min([m[x,y-1],m[x-1,y],m[x-1,y-1]])
      if m[-1,-1] == 0:
         res = Mc.Yes
      elif m[-1,-1] == 1:
         res = Mc.Almost
      else:
         res = Mc.No

      if (not self._lids) and (len(c) == 2) and (res == Mc.Almost):
         res = Mc.No
      if (res == Mc.Yes) and ((len(c) != len(c0)) or ('?' in c)):
         res = Mc.Almost
      if len(c.replace('?','')) < 2:
         res = Mc.No
      if self._lids and (len(c) > 3):
         if res == Mc.Yes:
            if self._rng.random() < 0.01:
               res = Mc.Almost
         elif res == Mc.Almost:
            if self._rng.random() < 0.04:
               res = Mc.Yes
      return res 

   def msgReceived(self,msgs):
      """
         Make state machine transitions based on contents of msgs
         Arguments
            msgs: messages sent by cq station.
      """
      if StationMessage.CQ in msgs:
         if self.state == Os.NeedPrevEnd:
            self.setState(Os.NeedQso)
         elif self.state == Os.NeedQso:
            self.decPatience()
         elif self.state in [Os.NeedNr, Os.NeedCall, Os.NeedCallNr]:
            self.state = Os.Failed
         elif self.state == Os.NeedEnd:
            self.state = Os.Done
         return

      if StationMessage.Nil in msgs:
         if self.state == Os.NeedPrevEnd:
            self.setState(Os.NeedQso)
         elif self.state == Os.NeedQso:
            self.decPatience()
         elif self.state in [Os.NeedNr, Os.NeedCall, Os.NeedCallNr, Os.NeedEnd]:
            self.state = Os.Failed
         return   

      if StationMessage.HisCall in msgs:
         isme = self.ismycall()
         if isme == Mc.Yes:
            if self.state in [Os.NeedPrevEnd, Os.NeedQso, Os.NeedCallNr]:
               self.setState(Os.NeedNr)
            elif self.state == Os.NeedCall:
               self.setState(Os.NeedEnd)
         elif isme == Mc.Almost:
            if self.state in [Os.NeedPrevEnd, Os.NeedQso, Os.NeedNr]:
               self.setState(Os.NeedCallNr)
            elif self.state == Os.NeedEnd:
               self.setState(Os.NeedCall)
         elif isme == Mc.No:
            if self.state == Os.NeedQso:
               self.state = Os.NeedPrevEnd
            elif self.state in [Os.NeedNr, Os.NeedCall, Os.NeedCallNr]:
               self.state = Os.Failed
            elif self.state == Os.NeedEnd:
               self.state = Os.Done

      if StationMessage.B4 in msgs:
         if self.state in [Os.NeedPrevEnd, Os.NeedQso]:
            self.setState(Os.NeedQso)
         elif self.state in [Os.NeedNr, Os.NeedEnd]:
            self.state = Os.Failed

      if StationMessage.NR in msgs:
         if self.state == Os.NeedQso:
            self.state = Os.NeedPrevEnd
         elif self.state == Os.NeedNr:
            if self._rng.random() >= self._rptProb: 
               self.setState(Os.NeedEnd)
         elif self.state in [Os.NeedCallNr]:
            if self._rng.random() >= self._rptProb: 
               self.setState(Os.NeedCall)

      if StationMessage.TU in msgs:
         if self.state == Os.NeedPrevEnd:
            self.setState(Os.NeedQso)
         elif self.state == Os.NeedEnd:
            self.state = Os.Done

      if (not self._lids) and (msgs == [StationMessage.Garbage]):
         self.state = Os.NeedPrevEnd

      if self.state != Os.NeedPrevEnd:
         self.decPatience()

   def getReply(self):
      """
         Given current state, patience and relevant probabilities,
         return reply message.
      """
      if self.state in [Os.NeedPrevEnd, Os.Done, Os.Failed]:
         res = StationMessage.noMsg
      elif self.state == Os.NeedQso:
         res = StationMessage.MyCall
      elif self.state == Os.NeedNr:
         if (self.patience == (DxOperator.FULL_PATIENCE-1)
            or self._rng.random() < 0.3):
            res = StationMessage.NrQm
         else:
            res = StationMessage.AGN
      elif self.state == Os.NeedCall:
         r1 = self._rng.random() # Morserunner's probabilities are 0.5, 0.5*0.25
         if r1 < 0.5:
            res = StationMessage.DeMyCallNr1
         elif r1 < 0.625:
            res = StationMessage.DeMyCallNr2
         else:
            res = StationMessage.MyCallNr2
      elif self.state == Os.NeedCallNr:
         if self._rng.random() < 0.5:
            res = StationMessage.DeMyCall1
         else:
            res = StationMessage.DeMyCall2
      else: #NeedEnd
         if (self.patience == (DxOperator.FULL_PATIENCE-1)
            or self._rng.random() < 0.9):
            res = StationMessage.R_NR
         else:
            res = StationMessage.R_NR2
 
      return res

