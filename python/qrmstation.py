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
import station
from station import StationMessage

class QrmStation(station.Station):
   qrm = [
      StationMessage.QRL,
      StationMessage.QRL2,
      StationMessage.QRL2,
      StationMessage.LongCQ,
      StationMessage.LongCQ,
      StationMessage.LongCQ,
      StationMessage.QSY
   ]
      
   def __init__(self,rng,keyer,callList,hisCall="",bufsize=512,rate=11025):
      super().__init__(rng,keyer,bufsize=bufsize,rate=rate)
      self._b2 = round(2*self._rate/self._bufsize)
      self._b6 = round(6*self._rate/self._bufsize)
      self.patience = rng.integers(low=1,high=6) # [1,5]
      self.hisCall = hisCall
      self.myCall = callList.pickCall()
      self._amplitude = 5000 + 25000*rng.random()
      self.pitch = rng.integers(low=-300,high=301)
      self.wpm = rng.integers(low=30,high=51)
      self.sendMsg(QrmStation.qrm[
         rng.integers(low=0,high=len(QrmStation.qrm))])

   def processEvent(self,evt):
      if evt == station.StationEvent.MsgSent:
         self.patience -= 1
         if self.patience > 0:
            self._timeout = self._rng.integers(self._b2,self._b6,endpoint=True)
         else:
            self.state = station.StationState.DeleteMe
      elif evt == station.StationEvent.Timeout:
         self.sendMsg(StationMessage.LongCQ)
