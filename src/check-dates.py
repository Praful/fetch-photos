"""
=============================================================================
File: check-dates.py
Description: Check which files have exif dates

Author: Praful https://github.com/Praful/fetch-photos
Licence: GPL v3

# py ./check-dates.py --dir /mnt/sd512/data/pictures/phone-s24ultra --exclude '.mp4'
=============================================================================
"""
import glob
import os
import time
import datetime
import shutil
import argparse
import re

# python -m pip install Pillow
from PIL import Image
from PIL.ExifTags import TAGS

# python -m pip install Pillow-heif (this provides support for heic files)
from pillow_heif import register_heif_opener
register_heif_opener()

EXIF_DATATIME = 306
EXIF_DATATIME_ORIGINAL = 36867
EXIF_OFFSET = 34665


def exif_date_original(filepath):
    try:
        im = Image.open(filepath)
        exif = im.getexif()
        ifd_data = exif.get_ifd(EXIF_OFFSET)

        if ifd_data is not None:
            date = ifd_data.get(EXIF_DATATIME_ORIGINAL)
            if date is not None:
                return (date.split(' ')[0]).replace(":", "-")
    except Exception as ex:
        #  print(f'Info: {filepath}: no exif date taken:', ex)
        None

    return None
    #  print('Error getting date taken: ', ex, filepath)


def exif_date(filepath):
    try:
        im = Image.open(filepath)
        exif = im.getexif()
        if exif is not None:
            date = exif.get(EXIF_DATATIME)
            if date is not None:
                return (date.split(' ')[0]).replace(":", "-")
    except Exception as ex:
        #  print(f'Info: {filepath}: no exif date:', ex)
        None

    return None
    #  print('Error getting date taken: ', ex, filepath)


def filestamp_to_local_date_str(d):
    year, month, day, hour, minute, second = time.localtime(d)[
        :-3]
    return "%d-%02d-%02d" % (year, month, day)


def filestamp_to_utc_date_str(d):
    year, month, day, hour, minute, second = time.gmtime(d)[
        :-3]
    return "%d-%02d-%02d" % (year, month, day)


def setup_command_line():
    """
    Define command line switches
    """
    cmdline = argparse.ArgumentParser(
        prog='fetch-photos.py', description='Fetch photos and put them into date folders')

    cmdline.add_argument('--dir', dest='dir', type=str, required=True,
                         help='Folder to check')

    cmdline.add_argument('--exclude', dest='exclude', type=str, required=False,
                         help='Exclude paths containing this string')

    cmdline.add_argument('--include', dest='include', type=str, required=False,
                         help='Include paths containing this regex; overrides --exclude')

    cmdline.add_argument('--verbose', action=argparse.BooleanOptionalAction,
                         default=False, help='Provides verbose output')

    return cmdline


def must_include(filepath, regex):
    return re.search(rf'{regex}', filepath) is not None

def is_photo(filepath):
    return filepath.lower().endswith(('.jpg', '.jpeg', '.png', '.heic'))

def get_creation_date(filepath):
    # eg may be .mp4
    if not is_photo(filepath):
        creation_timestamp = os.path.getctime(filepath)
        return filestamp_to_utc_date_str(creation_timestamp)

    date_original_exif = exif_date_original(filepath)
    if date_original_exif is not None:
        return date_original_exif

    date_exif = exif_date(filepath)
    if date_exif is not None:
        return date_exif
    else:
        # changed 4/4/2025 - don't use file creation date since we should always
        # find exif data
        return None
        #  creation_timestamp = os.path.getctime(filepath)
        #  return filestamp_to_utc_date_str(creation_timestamp)

def move_files(source_root, exclude, include_regex, verbose):
    file_count = files_copied = files_exist = file_errors = files_excluded = 0

    for filepath in glob.iglob(source_root + '**/**', recursive=True):

        if os.path.isfile(filepath):
            file_count += 1

            if exclude is not None and not must_include(filepath, include_regex):
                if exclude in filepath:
                    if verbose:
                        print('Excluding', filepath)
                    files_excluded += 1
                    continue

            creation_date = get_creation_date(filepath)
            if creation_date is None:
                print(f'====> {filepath}: no creation date found')
                files_exist += 1
                continue

    print(
        f'Total files: {file_count}\nCopied: {files_copied}\nSkipped: {files_exist}\nExcluded: {files_excluded}\nErrors: {file_errors}')


def main():
    """
    Processing begins here if script run directly
    """
    args = setup_command_line().parse_args()
    print(args)

    move_files(os.path.expanduser(args.dir),
               args.exclude, args.include, args.verbose)


if __name__ == '__main__':
    main()
