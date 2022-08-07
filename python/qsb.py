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
import audioprocess

class Qsb():
   """
      Class to adjust gain to simulate QSB.
   """
   def __init__(self,rng,bandwidth=0.1,bufsize=512,rate=11025):
      """
         Arguments:
            rng: a numpy random number generator
         Keyword Arguments:
            bandwidth: The inverse of the correlation time for the
               (approximate) gaussian process (default 0.1).
      """
      self.buf4 = bufsize // 4
      self.rate = rate
      self._av1 = None
      self._av2 = None
      self._av3 = None
      self._buf = None
      self._bufptr = None
      self._bufsize = None
      self._norm = None
      self._gain0 = None
      self._rng = rng
      self.bandwidth = bandwidth

   @property
   def bandwidth(self):
      """
         The inverse of the correlation time for the (approximate) gaussian
         process.
      """
      return self._bandwidth

   @bandwidth.setter
   def bandwidth(self,b):
      self._bandwidth = b
      navg = np.max([int(np.ceil(0.37*self.rate/(self.buf4*b))),1])
      self._norm = np.sqrt(3.0*navg)
      self._bufsize = np.max([navg+4-(navg % 4),100])
      self._av1 = audioprocess.movavg(self._bufsize,navg,dtype=np.complex128)
      self._av2 = audioprocess.movavg(self._bufsize,navg,dtype=np.complex128)
      self._av3 = audioprocess.movavg(self._bufsize,navg,dtype=np.complex128)
      bufptr = 3*navg
      self._newbuf()
      while self._bufsize < bufptr:
         self._newbuf()
         bufptr -= self._bufsize
      self._gain0 = self._buf[bufptr]
      self._bufptr = bufptr+1
      if self._bufptr >= self._bufsize:
         self._newbuf()

   def _newbuf(self):
      r2 = 2.0*self._rng.random(2*self._bufsize)-1.0
      r = r2[::2]+1j*r2[1::2]
      self._buf = np.abs(
         self._av3.avg(self._av2.avg(self._av1.avg(r))))*self._norm
      self._bufptr = 0

   def applyTo(self,buf):
      """
         Applies the sampled process gain to the buffer. 4 samples are used
         and the gain is linearly interpolated between them.
      """
      i4 = self.buf4
      for i in range(4):
         g1 = self._buf[self._bufptr]
         buf[i*i4:(i+1)*i4] *= np.linspace(self._gain0,g1,i4,endpoint=False)
         self._gain0 = g1
         self._bufptr += 1
         if self._bufptr >= self._bufsize:
            self._newbuf()
