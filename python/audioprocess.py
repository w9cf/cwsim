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

import sys
import numpy as np

class movavg():
   """ Class to perform a moving average over bufsize inputs returning
       bufsiz moving averages.
   """

   def __init__(self,bufsize,navg,dtype=np.float64):
      """
          Arguments:
             bufsize: number of elements to process and return
             navg: number of elements to average; navg < bufsize
          Keyword arguments:
             dtype: The data type (default float64)
      """
      assert (bufsize > navg)
      self._bufsize = bufsize
      self._navg = navg
      self._dt = dtype
      self._sums = np.zeros((2,bufsize),self._dt)
      self._inew = 1

   def avg(self,buf):
      """
         Calculate moving averages.
         Arguments:
            buf = input buffer of length bufsize
         Returns: bufsize moving averages where the last element
            returned is the average of the last navg elements in buf.
      """
      np.cumsum(buf,out=self._sums[self._inew,:])
      avg = np.zeros(self._bufsize,self._dt)
      avg[:self._navg] = (self._sums[self._inew,:self._navg]
            +self._sums[1-self._inew,self._bufsize-1]
            -self._sums[1-self._inew,self._bufsize-self._navg:])
      avg[self._navg:] = (self._sums[self._inew,self._navg:]
         -self._sums[self._inew,:self._bufsize-self._navg])
      self._inew = 1-self._inew
      return avg/self._navg

class modulator():
   """
      Class to shift the frequency of the i/q buffer by pitch.
   """
   def __init__(self,bufsize,rate,pitch,reverse=False):
      """
         Arguments:
            bufsize: number of elements to process and return
            rate: The sampling rate of the audio in samples/second
            pitch: A positive shift frequency. This is changed so that
               bufsize corresponds to an integer number of periods.
            reverse: Shift by -pitch when true (default False)
      """
      self._bufsize = bufsize
      self._rate = rate
      self._reverse = False
      self.pitch = pitch
      self.reverse = reverse

   @property
   def pitch(self):
      """
         The pitch rounded so that bufsize is an integer number of periods.
      """
      return self._pitch

   @pitch.setter
   def pitch(self,pitch):
      self._pitch = pitch
      period = np.rint(self._rate/pitch)
      self._shift = int(self._bufsize % period)
      dphi = 2.0*np.pi/period
      if self.reverse:
         self._ex = -np.exp(1j*dphi*np.arange(self._bufsize-self._shift
            +period))
      else:
         self._ex = -np.exp(-1j*dphi*np.arange(self._bufsize-self._shift
            +period))

   @property
   def reverse(self):
      """
         Use a negative pitch shift
      """
      return self._reverse

   @reverse.setter
   def reverse(self,reverse):
      self._reverse = reverse
      self.pitch = self.pitch

   def modulate(self,buf):
      """
         Arguments:
            buf: The input complex i/q buffer whose frequency is shifted
         Returns:
            Real part of i*exp(-i*w*t)*buf, w = 2*pi*pitch
      """
      assert(self._bufsize == len(buf))
      out = np.imag(self._ex[:self._bufsize]*buf)
      self._ex = np.roll(self._ex,-self._shift)
      return out

class agc():
   """
      Class to apply agc to audio buffer
   """

   def __init__(self,bufsize,maxout=20000,maxoutnorm=0.67,noiseindb=76.0
      ,noiseoutdb=76,attacksamples=155,holdsamples=155):
      """
         Arguments:
            bufsize: number of elements to process and return
         Keyword arguments:
            maxout: maximum output before normalization (default 20000)
            maxoutnorm: maximum output after normalization (default 0.67)
            noiseindb: input noise in dB to map to output noise (default 76)
            noiseoutdb: output noise in dB to map to (default 76)
            attacksamples: samples multiplied by raised cosine (default 155)
            holdsamples: samples multiplied by 1 (default 155)
      """
      self._bufsize = bufsize
      self._maxoutnorm = maxoutnorm
      noisein = 10.0**(0.05*noiseindb)
      noiseout = np.minimum(10.0**(0.05*noiseoutdb),0.25*maxout)
      self._beta = noisein/np.log(maxout/(maxout-noiseout))
      agcmid = attacksamples+holdsamples
      agcbufsize = 2*agcmid+1
      self._agcshape = np.ones(agcbufsize,dtype=np.float32)
      self._agcshape[:attacksamples] = 0.5-0.5*np.cos(
         np.arange(1,attacksamples+1)*np.pi/(attacksamples+1))
      self._agcshape[-attacksamples:] =\
         self._agcshape[attacksamples-1::-1]
      self._magbufsize = agcbufsize+self._bufsize-1
      self._valbufsize = agcmid+self._bufsize
      self._magbuf = np.zeros(self._magbufsize,dtype=np.float32)
      self._valbuf = np.zeros(self._valbufsize,dtype=np.float32)
      self._ind = np.add.outer(
         agcbufsize*np.arange(self._magbufsize-agcbufsize+1),
         (agcbufsize+1)*np.arange(agcbufsize)).astype(np.integer)

   def process(self,buf):
      """
      Apply agc
      Arguments:
         buf: input buffer to apply agc to
      Returns: new buffer with agc applied
      """
      self._valbuf[:self._valbufsize-self._bufsize] = (
         self._valbuf[self._bufsize:])
      self._magbuf[:self._magbufsize-self._bufsize] = (
         self._magbuf[self._bufsize:])
      self._valbuf[self._valbufsize-self._bufsize:] = buf[:].astype(np.float32)
      self._magbuf[self._magbufsize-self._bufsize:] = (
         np.abs(buf[:]).astype(np.float32))
      gain = np.ravel(np.outer(self._magbuf,self._agcshape))[self._ind].max(1)
      gain = np.maximum(gain,1.0e-8)
      gain = self._maxoutnorm*(1.0-np.exp(-gain/self._beta))/gain
      return gain*self._valbuf[:self._bufsize]
