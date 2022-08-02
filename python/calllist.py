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
