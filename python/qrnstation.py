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

class QrnStation(station.Station):
      
   def __init__(self,rng,bufsize=512,rate=11025):
      super().__init__(rng,None,bufsize=bufsize,rate=rate)
      nenv = int((round(rng.random()*rate/bufsize)+1)*bufsize)
      amp = 1.0e5*10.0**(2.0*rng.random())
      self._envelop = amp*(rng.random(nenv)-0.5)
      self._envelop[rng.random(nenv) < 0.99] = 0.0
      self.state = station.StationState.Sending

   def processEvent(self,evt):
      if evt == station.StationEvent.MsgSent:
         self.state = station.StationState.DeleteMe
