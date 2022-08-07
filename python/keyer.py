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
import math
import configparser
import os

class Keyer():
   """
      Class to encode text to morse and produce keying envelope from morse
   """

   _morse = ({ "a":".-", "b":"-...", "c":"-.-.", "d":"-..", "e":".", "f":"..-.",
       "g":"--.", "h":"....", "i":"..", "j":".---", "k":"-.-", "l":".-..",
       "m":"--", "n":"-.", "o":"---", "p":".--.", "q":"--.-", "r":".-.",
       "s":"...", "t":"-", "u":"..-", "v":"...-", "w":".--", "x":"-..-",
       "y":"-.--", "z":"--..", "0":"-----", "1":".----", "2":"..---",
       "3":"...--", "4":"....-", "5":".....", "6":"-....", "7":"--...",
       "8":"---..", "9":"----.", ".":".-.-.-", "-":"-....-", ",":"--..--",
       "?":"..--..", "/":"-..-.", ";":"-.-.-.", "(":"-.--.", "[":"-.--.",
       ")":"-.--.-", "]":"-.--.-", "@":".--.-.", "*":"...-.-", "+":".-.-.",
       "%":".-...", ":":"---...", "=":"-...-", '"':".-..-.", "'":".----.",
       "!":"---.", "$":"...-..-"," ":"", "_":""
   })

   def __init__(self,rate=11025,bufsize=512,risetime=0.005):
      """
         Keyword arguments
            rate: audio sample rate (default 11025)
            bufsize: audio buffer size (default 512)
            risetime: keyer risetime in seconds (default 0.005)
      """
      self.rate = rate
      self._bufsize = bufsize
      self.risetime = risetime

   @property
   def risetime(self):
      """
         keyer risetime in seconds
      """
      return self._risetime

   @risetime.setter
   def risetime(self,risetime):
      self._risetime = risetime
      x = np.arange(0.0,1.0,1.0/(2.7*risetime*self.rate))
      erf = np.frompyfunc(math.erf,1,1)
      self.rise = 0.5*(1.0+erf(5*(x-0.5))).astype(np.float32)
      self.fall = np.array(self.rise)
      self.fall[:] = self.rise[len(self.rise)::-1]

   def encode(self,txt):
      """
         Arguments:
            txt: ascii text to convert to morse
         Returns:
            string encoding for morse dits and dahs
      """
      s = ""
      for i in range(len(txt)-1):
         s += Keyer._morse[txt[i]] + " "
      s += Keyer._morse[txt[len(txt)-1]]
      if s != "":
         s += "~"
      return s

   def getenvelop(self,msg,wpm):
      """
         Arguments
            msg: morse encoding of dits and dahs
            wpm: speed in words per minute (PARIS)
         Returns
            keying envelop for audio samples
      """
      nr = len(self.rise)
      count = 2*(msg.count('.')+msg.count(' ')+2*msg.count('-'))+msg.count('~')
      samples = int(np.rint(1.2*self.rate/wpm))
      n = int(self._bufsize*np.ceil((count*samples+nr)/self._bufsize))
      env = np.zeros(n,dtype=np.float32)
      dit = np.ones(nr+samples,dtype=np.float32)
      dit[:nr] = self.rise
      dit[samples:] = self.fall
      dah = np.ones(nr+3*samples,dtype=np.float32)
      dah[:nr] = self.rise
      dah[3*samples:] = self.fall
      k = 0
      for i in range(len(msg)):
         if msg[i] == '.':
            env[k:k+len(dit)] = dit
            k += 2*samples
         elif msg[i] == '-':
            env[k:k+len(dah)] = dah
            k += 4*samples
         elif msg[i] == ' ':
            k += 2*samples-nr
         elif msg[i] == '~':
            k += samples-nr
      return env
