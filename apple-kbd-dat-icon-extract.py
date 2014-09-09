#!/usr/bin/env python
#
# Copyright (C) 2012 Philip Belemezov <philip@belemezov.net>
# Modifications by Chaim-Leib Halbert <chaim.leib.halbert@gmail.com>
#
# Public domain
#
import optparse
import sys
import os

from recognizers import ICNSRecognizer, LanguageRecognizer


def write_buffer(filename, buf):
    with open(filename, 'wb') as f:
        f.write(buf)


def extract_data(buf):
    origin = 0
    results = []
    while True:
        r = ICNSRecognizer.find_next_data_range(buf, origin)
        if r is None:
            break
        (pos, size) = r
        results.append((None, buf[origin:pos]))
        results.append(('ICNS', buf[pos:pos+size]))
        origin = pos + size
    if origin < len(buf):
        results.append((None, buf[origin:len(buf)]))

    # try to get labels for the parts
    temp = results
    results = []
    for i, (kind, data) in enumerate(temp):
        if kind == 'ICNS':
            results.append((kind, data))
            continue

        # elif kind is None:
        r = LanguageRecognizer.find_next_data_range(data, 0)
        if r is None:
            results.append((None, data))
            continue
        if r[0] != 0 and not all(b == '\x00' for b in data[0:r[0]]):
            results.append((None, data[0:r[0]]))
        end = sum(r)
        results.append(('LANG', data[r[0]:end]))
        if end < len(data):
            results.append((None, data[end:]))

    return results


def name_results(results):
    temp = results
    results_count = len(temp)
    max_digits = len(str(results_count))

    exts = {
        None: 'dat',
        'LANG': 'txt',
        'ICNS': 'icns',
    }

    default_fmt = '{i}-{kind}.{ext}'

    results = []
    label = None
    for i, (kind, data) in enumerate(temp):
        istr = str(i).zfill(max_digits)

        filename = None  # gets set later

        if kind == 'LANG':
            label = LanguageRecognizer.read_next_data(data, 0)
            print '{istr} {label}'.format(istr=istr, label=data)
        elif kind == 'ICNS' and label is not None:
            filename = '{i}-{name} ({code}).icns'.format(i=istr, **label)
            label = None

        if filename is None:
            filename = default_fmt.format(
                i=istr,
                kind='UNKNOWN' if kind is None else kind,
                ext=exts[kind]
            )

        results.append((kind, filename, data))
    return results


def write_data(items, output_dir, types=None):
    items = (
        (filename, data)
        for (kind, filename, data) in items
        if kind in types
    ) if types is not None else (
        (filename, data)
        for (kind, filename, data) in items
    )

    for (filename, data) in items:
        filename = output_dir + '/' + filename
        print('Writing %s ...' % filename)
        write_buffer(filename, data)


def parse_args():
    prog = os.path.basename(sys.argv[0])

    layouts_path = (
        "/System/Library"
        "/Keyboard Layouts/AppleKeyboardLayouts.bundle"
        "/Contents/Resources"
        "/AppleKeyboardLayouts-L.dat"
    )

    parser = optparse.OptionParser(
        usage="Usage: %s [options] DATFILE" % prog
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

    opts.filename = args[0] if args else layouts_path

    return opts


def check_args(opts):
    if not os.path.exists(opts.output):
        print "Output directory %s doesn't exist, please create it first" \
            % opts.output
        return 1


def main():
    opts = parse_args()
    error = check_args(opts)
    if error:
        return error

    print "Reading %s" % opts.filename

    with open(opts.filename, "rb") as f:
        data = f.read()
    if not data:
        return 1

    items = extract_data(data)
    if not items:
        return 1

    items = name_results(items)
    if not items:
        return 1

    write_data(items, opts.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
