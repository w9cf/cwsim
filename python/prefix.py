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
import re

class Prefix():

   def __init__(self):
      self._nre = re.compile(r'[0-9]')

   def getPrefix(self,call):
      parts = call.strip().split('/')
      np = len(parts)
      pfx = self._getPrefixNoStroke(parts[0])
      if np < 2 or (len(parts[1])>2 and parts[1].isalpha()):
         return pfx
      else:
         if len(parts[1]) == 1:
            if parts[1].isdigit():
               pfx = pfx[0:len(pfx)-1]+parts[1]
            return pfx
         else:
            if len(parts[0]) > len(parts[1]):
               pfx = self._getPrefixNoStroke(parts[1])
            if pfx[-1].isdigit():
               return pfx
            else:
               return pfx+'0'
   
   def _getPrefixNoStroke(self,call):
      if not call.isalnum():
         return ''
      if call.isalpha() or ((len(call) == 2) and call[0].isdigit()):
         return call+'0'
      i = list(self._nre.finditer(call))[-1].span(0)[1]
      if i > 1:
         return call[:i]
      return ''

if __name__ == "__main__":
   p = Prefix()
   with open("MASTER.SCP","r") as f:
      while True:
         c = f.readline().rstrip()
         if len(c) == 0:
            break
         c = c.rstrip()
         pfx = p.getPrefix(c)
         print(c,pfx,pfx,len(pfx),len(pfx))
