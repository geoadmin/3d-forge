# -*- coding: utf-8 -*-


def numberToZigZag(n):
    """
    ZigZag-Encodes a number:
       -1 = 1
       -2 = 3
        0 = 0
        1 = 2
        2 = 4
    """
    return (n << 1) ^ (n >> 31)


def zigZagToNumber(z):
    """ Reverses ZigZag encoding """
    return (z >> 1) ^ (-(z & 1))
    #return (z >> 1) if not z & 1 else -(z+1 >> 1)
