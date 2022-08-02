#
# Copyright (C) 2022 Kevin E. Schmidt. All rights reserved.
#
# This file is part of cwsim <https://github.com/w9cf/cwsim/>
#
# cwsim is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the
# Free Software Foundation and appearing in the file LICENSE included in the
# packaging of this file.
#
# cwsim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See https://www.gnu.org/licenses/ for GPL licensing information.
#

import numpy as np
import enum
import keyer
import calllist
from audioprocess import movavg, modulator, agc
from station import StationEvent, StationState, StationMessage
from qrmstation import QrmStation
from qrnstation import QrnStation
from dxstation import DxStation
from mystation import MyStation
from dxoper import Os
import queue
import wave
import time
import sys
import os
import errno
import configparser
import sounddevice as sd

class RunMode(enum.IntEnum):
  stop = 1
  pileup = 2
  single = 3

class Contest():
   """
      Class to hold contest stations and produce audio buffers
   """
   def __init__(self,rng,inifile=None):
      """
         Arguments
            rng = numpy random number generator
            inifile = initialization file name
      """
      self.modulator = None
      self.me = None
      try:
         self.readConfig(inifile)
      except:
         self._rate = 11025
         self._bufsize = 512
         self.call = "P55CF"
         self.wpm = 40
         self.fast = 1.1
         self.slow = 0.9
         self.bandwidth = 500
         self.pitch = 500
         self.qsk = 1
         self.qskdecaytime = 0.030
         self.rit = 0
         self.monitor = 0.1
         self.qrn = 1
         self.qrm = 1
         self.qsb = 1
         self.qsy = 1
         self.flutter = 1
         self.flutterProb = 0.3
         self.lids = 1
         self.activity = 4
         self.lidRstProb = 0.03
         self.lidNrProb = 0.1
         self.rptProb = 0.1
         self.tqrm = 240
         self.duration = 60
         self.mode = RunMode.pileup
         self.cwreverse = 0
         self.savewave = 0
         self.fontsize = 12 # not used
         
      self._qskdecayfactor = 1.0/(self._rate*self.qskdecaytime)
      self.q = queue.Queue()
      self.modulator = modulator(self._bufsize,self._rate,self.pitch
         ,reverse=self.cwreverse == 1)
      self._m5 = agc(self._bufsize)
      self._rng = rng
      self._keyer = keyer.Keyer(rate=self._rate,bufsize=self._bufsize)
      self._callList = calllist.CallList(rng)
      self.stations = []
      self.me = MyStation(self._rng,self._keyer,self,self.call,self.pitch
         ,self.wpm,bufsize=self._bufsize,rate=self._rate)
      self.bufcount = 0
      self._rfg0 = 1.0
      self._rfg = np.zeros(self._bufsize+1,dtype=np.float64)
      self._rfgcal = np.frompyfunc(self.rfgfun,2,1)
      self._ritph = 0.0
      self._bufindex = np.arange(self._bufsize,dtype=np.float64)
#      self.ef = open('temp.out',mode='w')
#      self.ef.close()
#      self.ef = open('temp.out',mode='a')
#      self.wf = wave.open('temp.wav',mode='wb')
#      self.wf.setnchannels(1)
#      self.wf.setsampwidth(2)
#      self.wf.setframerate(self._rate)
   @property
   def tqrm(self):
      """
         Mean time for QRM station
      """
      return self._tqrm

   @tqrm.setter
   def tqrm(self,tqrm):
      self._tqrm = tqrm
      self.qrmProbPerBuffer = self._bufsize/self._rate/self._tqrm

   @property
   def bandwidth(self):
      """
         Filter bandwidth for receive audio
      """
      return self._bandwidth

   @bandwidth.setter
   def bandwidth(self,bandwidth):
      self._bandwidth = np.max([np.min([round(bandwidth/50)*50,600]),100])
      navg = int(np.rint(0.7*self._rate/self._bandwidth))
      self._fgain = np.sqrt(500/self._bandwidth);
      self._m1 = movavg(self._bufsize,navg,dtype=np.complex128)
      self._m2 = movavg(self._bufsize,navg,dtype=np.complex128)
      self._m3 = movavg(self._bufsize,navg,dtype=np.complex128)

   @property
   def pitch(self):
      """
         Filter center pitch for receive audio
      """
      return self._pitch

   @pitch.setter
   def pitch(self,pitch):
      self._pitch = pitch
      if self.modulator is not None:
         self.modulator.pitch = pitch

   @property
   def call(self):
      """
         myStation call
      """
      return self._call

   @call.setter
   def call(self,call):
      self._call = call
      if self.me is not None:
         self.me.myCall = call

   @property
   def wpm(self):
      """
         myStation wpm
      """
      return self._wpm

   @wpm.setter
   def wpm(self,wpm):
      self._wpm = wpm
      if self.me is not None:
         self.me.wpm = wpm

   @property
   def cwreverse(self):
      """
         Use LSB shift by -pitch
      """
      return self._cwreverse

   @cwreverse.setter
   def cwreverse(self,cwreverse):
      self._cwreverse = cwreverse
      if self.modulator is not None:
         self.modulator.reverse = (cwreverse == 1)

   def rfgfun(self,a0,a1):
      """
         Function for rf gain fast attack slow decay
      """
      if a0<a1: a1 = a0+self._qskdecayfactor*(a1-a0)
      return a1

   def getAudio(self,outdata,nf,tinfo,status):
      """
         Callback for sounddevice interface to port audio
      """
      if status:
         print('Port audio error ',status,self.bufcount,file=sys.stderr)
      self.bufcount += 1
      self.checkDuration()
      NOISEAMP = 6000
      r = self._rng.random(2*self._bufsize)
      reim = np.full(self._bufsize,-1.5*NOISEAMP*(1+1j),dtype=np.complex128)
      reim[:] += 3*NOISEAMP*(r[::2]+1j*r[1::2])
      if self.qrn:
         r1 = self._rng.random(self._bufsize)
         r2 = self._rng.random(self._bufsize)
         b = r1<0.01
         reim[b] += 60*NOISEAMP*(r2[b]-0.5)
         if self._rng.random() < 0.01:
            self.stations.append(
               QrnStation(self._rng,bufsize=self._bufsize,rate=self._rate))
      if self.qrm:
         if self._rng.random() < self.qrmProbPerBuffer:
            self.stations.append(QrmStation(self._rng,self._keyer,self._callList
               ,hisCall=self.me.myCall,bufsize=self._bufsize,rate=self._rate))
      ritfac = 2.0*np.pi*self.rit/self._rate
      for s in self.stations:
         if s.state == StationState.DeleteMe:
            if (self.qsy and isinstance(s,DxStation) and
               s.oper.state != Os.Done and s.called):
               self.q.put(s.myCall)
               if not (self.me.app is None):
                  self.me.app.qsy()
            self.stations.remove(s)
         elif s.state == StationState.Sending:
            buf = s.getBuffer()
            bfo = s.getBfo()-self._bufindex*ritfac-self._ritph
            reim[:] += buf*np.exp(-1j*bfo)
      self._ritph += self._bufsize*ritfac % (2.0*np.pi)
      mvol = self.monitor*20000
      if self.qsk:
         if self.me.state == StationState.Sending:
            buf = self.me.getBuffer()
            self._rfg[0] = self._rfg0
            self._rfg[1:] = 1.0-buf
            self._rfg = self._rfgcal.accumulate(self._rfg)
            reim = mvol*buf*(1+1j)+self._rfg[0:self._bufsize]*reim
            self._rfg0 = self._rfg[-1]
         elif self._rfg0 < 0.999:
            self._rfg[0] = self._rfg0
            self._rfg[1:] = 1.0
            self._rfg = self._rfgcal.accumulate(self._rfg)
            reim = self._rfg[0:self._bufsize]*reim
            self._rfg0 = self._rfg[-1]
         else:
            self._rfg0 = 1.0
      elif self.me.state == StationState.Sending:
         buf = self.me.getBuffer()
         reim = mvol*buf*(1+1j)
      reim = self._m3.avg(self._m2.avg(self._m1.avg(reim)))
      reim *= self._fgain
      audio = self.modulator.modulate(reim)
      audio = self._m5.process(audio)
      outdata[:,0] = audio
      self.me.tick()
      for s in self.stations:
         s.tick()
      for s in self.stations:
         if isinstance(s,DxStation):
            if (s.oper.state == Os.Done):
               self.q.put(s.dataToLastQso())
               if not (self.me.app is None):
                  self.me.app.lastQso()
#               (trueCall, trueRst, trueNr) = s.dataToLastQso()
#               print("contest Correct Info ",trueCall,trueRst,trueNr)
      if self.mode == RunMode.single:
         if self.dxCount() == 0:
            s = DxStation(self._rng,self._keyer,self._callList,self.me,
               self._bufsize*self.bufcount/(60.0*self._rate),
               lids=self.lids,lidNrProb=self.lidNrProb,
               lidRstProb=self.lidRstProb,qsb=self.qsb,
               flutterProb=self.flutterProb,
               rptProb=self.rptProb,fast=self.fast,slow=self.slow,
               isSingle=True,bufsize=self._bufsize,rate=self._rate)
            self.stations.append(s)
            s.processEvent(StationEvent.MeFinished)
         
#      np.savetxt(self.ef,audio)
#      self.wf.writeframesraw((audio*30000).astype(np.int16))

   def dxCount(self):
      """
         Returns
           Number of dx stations in station list
      """
      count = 0
      for s in self.stations:
         if isinstance(s,DxStation):
            if s.oper.state != Os.Done:
               count += 1
      return count

   def onMeStartedSending(self):
      """
         Inform all stations that we have started sending
      """
      for s in self.stations:
         s.processEvent(StationEvent.MeStarted)

   def onMeFinishedSending(self):
      """
         Inform all stations that we finished sending
         Add new calling station with Poisson probability if not single call
      """
      if self.mode != RunMode.single:
         if (StationMessage.CQ in self.me.msgs or
            (# fixme QsoList not none and
             StationMessage.TU in self.me.msgs 
             and StationMessage.MyCall in self.me.msgs)):
            newst = self._rng.poisson(0.5*self.activity)
            for i in range(newst):
               self.stations.append(
                  DxStation(self._rng,self._keyer,self._callList,self.me,
                  self._bufsize*self.bufcount/(60.0*self._rate),
                  lids=self.lids,lidNrProb=self.lidNrProb,
                  lidRstProb=self.lidRstProb,qsb=self.qsb,
                  flutterProb=self.flutterProb,
                  rptProb=self.rptProb,fast=self.fast,slow=self.slow,
                  isSingle=False,bufsize=self._bufsize,rate=self._rate))
      for s in self.stations:
         s.processEvent(StationEvent.MeFinished)

   def start(self):
      self.bufcount = 0
      self.stream = sd.OutputStream(samplerate=self._rate
         ,blocksize=self._bufsize,channels=1,dtype=np.float32,latency=0.1
         ,callback=self.getAudio)
      self.stream.start()

   def stop(self):
      for s in self.stations:
         self.stations.remove(s)
      self.stream.stop()
      self.stream.close()

   def time(self):
      s = int(self.bufcount*self._bufsize/self._rate)
      m, s = divmod(s,60)
      h, m = divmod(m,60)
      return (h,m,s)

   def checkDuration(self):
      if self.duration < self.bufcount*self._bufsize/(self._rate*60):
         self.me.app.contestEnded()

   def readConfig(self,filename):
      if os.path.exists(filename):
         configFile = filename
      else:
         myDir = os.path.dirname(__file__)
         configFile = os.path.join(myDir,filename)
         if not os.path.exists(configFile):
            raise FileNotFoundError(errno.ENOENT,
               os.strerror(errno.ENOENT),filename)
      p = configparser.ConfigParser(delimiters='=',comment_prefixes='#')
      p.read(configFile)
      appearancedict = dict(p['Appearance'])
      self.fontsize = int(appearancedict['fontsize'])
      sounddict = dict(p['Sound'])
      self._rate = int(sounddict['rate'])
      self._bufsize = int(sounddict['bufsize'])
      stationdict = dict(p['Station'])
      self.call = stationdict['call'].upper()
      self.wpm = int(stationdict['wpm'])
      self.fast = float(stationdict['fast'])
      self.slow = float(stationdict['slow'])
      self.bandwidth = int(stationdict['bandwidth'])
      self.pitch = int(stationdict['pitch'])
      self.cwreverse = int(stationdict['cwreverse'])
      self.qsk = int(stationdict['qsk'])
      self.qskdecaytime = float(stationdict['qskdecaytime'])
      self.rit = int(stationdict['rit'])
      self.monitor = float(stationdict['monitor'])
      conditionsdict = dict(p['Conditions'])
      self.qrn = int(conditionsdict['qrn'])
      self.qrm = int(conditionsdict['qrm'])
      self.qsy = int(conditionsdict['qsy'])
      self.tqrm = int(conditionsdict['tqrm'])
      self.qsb = int(conditionsdict['qsb'])
      self.flutter = int(conditionsdict['flutter'])
      self.flutterProb = float(conditionsdict['flutterprob'])
      self.lids = int(conditionsdict['lids'])
      self.activity = int(conditionsdict['activity'])
      self.lidRstProb = float(conditionsdict['lidrstprob'])
      self.lidNrProb = float(conditionsdict['lidnrprob'])
      self.rptProb = float(conditionsdict['rptprob'])
      contestdict = dict(p['Contest'])
      self.duration = int(contestdict['duration'])
      self.mode = eval(contestdict['mode'])
      self.savewave = int(contestdict['savewave'])

   def writeConfig(self,filename):
      with open(filename,'w') as f:
         p = configparser.ConfigParser(delimiters='=',comment_prefixes='#')
         p.add_section('Appearance')
         for i in ['fontsize']:
            p.set('Appearance',i,str(eval('self.'+i)))
         p.add_section('Sound')
         for i in ['rate', 'bufsize']:
            p.set('Sound',i,str(eval('self._'+i)))
         p.add_section('Station')
         for i in ['call','wpm','fast','slow','bandwidth','pitch','qsk'
            ,'qskdecaytime', 'cwreverse', 'rit', 'monitor']:
            p.set('Station',i,str(eval('self.'+i)))
         p.add_section('Conditions')
         for i in ['qrn','qrm','tqrm','qsb','flutter','qsy','lids','activity'
            ,'lidRstProb','lidNrProb','rptProb','flutterProb']:
            p.set('Conditions',i,str(eval('self.'+i)))
         p.add_section('Contest')
         for i in ['duration','mode','savewave']:
            p.set('Contest',i,str(eval('self.'+i)))
         p.write(f)
