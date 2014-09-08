#!/usr/bin/env python
#
# Copyright (C) 2012 Philip Belemezov <philip@belemezov.net>
#
# Public domain
#


import struct
import optparse
import sys
import os

class DataRecognizer(object):
    header = 'start'
    footer = 'end'

    @classmethod
    def isDataStart(cls, buf, pos):
        raise NotImplemented

    @classmethod
    def findNextDataStart(cls, buf, pos):
        raise NotImplemented

    @classmethod
    def findDataSize(cls, buf, pos):
        raise NotImplemented

    @classmethod
    def findDataRange(cls, buf, pos):
        raise NotImplemented

    @classmethod
    def findNextDataRange(cls, buf, pos):
        raise NotImplemented



class ICNSRecognizer(DataRecognizer):
    header = 'icns'
    footer = 'IEND\xae\x42\x60\x82'

    @classmethod
    def isDataStart(cls, buf, pos):
        return buf.startswith(cls.header, pos)


    @classmethod
    def findNextDataStart(cls, buf, pos):
        while pos < len(buf):
            if cls.isDataStart(buf, pos):
                return pos
            pos += 1
        return None


    @classmethod
    def findDataSize(cls, buf, pos):
        origin = pos
        assert cls.isDataStart(buf, origin)
        pos += len(cls.header)
        size = struct.unpack('>I', buf[pos:pos+4])[0]
        assert origin + size < len(buf)
        assert buf[origin + size - len(cls.footer):origin + size] == cls.footer
        return size


    @classmethod
    def findDataRange(cls, buf, pos):
        size = cls.findDataSize(buf, pos)
        return (pos, size)


    @classmethod
    def findNextDataRange(cls, buf, pos):
        origin = cls.findNextDataStart(buf, pos)
        if origin is None:
            return None
        return cls.findDataRange(buf, origin)


def writeBuffer(filename, buf):
    with open(filename, 'wb') as f:
        f.write(buf)


# def bufferToHex(buffer):
#     return ''.join('%02x ' % ord(b) for b in buffer)


def extractData(buf):
    origin = 0
    pos = 0
    results = []
    while pos < len(buf):
        r = ICNSRecognizer.findNextDataRange(buf, origin)
        if r is None:
            break
        (pos, size) = r
        results.append(('UNKNOWN', buf[origin:pos]))
        results.append(('ICNS', buf[pos:pos+size]))
        origin = pos + size
    if origin < len(buf):
        results.append(('UNKNOWN', buf[origin:len(buf)]))
    return results


def writeAllData(items, outputDir):
    total = len(items)
    maxDigits = len(str(total))
    filenameFormat = '{index:#0%d}-{type}.{ext}' % maxDigits

    exts = {
        'UNKNOWN': 'dat',
        'ICNS': 'icns',
    }

    for index, (type, data) in enumerate(items):
        filename = outputDir + '/' + filenameFormat.format(
            index=index,
            type=type,
            ext=exts[type],
        )

        print('Writing %s ...' % filename)
        writeBuffer(filename, data)


def parseArgs():
    prog = os.path.basename(sys.argv[0])

    DEFAULT_DATFILE = (
        "/System/Library"
        "/Keyboard Layouts/AppleKeyboardLayouts.bundle"
        "/Contents/Resources"
        "/AppleKeyboardLayouts-L.dat"
    )

    parser = optparse.OptionParser(
        usage="Usage: %prog [options] DATFILE"
    )
    parser.add_option(
        "-o", "--output",
        dest="output",
        help="Output directory",
        metavar="OUTPUT"
    )

    (opts, args) = parser.parse_args()
    if not opts.output:
        parser.error("Please specify output dir using `-o'")

    opts.filename = args[0] if args else DEFAULT_DATFILE

    return opts


def checkArgs(opts):
    if not os.path.exists(opts.output):
        print "Output directory %s doesn't exist, please create it first" \
                % outputDir
        return 1


def main():
    opts = parseArgs()
    error = checkArgs(opts)
    if error:
        return error

    print "Reading %s" % opts.filename
    data = None
    with open(opts.filename, "rb") as f:
        data = f.read()

    items = extractData(data)
    if not items:
        return 1

    writeAllData(items, opts.output)
    return 0
    # return processIcons(data, outputDir=opts.output)


if __name__ == "__main__":
    sys.exit(main())
