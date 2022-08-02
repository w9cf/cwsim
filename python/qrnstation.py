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
