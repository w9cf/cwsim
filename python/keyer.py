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
       "!":"---.", "$":"...-..-"," ":"", "_":"", ">":"", "<":""
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
      for i in range(len(txt)):
         char = txt[i]
         if char in [">", "<"]:
            s += char
         elif char in Keyer._morse:
            s += Keyer._morse[char]
            # Add space only if not the last char and next is not a speed marker
            if i < len(txt) - 1 and txt[i+1] not in [">", "<"]:
               s += " "
      if s != "":
         s += "~"
      return s

   def getenvelop(self,msg,wpm,l=30,s=50,p=50,speed_up_factor=0.20):
      """
         Arguments
            msg: morse encoding of dits and dahs
            wpm: speed in words per minute (PARIS)
            l: dash weight (default 30)
            s: space weight (default 50)
            p: dot weight (default 50)
            speed_up_factor: how much to increase speed (0 to 1)
         Returns
            keying envelop for audio samples
      """
      nr = len(self.rise)
      
      def get_params(current_wpm):
         T = 1.2 * self.rate / current_wpm
         d_on = int(np.rint(T * (p / 50.0)))
         da_on = int(np.rint(3.0 * T * (l / 30.0)))
         i_off = int(np.rint(T * (s / 50.0)))
         l_gap = int(np.rint(3.0 * T * (s / 50.0))) - i_off
         pad = int(np.rint(T))
         return d_on, da_on, i_off, l_gap, pad

      # First pass: Calculate total length
      total_samples = 0
      cur_wpm = wpm
      for char in msg:
         if char == '>':
            cur_wpm = wpm * (1.0 + speed_up_factor)
            continue
         elif char == '<':
            cur_wpm = wpm
            continue
         
         d_on, da_on, i_off, l_gap, pad = get_params(cur_wpm)
         if char == '.':
            total_samples += d_on + i_off
         elif char == '-':
            total_samples += da_on + i_off
         elif char == ' ':
            total_samples += l_gap
         elif char == '~':
            total_samples += pad
            
      n = int(self._bufsize*np.ceil((total_samples + nr + 100)/self._bufsize))
      env = np.zeros(n,dtype=np.float32)
      
      k = 0
      cur_wpm = wpm
      for char in msg:
         if char == '>':
            cur_wpm = wpm * (1.0 + speed_up_factor)
            continue
         elif char == '<':
            cur_wpm = wpm
            continue
            
         d_on, da_on, i_off, l_gap, pad = get_params(cur_wpm)
         
         if char == '.':
            pulse = np.ones(nr+d_on,dtype=np.float32)
            pulse[:nr] = self.rise
            pulse[d_on:] = self.fall
            if k+len(pulse) <= n:
               env[k:k+len(pulse)] = pulse
            k += d_on + i_off
         elif char == '-':
            pulse = np.ones(nr+da_on,dtype=np.float32)
            pulse[:nr] = self.rise
            pulse[da_on:] = self.fall
            if k+len(pulse) <= n:
               env[k:k+len(pulse)] = pulse
            k += da_on + i_off
         elif char == ' ':
            k += l_gap
         elif char == '~':
            k += pad
            
      return env
