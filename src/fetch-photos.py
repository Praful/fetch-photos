"""
=============================================================================
File: fetch-photos.py
Description: Copy photos from one folder to another and, in the process,
putting them into folders according to the date the photos were created.
Author: Praful https://github.com/Praful/fetch-photos
Licence: GPL v3
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


def date_taken(filepath):
    try:
        im = Image.open(filepath)
        exif = im.getexif()
        if exif is not None:
            date = exif.get(EXIF_DATATIME)
            if date is not None:
                return (date.split(' ')[0]).replace(":", "-")
    except Exception as ex:
        #  print('No date taken:', ex)
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
    cmdline.add_argument('--from', dest='source', type=str, required=True,
                         help='Folder to copy from')
    cmdline.add_argument('--to', dest='dest', type=str, required=True,
                         help='Folder to copy to')
    cmdline.add_argument('--exclude', dest='exclude', type=str, required=False,
                         help='Exclude paths containing this string')
    cmdline.add_argument('--include', dest='include', type=str, required=False,
                         help='Include paths containing this regex; overrides --exclude')
    cmdline.add_argument('--verbose', action=argparse.BooleanOptionalAction,
                         default=False, help='Provides verbose output')

    return cmdline


def must_include(filepath, regex):
    return re.search(rf'{regex}', filepath) is not None


def get_creation_date(filepath):
    date_taken_exif = date_taken(filepath)

    if date_taken_exif is not None:
        return date_taken_exif
    else:
        creation_timestamp = os.path.getctime(filepath)
        #  date_local = filestamp_to_local_date_str(creation_timestamp)
        return filestamp_to_utc_date_str(creation_timestamp)


def move_files(source_root, dest_root, exclude, include_regex, verbose):
    file_count = files_copied = files_exist = file_errors = files_excluded = 0

    for filepath in glob.iglob(source_root + '**/**', recursive=True):

        if os.path.isfile(filepath):
            file_count += 1

            # TODO accept more than one string to exclude and include

            if exclude is not None and not must_include(filepath, include_regex):
                if exclude in filepath:
                    if verbose:
                        print('Excluding', filepath)
                    files_excluded += 1
                    continue

            creation_date = get_creation_date(filepath)

            _, filename = os.path.split(filepath)

            dest_file = os.path.join(dest_root, creation_date, filename)
            photo_dir = os.path.join(dest_root, creation_date)
            if verbose:
                print(filepath, dest_file)

            if not os.path.exists(dest_file):
                print('Copying', filepath, end=' ')
                if not os.path.exists(photo_dir):
                    os.makedirs(photo_dir)
                res = shutil.copy2(filepath, photo_dir)
                if os.path.exists(dest_file):
                    print('====> done:', res)
                    files_copied += 1
                else:
                    print('====> FAILED:', res)
                    file_errors += 1
            else:
                if verbose:
                    print('====> Skipping: file already exists in destination folder')
                files_exist += 1

    print(
        f'Total files: {file_count}\nCopied: {files_copied}\nSkipped: {files_exist}\nExcluded: {files_excluded}\nErrors: {file_errors}')


def main():
    """
    Processing begins here if script run directly
    """
    args = setup_command_line().parse_args()
    print(args)
    move_files(os.path.expanduser(args.source), os.path.expanduser(
        args.dest), args.exclude, args.include, args.verbose)


if __name__ == '__main__':
    main()
