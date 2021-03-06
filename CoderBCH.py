#!/usr/bin/python
from Polynomial import *
import numpy, copy

class CoderBCH:

    def __init__(self, fieldGenerator, generator, m, t):
        self._generator = generator
        self._m = m
        self._n = 2 ** m - 1;
        self._nk = self._generator.degree()
        self._k = self._n - self._nk
        self._t = t
        self._field = Field(m, fieldGenerator)

    def encode(self, info):
        if not self._isEncodePossible(info):
            raise RuntimeError("Encoding imposible. Check length of message")
        return self._encode(info)

    def decode(self, info):
        return self._decode(info) / self._nk

    def _isEncodePossible(self, info):
        return info.degree() <= self._k

    def _encode(self, info):
        encodedMsg = info*self._nk
        return encodedMsg + (encodedMsg % self._generator)

    def _decode(self, info):
        decodedMsg = info.copy()
        for i in range(self._k):
            syndrome = decodedMsg % self._generator
            if syndrome.hammingWeight() <= self._t:
                print 'DECODE ITERATIONS: ' + str(i)
                decodedMsg = decodedMsg + syndrome
                decodedMsg = decodedMsg << i
                return decodedMsg
            decodedMsg = decodedMsg >> 1
        raise RuntimeError('Unable to correct errors for input message: ' + str(hex(info)))

    def decodeEuclid(self, info):
        info = copy.deepcopy(info)
        syndrome = info % self._generator
        if syndrome.hammingWeight() == 0:
            print 'No transmission error'
            return info

        # assume that generator first minimal poly is m1
        t = self._getPartSyndroms(info , 1)
        print 'Part syndroms computed'

        fi = self._euclidian(t)
        print 'Euclidian algorithm ended'

        errorPos = self._getErrorPositions(fi)
        print 'Error positions: ' + str(errorPos)

        encodedMessage = self._correctErrors(info, errorPos) / self._nk
        encodedMessage.trimPoly()
        return encodedMessage, errorPos

    def _correctErrors(self, message, errorPositions):
        for pos in errorPositions:
            message[pos] = int(not(message[pos]))
        return message

    def _getErrorPositions(self, fi):
        fi = copy.deepcopy(fi)
        result = []

        for i in range(self._n):
            if not Polynomial.getValueUsingAlphaMap(fi , i, self._field):
                result.append(self._field.getReversedPower(i))

        return result

    def _getPartSyndroms(self, info, m0):
        partSyndroms = {}
        polyAlpha = info.getAlphaMap()

        for i in range(2 * self._t):
            alphaPower = i + m0
            value = Polynomial.getValueUsingAlphaMap(polyAlpha, alphaPower, self._field)
            if value is None:
                print 'Syndrom S(alpha^%d) is 0' % alphaPower
            else:
                partSyndroms[i] = value
        return partSyndroms

    def _euclidian(self, T):
        old_r = Polynomial(1) * (2 * self._t)
        old_r = old_r.getAlphaMap()
        r = copy.deepcopy(T)
        old_t = {}
        t = {0 : 0}
        old_s = { 0 : 0}
        s = {}

        while Polynomial.getMapMaxKey(r) >= self._t:
            (result, remainder) = Polynomial.divideUsingAlphaMap(old_r, r, self._field)
            quotient = result

            old_r = r
            r = remainder

            temp = copy.deepcopy(old_s)
            old_s = s
            s = Polynomial.multiplyUsingAlphaMap(s, quotient, self._field)
            s = Polynomial.addUsingAlphaMap(s, temp, self._field)

            temp = copy.deepcopy(old_t)
            old_t = t
            t = Polynomial.multiplyUsingAlphaMap(t, quotient, self._field)
            t = Polynomial.addUsingAlphaMap(t, temp, self._field)

        # print "Bezout coefficients:"
        # print old_s, old_t
        # print "greatest common divisor:"
        # print old_r
        # print "quotients by the gcd:"
        # print t,

        return t

    def __repr__(self):
        return """Coder parameters:
generator:\t%s
m:\t\t%d
n:\t\t%d
k:\t\t%d
n - k:\t\t%d
t:\t\t%d
""" % (int(self._generator), self._m, self._n, self._k, self._nk, self._t)

def randErrorPositions(range, numberOfErrors):
    if range < numberOfErrors:
        raise RuntimeError("Range value cant be bigger then number of errors!")
    positions = list()
    diff = numberOfErrors
    while diff > 0:
        positions += list(numpy.random.randint(range, size=diff))
        positions = list(set(positions))
        diff = numberOfErrors - len(positions)
    return sorted(positions)

def moveRagne(positions, messageLen, errorsDelta):
    temp = list(positions)
    if len(positions) == 1:
        return temp
    diff = temp[-1] - temp[0]
    while diff <= errorsDelta:
        if temp[-1] < (messageLen-1):
            temp[-1] += 1
        if temp[0] > 0:
            temp[0] -= 1
        diff = temp[-1] - temp[0]
    return temp

def addNoise(message, numberOfErrors, errorsDelta, higherDelta=None):
    poly = message.copy()
    positions = randErrorPositions(errorsDelta, numberOfErrors)
    shift = numpy.random.randint(len(message) - errorsDelta)
    for i, pos in enumerate(positions):
        positions[i]  = pos + shift
    if higherDelta is not None:
        positions = moveRagne(positions, len(message), errorsDelta)
    for position in positions:
        poly[position] = int(not(poly[position]))
    return poly, positions

if __name__ == '__main__':
    t = 29
    m = 8
    fieldGen = Polynomial(0435)
    gen = Polynomial(024024710520644321515554172112331163205444250362557643221706035)
    info = Polynomial(0b10101110010100101011110011010101010111100110101110011010111001101011100)
    coder = CoderBCH(fieldGen, gen, m, t)
    print coder
    print 'INFO: ' + str(info)
    encodedMsg = coder.encode(info)
    print 'ENCODED: ' + str(encodedMsg)
    noisedMsg = Polynomial(poly=[0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1])
    print 'NOISED: ' + str(noisedMsg)
    decodedMsg = Polynomial()
    try:
        decodedMsg = coder.decode(noisedMsg)
    except RuntimeError, e:
        print e
    else:
        print 'DECODED: ' + str(decodedMsg)

    if decodedMsg == info:
        print 'INFO and DECODED messages match!'
    else:
        print 'No match at all'
    print '-----------------------------------------------'
    decodedMsgEuclid, correctedPositions = coder.decodeEuclid(noisedMsg)
    print '-----------------------------------------------'
    print 'DECODED EUCLID: ' + str(decodedMsgEuclid)

    if decodedMsgEuclid == info:
        print 'INFO and DECODED messages match!'
    else:
        print 'No match at all'