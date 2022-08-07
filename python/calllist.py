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
import sys
import os

class CallList():
   """
      Class to read call file and select calls randomly
   """
   def __init__(self,rng,callFile='MASTER.SCP'):
      """
         Arguments
            rng: numpy random number generator
         Keyword Arguments
            callFile: File in same directory with 1 callsign per line,
            # in first column is a comment (default MASTER.SCP).
      """
      self._rng = rng
      myDir = os.path.dirname(__file__)
      callFile = os.path.join(myDir,callFile)
      try:
         with open(callFile,'r') as f:
            calls = f.readlines()
      except EnvironmentError:
         print("Error processing " + callFile,file=sys.stderr)
         sys.exit(1)

      self._calls = [x for x in calls if not x.startswith('#')]
      for i in range(len(self._calls)):
         self._calls[i] = self._calls[i].replace('\n','')
      self._calls = sorted(set(self._calls))

   def pickCall(self):
      """
         Returns
            A randomly chosen callsign.
      """
      return self._calls[self._rng.integers(low=0,high=len(self._calls))]
