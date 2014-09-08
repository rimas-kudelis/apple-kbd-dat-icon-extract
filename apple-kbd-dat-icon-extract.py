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
    name = None


    recognizers = []


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
    name = 'ICNS'

    @classmethod
    def isDataStart(cls, buf, pos):
        return buf.startswith(cls.header, pos)


    @classmethod
    def findNextDataStart(cls, buf, pos):
        if pos >= len(buf):
            return None
        pos = buf.find(cls.header, pos)
        return pos if pos != -1 else None


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


class LanguageRecognizer(DataRecognizer):
    header = None
    footer = None
    name = 'LANG'

    @classmethod
    def isDataStart(cls, buf, pos):
        return buf[pos].isalpha()


    @classmethod
    def findNextDataStart(cls, buf, pos):
        if pos >= len(buf):
            return None
        while buf[pos] == '\x00':
            pos += 1
            if pos >= len(buf):
                return None
        if not buf[pos].isalpha():
            return None
        return pos


    @classmethod
    def readCString(cls, buf, pos):
        origin = pos
        pos = buf.find('\x00', origin)
        if pos == -1:
            return None
        return buf[origin:pos]

    @classmethod
    def readData(cls, buf, pos):
        origin = pos
        assert cls.isDataStart(buf, origin)
        name = cls.readCString(buf, origin)
        if name is None:
            return None
        pos += len(name) + 1
        if pos >= len(buf):
            return None
        pos = cls.findNextDataStart(buf, pos)
        if pos is None:
            return None
        code = cls.readCString(buf, pos)
        if code is not None:
            pos += len(code) + 1
        if pos >= len(buf):
            return None
        result = {
            'origin': origin,
            'size': pos - origin,
            'name': name,
            'code': code,
        }
        print(result)
        return result


    @classmethod
    def findDataSize(cls, buf, pos):
        assert cls.isDataStart(buf, pos)
        origin = pos
        pos = buf.find('\x00', pos)
        if pos == -1:
            return None
        pos = cls.findNextDataStart(buf, pos)
        if pos is None:
            return None
        pos = buf.find('\x00', pos)
        if pos == -1:
            return None
        pos += 1
        if pos >= len(buf):
            return None
        return pos - origin


    @classmethod
    def findDataRange(cls, buf, pos):
        origin = pos
        size = cls.findDataSize(buf, pos)
        if size is None:
            return None
        return (origin, size)


    @classmethod
    def findNextDataRange(cls, buf, pos):
        pos = cls.findNextDataStart(buf, pos)
        if pos is None:
            return None
        r = cls.findDataRange(buf, pos)
        if r is None:
            return None
        return r


    @classmethod
    def readNextData(cls, buf, pos):
        pos = cls.findNextDataStart(buf, pos)
        if pos is None:
            return None
        return cls.readData(buf, pos)


def writeBuffer(filename, buf):
    with open(filename, 'wb') as f:
        f.write(buf)


# def bufferToHex(buffer):
#     return ''.join('%02x ' % ord(b) for b in buffer)


def extractData(buf):
    origin = 0
    pos = 0
    results = []
    while True:
        r = ICNSRecognizer.findNextDataRange(buf, origin)
        if r is None:
            break
        (pos, size) = r
        results.append(('UNKNOWN', buf[origin:pos]))
        results.append(('ICNS', buf[pos:pos+size]))
        origin = pos + size
    if origin < len(buf):
        results.append(('UNKNOWN', buf[origin:len(buf)]))

    # try to get labels for the parts
    temp = results
    results = []
    for i, (type, data) in enumerate(temp):
        if type == 'ICNS':
            results.append((type, data))
            continue

        # elif type == 'UNKNOWN':
        r = LanguageRecognizer.findNextDataRange(data, 0)
        print str(i) + ':' + repr(r)
        if r is None:
            results.append(('UNKNOWN', data))
            continue
        if r[0] != 0 and not all(b == '\x00' for b in data[0:r[0]]):
            results.append(('UNKNOWN', data[0:r[0]]))
        end = sum(r)
        results.append(('LANG', data[r[0]:end]))
        if end < len(data):
            results.append(('UNKNOWN', data[end:]))

    return results


def writeAllData(items, outputDir):
    total = len(items)
    maxDigits = len(str(total))
    filenameFormat = '{index:#0%d}-{type}.{ext}' % maxDigits

    exts = {
        'UNKNOWN': 'dat',
        'LANG': 'txt',
        'ICNS': 'icns',
    }

    name = None
    code = None
    for index, (type, data) in enumerate(items):
        if type == 'LANG':
            labelData = LanguageRecognizer.readNextData(data, 0)
            if labelData:
                name = labelData['name']
                code = labelData['code']
            else:
                name = None
                code = None

        filename = outputDir + '/' + filenameFormat.format(
            index=index,
            type=type if type == 'UNKNOWN' or not name else name + ' (' + code + ')' or type,
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
