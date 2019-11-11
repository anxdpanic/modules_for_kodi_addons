# -*- coding: utf-8 -*-

"""
This is an:
- addons.xml generator
- addons.xml.md5 generator
- optional auto-compressor (including handling of icons, fanart and changelog)

Python 2.7 -> 3.7

Compression of addons in repositories has many benefits, including:
 - Protects addon downloads from corruption.
 - Smaller addon file size resulting in faster downloads and
   less space / bandwidth used on the repository.
 - Ability to 'roll back' addon updates in XBMC to previous versions.

To enable the auto-compressor, set the compress_addons setting to True
If you do this you must make sure the 'datadir zip' parameter in the addon.xml
of your repository file is set to 'true'.

Please bump __revision__ one decimal point and add your name to __credits__ when making changes
"""

import json
import os
import shutil
import sys
import hashlib
import zipfile
import re

__script__ = '.repo_prep.py'
__revision__ = 5.1
__homepage__ = 'https://forum.kodi.tv/showthread.php?tid=129401'
__credits__ = 'Unobtanium, anxdpanic'
__license__ = 'GPL-3.0-only'


class Generator:
    """
        Generates a new addons.xml file from each addons addon.xml file
        and a new addons.xml.md5 hash file. Must be run from the root of
        the checked-out repo. Only handles single depth folder structure.
    """

    def __init__(self):

        # paths
        self.addons_xml = os.path.join(REPOSITORY_PATH, 'addons.xml')
        self.addons_xml_md5 = os.path.join(REPOSITORY_PATH, 'addons.xml.md5')

        # call master function
        self.generate_addons_files()

    def generate_addons_files(self):
        """
        Generate addons.xml and addons.xml.md5
        """
        # addon list
        addons = os.listdir(SOURCE_PATH)
        # final addons text
        addons_xml = u'<?xml version=\'1.0\' encoding=\'UTF-8\' standalone=\'yes\'?>\n<addons>\n'

        found_an_addon = False
        path = ''

        # loop through and add each addons addon.xml file
        for addon in addons:
            if addon in IGNORED_ADDONS:
                continue
            try:
                # skip any file or .svn folder
                if is_addon_dir(addon):

                    # create path
                    path = os.path.join(addon, 'addon.xml')

                    if os.path.exists(path):
                        found_an_addon = True

                    # split lines for stripping
                    xml_lines = read_file(path)
                    xml_lines = xml_lines.splitlines()

                    # new addon
                    addon_xml = ''

                    # loop through cleaning each line
                    for line in xml_lines:
                        if isinstance(line, bytes):
                            line.decode('utf-8')
                        # skip encoding format line
                        if line.find('<?xml') >= 0:
                            continue
                        # add line
                        addon_xml += line.rstrip() + '\n'

                    # we succeeded so add to our final addons.xml text
                    addons_xml += addon_xml.rstrip() + '\n\n'

            except Exception as error:  # pylint: disable=broad-except
                # missing or poorly formatted addon.xml
                print('Excluding %s for %s' % (path, error))

        # clean and add closing tag
        addons_xml = addons_xml.strip() + u'\n</addons>\n'

        # only generate files if we found an addon.xml
        if found_an_addon:
            # save files
            self._save_file(self.addons_xml, addons_xml.encode('UTF-8'))
            self.generate_md5_file()

            # notify user
            print(' ')
            print('Updated addons xml and addons.xml.md5 files')
        else:
            print('Could not find any addons, so script has done nothing.')

    def generate_md5_file(self):
        """
        Create addons.xml.md5
        """
        try:
            # create a new md5 hash
            contents = read_file(self.addons_xml)
            md5 = hashlib.md5(contents.encode('utf-8')).hexdigest()
            # save file
            self._save_file(self.addons_xml_md5, md5)

        except Exception as error:  # pylint: disable=broad-except
            # oops
            print('An error occurred creating addons.xml.md5 file!\n%s' % error)

    @staticmethod
    def _save_file(filename_and_path, contents):
        if isinstance(contents, bytes):
            contents = contents.decode('utf-8')
        try:
            if sys.version_info[0] >= 3:
                with open(filename_and_path, 'w', encoding='utf-8') as open_file:
                    open_file.write(contents)
            else:
                with open(filename_and_path, 'w') as open_file:
                    open_file.write(contents.encode('utf-8'))
        except Exception as error:  # pylint: disable=broad-except
            # oops
            print('An error occurred saving %s file!\n%s' % (filename_and_path, error))


class Compressor:
    """
    Create compressed addon releases
    """
    def __init__(self):
        # variables used later on
        self.addon_name = None
        self.addon_path = None
        self.addon_folder_contents = None
        self.addon_xml = None
        self.addon_version_number = None
        self.addon_zip_path = None
        self.addon_path_zips = None

        # run the master method of the class, when class is initialised.
        # only do so if we want addons compressed.
        if COMPRESS_ADDONS:
            self.compress_addons()

    def compress_addons(self):
        """
        Compress all addons found in SOURCE_PATH
        """
        source_directory = os.listdir(SOURCE_PATH)
        for addon in source_directory:
            if addon in IGNORED_ADDONS:
                continue
            # set variables
            self.addon_name = str(addon)
            self.addon_path = os.path.join(SOURCE_PATH, addon)
            self.addon_path_zips = os.path.join(ZIPS_PATH, addon)
            # skip any file or .svn folder.
            if is_addon_dir(self.addon_path):

                # set another variable
                self.addon_folder_contents = os.listdir(self.addon_path)

                # check if addon has a current zipped release in it.
                addon_zip_exists = self._get_zipped_addon_path()

                # checking for addon.xml and try reading it.
                addon_xml_exists = self._read_addon_xml()
                if addon_xml_exists:
                    # now addon.xml has been read, scrape version number from it.
                    # we need this when naming the zip (and if it exists the changelog)
                    self._read_version_number()

                    if not addon_zip_exists:
                        addon_zip_exists = self._get_zipped_addon_path()
                        if not addon_zip_exists:
                            print('Create compressed %s%s release for [%s] v%s' % \
                                  ('unofficial ' if self._is_unofficial() else '',
                                   self._get_release_type(), self.addon_name,
                                   self.addon_version_number))
                            self.create_compressed_addon_release()

    def _get_zipped_addon_path(self):
        # get name of addon zip file. returns False if not found.
        addon_xml_exists = self._read_addon_xml()
        if addon_xml_exists:
            self._read_version_number()

        if TAG_UNOFFICIAL_RELEASES and self._is_unofficial():
            zip_name = self.addon_name + '-unofficial-' + self.addon_version_number + '.zip'
        else:
            zip_name = self.addon_name + '-' + self.addon_version_number + '.zip'

        if not os.path.exists(self.addon_path_zips):
            if not self.addon_path_zips.endswith('zips'):
                make_path = self.addon_path_zips
                os.makedirs(make_path)

        folder_contents = os.listdir(self.addon_path_zips)

        for potential_zip in folder_contents:
            if zip_name == potential_zip:
                self.addon_zip_path = os.path.join(self.addon_path_zips, zip_name)
                return True
        # if loop is not broken by returning the addon path, zip was not found so return False
        self.addon_zip_path = None
        return False

    def _extract_addon_xml_to_release_folder(self):
        with zipfile.ZipFile(self.addon_path_zips, 'r') as zip_file:
            for filename in zip_file.namelist():
                if filename.find('addon.xml'):
                    zip_file.extract(filename, self.addon_path_zips)
                    break

    @staticmethod
    def recursive_zipper(directory, zip_file):
        """
        Create a zip_file of the provided addon directory
        """
        with zipfile.ZipFile(zip_file, 'w', compression=zipfile.ZIP_DEFLATED) as zipped_file:
            # get length of characters of what we will use as the root path
            root_len = len(os.path.dirname(os.path.abspath(directory)))

            # recursive writer
            for root, _, files in os.walk(directory):
                # subtract the source file's root from the archive root -
                # ie. make /Users/me/desktop/zip_me.txt into just /zip_me.txt
                archive_root = os.path.abspath(root)[root_len:]

                for repo_file in files:

                    if repo_file.endswith(IGNORED_FILES_END):
                        continue
                    if repo_file.startswith(IGNORED_FILES_START):
                        continue
                    if any(match for match in IGNORED_FILES if repo_file == match):
                        continue

                    full_path = os.path.join(root, repo_file)
                    if any(bl in full_path for bl in IGNORED_DIRECTORIES):
                        continue

                    archive_name = os.path.join(archive_root, repo_file)
                    zipped_file.write(full_path, archive_name, zipfile.ZIP_DEFLATED)

    def create_compressed_addon_release(self):
        """
        Create a zip of the addon into repo root directory, tagging it with '-x.x.x'
        release number scraped from addon.xml. Also updates uncompressed info:
        addon.xml, changelog-x.x.x.txt, and screenshots
        """
        if TAG_UNOFFICIAL_RELEASES and self._is_unofficial():
            zip_name = self.addon_name + '-unofficial-' + self.addon_version_number + '.zip'
        else:
            zip_name = self.addon_name + '-' + self.addon_version_number + '.zip'
        zip_path = os.path.join(ZIPS_PATH, zip_name)

        # zip full directories
        self.recursive_zipper(self.addon_path, zip_path)

        # now move the zip into the addon folder,
        # which we will now treat as the 'addon release directory'

        os.rename(zip_path, os.path.join(self.addon_path_zips, zip_name))

        try:
            shutil.copyfile(os.path.join(self.addon_path, 'addon.xml'),
                            os.path.join(self.addon_path_zips, 'addon.xml'))
        except (shutil.Error, IOError) as _:
            pass

        try:
            shutil.copyfile(os.path.join(self.addon_path, 'icon.png'),
                            os.path.join(self.addon_path_zips, 'icon.png'))
        except (shutil.Error, IOError) as _:
            pass

        try:
            shutil.copyfile(os.path.join(self.addon_path, 'fanart.jpg'),
                            os.path.join(self.addon_path_zips, 'fanart.jpg'))
        except (shutil.Error, IOError) as _:
            pass

        changelog = 'changelog-' + self.addon_version_number + '.txt'
        try:
            shutil.copyfile(os.path.join(self.addon_path, 'changelog.txt'),
                            os.path.join(self.addon_path_zips, changelog))
        except (shutil.Error, IOError) as _:
            pass

        screenshots = self._get_screenshots()
        for screenshot in screenshots:
            screenshot_path = os.path.join(self.addon_path_zips, screenshot)
            try:
                try:
                    os.makedirs(os.path.dirname(screenshot_path))
                except(IOError, OSError) as _:
                    pass
                shutil.copyfile(os.path.join(self.addon_path, screenshot), screenshot_path)
            except (shutil.Error, IOError) as _:
                pass

    def _read_addon_xml(self):
        # check for addon.xml and try and read it.
        addon_xml_path = os.path.join(self.addon_path, 'addon.xml')
        if os.path.exists(addon_xml_path):
            # load whole text into string
            self.addon_xml = read_file(addon_xml_path)
            # return True if we found and read the addon.xml
            return True
        # return False if we couldn't  find the addon.xml
        return False

    def _read_version_number(self):
        # find the header of the addon.
        headers = re.compile(r'<addon\s+id=(.+?)>', re.DOTALL).findall(self.addon_xml)
        for header in headers:
            # if this is the header for the addon, proceed
            if self.addon_name in header:
                # clean line of quotation characters so that it is easier to read.
                header = re.sub('\'', '', header)
                header = re.sub('"', '', header)
                # scrape the version number from the line
                version_tag_regex = re.compile(r'\s*version=(.+?)(?:\s+|$)', re.DOTALL)
                self.addon_version_number = version_tag_regex.findall(header)[0].strip()

    def _get_release_type(self):

        if not self.addon_version_number:
            self._read_version_number()

        if 'alpha' in self.addon_version_number:
            tag = 'alpha'
        elif 'beta' in self.addon_version_number:
            tag = 'beta'
        else:
            tag = 'stable'

        return tag

    def _get_screenshots(self):
        screenshot_tag_regex = re.compile(r'<screenshot>(.+?)</screenshot>', re.DOTALL)
        return screenshot_tag_regex.findall(self.addon_xml)

    def _is_unofficial(self):
        return re.search(r'\s*<!--\s*unofficial\s*-->\s*', self.addon_xml)


def is_addon_dir(addon):
    """
    This function is used by both classes.
    Very very simple and weak check that it is an addon dir.
    Intended to be fast, not totally accurate.
    Skip any file or .svn folder
    """
    if not os.path.isdir(addon) or addon == '.svn' or addon.endswith('zips') or addon == 'zips':
        return False

    return True


def read_file(filename, is_json=False):
    """
    python 2/3 read file
    """
    if sys.version_info[0] >= 3:
        if is_json:
            with open(filename, 'r', encoding='utf-8') as open_file:
                return json.load(open_file)
        else:
            with open(filename, 'r', encoding='utf-8') as open_file:
                return open_file.read()
    else:
        if is_json:
            with open(filename, 'r') as open_file:
                return json.load(open_file)
        else:
            with open(filename, 'r') as open_file:
                return open_file.read().decode('utf-8')


if __name__ == '__main__':
    CONFIG = read_file('.config.json', is_json=True)

    COMPRESS_ADDONS = bool(CONFIG.get('compress_addons'))
    TAG_UNOFFICIAL_RELEASES = bool(CONFIG.get('tag_unofficial_releases'))

    IGNORED_ADDONS = list(set(CONFIG.get('ignored', {}).get('addons', [])))
    IGNORED_FILES = list(set(CONFIG.get('ignored', {}).get('files', [])))
    IGNORED_FILES_START = tuple(set(CONFIG.get('ignored', {}).get('file_starts_with', [])))
    IGNORED_FILES_END = tuple(set(CONFIG.get('ignored', {}).get('file_ends_with', [])))
    IGNORED_DIRECTORIES = list(set(CONFIG.get('ignored', {}).get('directories', [])))

    SOURCE_PATH = CONFIG.get('path', {}).get('source', '')
    REPOSITORY_PATH = CONFIG.get('path', {}).get('repository', '')
    ZIPS_PATH = CONFIG.get('path', {}).get('zips', '')

    if not REPOSITORY_PATH:
        REPOSITORY_PATH = os.getcwd()
    if not SOURCE_PATH:
        SOURCE_PATH = os.getcwd()

    print(__script__)
    print('Version: v' + str(__revision__))
    print('License:  ' + __license__)
    print('Credits:  ' + __credits__)
    print('Homepage: ' + __homepage__)
    print(' ')

    print('Paths:')
    print('    Source:     ' + SOURCE_PATH)
    print('    Repository: ' + REPOSITORY_PATH)
    print('    Zips:       ' + ZIPS_PATH)
    print(' ')

    print('Compress Add-ons:       ' + str(COMPRESS_ADDONS))
    print('Tag Unofficial Add-ons: ' + str(TAG_UNOFFICIAL_RELEASES))
    print(' ')

    Compressor()
    Generator()
