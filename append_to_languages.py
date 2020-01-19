# -*- coding: utf-8 -*-
"""

    Copyright (C) 2018-2020 anxdpanic

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

"""

'''
    Does basic error checking and adds new strings to Kodi add-on language files

    Error checking tries to find:
        - missing, unescaped, or too many "
        - msgctxt missing #
        - duplicate string ids
        - out of bounds strings ids (30000-32999)  # this error will block addition of new strings
        - out of sync last string ids  # this error will block addition of new strings

    Usage:
        Place in add-ons resources/language directory
        Run this script to check .po files for errors, this will also create new_strings.txt in the resources/language directory
        Place the strings you wish to add in new_strings.txt, 1 string per line
        eg:
        --- new_strings.txt ---
        Videos
        Highlights
        Live streams
        --- end new_strings.txt ---
        Run this script again to add those strings
'''

import os
import re


def hline():
    return '=' * 50


def get_new_strings():
    with open('new_strings.txt', 'a') as f:
        f.close()  # touch

    with open('new_strings.txt', 'rb') as f:
        new_lines = [line.rstrip() for line in f if line.rstrip() != '']

    return new_lines


def get_po_files():
    _po_files = list()
    for dirpath, dirnames, filenames in list(os.walk(".")):
        for filename in [f for f in filenames if f.endswith(".po")]:
            _po_files.append(os.path.join(dirpath, filename))
    return _po_files


def get_last_msgctxt_id(_po_files):
    last_string_id = 29999

    for pf in _po_files:
        string_ids = list()

        with open(pf, 'rb') as f:
            contents = f.readlines()
            for i, line in enumerate(contents):
                line = line.decode('utf-8')
                match = re.search('msgctxt "#(?P<string_id>[0-9]+)"', line.strip())
                if match:
                    string_id = match.group('string_id')
                    string_id = int(string_id)
                    if string_id not in string_ids:
                        string_ids.append(string_id)
                        if string_id > last_string_id:
                            last_string_id = string_id

    return last_string_id


def check_for_errors(_po_files, last_string_id):
    blocking_error = False
    _errors = list()
    lower_limit = 30000
    upper_limit = 32999

    for pf in _po_files:
        string_ids = list()
        file_last_string_id = 29999
        first_msgctxt = -1

        with open(pf, 'rb') as f:
            print('Checking |%s| for errors...' % pf)
            contents = f.readlines()
            for i, line in enumerate(contents):
                line_number = str(i + 1)
                line = line.decode('utf-8')
                if line.startswith('#') and ' ' in line:
                    pass
                elif line.startswith('msgctxt "'):
                    if first_msgctxt == -1:
                        first_msgctxt = i
                    if not line.startswith('msgctxt "#'):
                        _errors.append('%s: Missing # in msgctxt |line: %s|' % (pf, line_number))
                    elif not line.rstrip().endswith('"'):
                        _errors.append('%s: Missing " in msgctxt |line: %s|' % (pf, line_number))
                    elif line.count('"') > 2:
                        _errors.append('%s: Too many "\'s in msgctxt |line: %s|' %
                                       (pf, line_number))

                    match = re.search('msgctxt "#(?P<string_id>[0-9]+)"', line.strip())
                    if match:
                        string_id = match.group('string_id')
                        string_id = int(string_id)
                        if string_id > upper_limit or string_id < lower_limit:
                            _errors.append('%s: String id out of bounds |%s| '
                                           '|bounds: 30000-32999| |line: %s|' %
                                           (pf, str(string_id), line_number))
                            blocking_error = True
                        if string_id not in string_ids:
                            string_ids.append(string_id)
                            if string_id > file_last_string_id:
                                file_last_string_id = string_id
                        else:
                            _errors.append('%s: Duplicate string id |%s| |line: %s|' %
                                           (pf, str(string_id), line_number))
                elif line.startswith('msgid "'):
                    if not line.rstrip().endswith('"'):
                        _errors.append('%s: Missing " in msgid |line: %s|' % (pf, line_number))
                    else:
                        if line.strip().count('"') > 2:
                            if line.strip().count('\\"') != (line.strip().count('"') - 2):
                                _errors.append('%s: Unescaped " in msgid |line: %s|' %
                                               (pf, line_number))
                elif line.startswith('msgstr "'):
                    if not line.rstrip().endswith('"'):
                        _errors.append('%s: Missing " in msgstr |line: %s|' %
                                       (pf, line_number))
                    else:
                        if line.strip().count('"') > 2:
                            if line.strip().count('\\"') != (line.strip().count('"') - 2):
                                _errors.append('%s: Unescaped " in msgstr |line: %s|' %
                                               (pf, line_number))
                elif (line.startswith('"') and
                      ((line.count('"') < 2) or not line.rstrip().endswith('"'))):
                    _errors.append('%s: Unrecognized header missing " |line: %s|' %
                                   (pf, line_number))
                elif line.startswith('"'):
                    pass
                elif line.strip():
                    _errors.append('%s: Uncommented text |line: %s|' % (pf, line_number))

            if file_last_string_id != last_string_id:
                _errors.append('%s: File out of sync. Last string id |%s| expected |%s|' %
                               (pf, file_last_string_id, last_string_id))
                blocking_error = True

    return _errors, blocking_error


def add_lines(_po_files, lines_to_add, last_string_id):
    strings_added = False

    for pf in _po_files:

        whitespace = '\n'

        with open(pf, 'rb') as f:
            contents = f.readlines()
            last_msgstr = len(contents)
            for i, line in enumerate(contents):
                line_number = str(i + 1)
                line = line.decode('utf-8')
                if line.startswith('msgstr "'):
                    last_msgstr = int(line_number)

        contents = contents[:last_msgstr]

        match = re.search(r'^.*(?P<whitespace>\s*)$', contents[0].decode('utf-8'))
        if match:
            whitespace = match.group('whitespace')
            whitespace = whitespace.encode('utf-8')

        for i, line in enumerate(lines_to_add):
            print('%s: Adding |%s| with string id: |%s|' %
                  (pf, line.decode('utf-8'), str(last_string_id + (i + 1))))
            if i == 0:
                contents.append(whitespace)
            contents.append(b'msgctxt "#%s"%s' %
                            (str(last_string_id + (i + 1)).encode('utf-8'), whitespace))
            contents.append(b'msgid "%s"%s' % (line, whitespace))
            contents.append(b'msgstr ""%s' % whitespace)
            if (i + 1) != len(lines_to_add):
                contents.append(whitespace)

        if lines_to_add:
            strings_added = True
            with open(pf, 'wb') as f:
                print('Writing ' + pf)
                f.writelines(contents)

    return strings_added


def remove_new_strings():
    with open('new_strings.txt', 'w') as f:
        f.close()


if __name__ == "__main__":

    new_strings = get_new_strings()
    po_files = get_po_files()

    print(hline())

    if len(new_strings) > 0:
        print('Found strings to add:')
        print('')
    else:
        print('No strings found to add.')

    for l in new_strings:
        print('\t' + str(l))

    print('')
    print(hline())

    written_to_file = False

    print('Finding last string id:')
    print('')

    last_msgctxt_id = get_last_msgctxt_id(po_files)

    print('\tFound: |%s|' % str(last_msgctxt_id))
    print('')
    print(hline())

    errors, write_blocked = check_for_errors(po_files, last_msgctxt_id)

    if new_strings:
        if not write_blocked:
            written_to_file = add_lines(po_files, new_strings, last_msgctxt_id)
        elif write_blocked and new_strings:
            print('Write deferred. Correct any errors and try again.')

    if written_to_file:
        print('')
        print(hline())
        print('Strings were added, removing from new_strings.txt')
        remove_new_strings()

    print('')
    print(hline())
    if len(errors) > 0:
        print('Errors:')
        print('')
    else:
        print('No errors found.')

    for error in errors:
        print(error)

    print('')
    print(hline())
