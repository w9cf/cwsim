import numpy as np
import station
from station import StationState
from station import StationEvent
from station import StationMessage
from dxoper import DxOperator
from dxoper import Os
from qsb import Qsb

class DxStation(station.Station):
   def __init__(self,rng,keyer,callList,cqstn,minutes=0,
      lids=True,lidNrProb=0.1,lidRstProb=0.03,qsb=True,flutterProb=0.3,
      rptProb=0.1,fast=1.1,slow=0.9,
      isSingle=False,bufsize=512,rate=11025):
      super().__init__(rng,keyer,bufsize=bufsize,rate=rate)
      self.cqstn = cqstn
      self.hisCall = self.cqstn.myCall
      self.myCall = callList.pickCall()
      self.called = False # have not transmitted yet
      self.oper = DxOperator(
         rng,
         minutes,
         call=self.myCall,
         skills=rng.integers(low=1,high=4),
         s2bfac=rate/bufsize,
         lids=lids,
         rptProb=rptProb,
         wpm=cqstn.wpm,
         fast=fast,
         slow=slow,
         isSingle = isSingle,
         state=Os.NeedPrevEnd,
         cqstn=cqstn)
      self.nrWithError = lids and (self._rng.random() < lidNrProb)
      self.wpm = self.oper.getWpm()
      self.nr = self.oper.getNr()
      if lids and self._rng.random() < lidRstProb:
         self._rst = 559+10*self._rng.integers(4)
      else:
         self._rst = 599
      self._qsb = None
      if qsb:
         if self._rng.random() < flutterProb:
            self._qsb = Qsb(self._rng,bandwidth=3.0+30.0*self._rng.random()
               ,bufsize=self._bufsize,rate=self._rate)
         else:
            self._qsb = Qsb(self._rng,bandwidth=0.1+0.5*self._rng.random()
               ,bufsize=self._bufsize,rate=self._rate)
      self._amplitude = 9000+18000*(1.0+np.sin(np.pi*(self._rng.random()-0.5)))
      self.pitch = np.fmod(self._rng.normal(0,150),300)
      self.state = StationState.Copying

   def processEvent(self,evt):
      if self.oper.state == Os.Done:
         return

      if evt == StationEvent.MsgSent:
         if self.cqstn.state == StationState.Sending:
            self._timeout = station.NEVER
         else:
            self._timeout = self.oper.getReplyTimeout()
      elif evt == StationEvent.Timeout:
         if self.state == StationState.Listening:
            self.oper.msgReceived([StationMessage.NoMsg])
            if self.oper.state == Os.Failed:
               self.state = StationState.DeleteMe
               return
            else:
               self.state = StationState.PreparingToSend
         if self.state == StationState.PreparingToSend:
            for i in range(self.oper.repeatCnt):
               reply = self.oper.getReply()
               self.called |= reply != StationMessage.NoMsg
               self.sendMsg(reply)
      elif evt == StationEvent.MeFinished:
         if self.state != StationState.Sending:
            if self.state == StationState.Copying:
               self.oper.msgReceived(self.cqstn.msgs)
            elif self.state in [StationState.Listening,
               StationState.PreparingToSend]:
               if (StationMessage.CQ in self.cqstn.msgs or 
                  StationMessage.TU in self.cqstn.msgs or
                  StationMessage.Nil in self.cqstn.msgs):
                  self.oper.msgReceived(self.cqstn.msgs)
               else:
                  self.oper.msgReceived([StationMessage.Garbage])
            if self.oper.state == Os.Failed:
               self.state = StationState.DeleteMe
               return
            else:
               self._timeout = self.oper.getSendDelay()
            self.state = StationState.PreparingToSend
        
      elif evt == StationEvent.MeStarted:
         if self.state != StationState.Sending:
            self.state = StationState.Copying
         self._timeout = station.NEVER

   def dataToLastQso(self):
      self.state = StationState.DeleteMe
      return self.myCall,self._rst,self.nr

   def getBuffer(self):
      buf = super().getBuffer()
      if self._qsb is not None:
         self._qsb.applyTo(buf)
      return buf
