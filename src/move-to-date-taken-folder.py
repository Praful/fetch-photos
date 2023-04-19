"""
=============================================================================
File: move-to-date-taken-folder.py
Description: fetch-photos.py moved photos to a folder named derived from the date
the file was created. This date wasn't alwasy the same as the date the photo was taken.
The program failed when the timezone of the computer it was running on wasn't UTC since
Linux adjusts the file dates according to the timezone.
This patch file corrects that situation by moving photos into the folder that
matches the date the photo was taken.
Author: Praful https://github.com/Praful/fetch-photos
Licence: GPL v3
=============================================================================
"""

import glob
import os
import time
#  import datetime
from datetime import datetime, timezone
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


def test():
    image = Image.open("/mnt/sd512/data/pictures/asia-2023/2023-04-15/DSC07105.JPG")
    image = Image.open(
        "/mnt/sd512/data/pictures/phone-s10lite/2023-04-18/20230418_103520.heic")
    exifdata = image.getexif()
    # getting the basic metadata from the image
    info_dict = {
        "Filename": image.filename,
        "Image Size": image.size,
        "Image Height": image.height,
        "Image Width": image.width,
        "Image Format": image.format,
        "Image Mode": image.mode,
        "Image is Animated": getattr(image, "is_animated", False),
        "Frames in Image": getattr(image, "n_frames", 1)
    }

    for label, value in info_dict.items():
        print(f"{label:25}: {value}")

    # iterating over all EXIF data fields
    for tag_id in exifdata:
        tag = TAGS.get(tag_id, tag_id)
        data = exifdata.get(tag_id)
        # decode bytes
        if isinstance(data, bytes):
            try:
                data = data.decode()
            except:
                print("can't decode ")

        print(f"{tag:25}: {data} ({tag_id})")


def test2(filepath):
    filepath = "/mnt/sd512/data/pictures/asia-2023/2023-04-20/DSC07489.JPG"
    creation_date = os.path.getctime(filepath)
    print(filestamp_to_local_date_str(creation_date))
    print(filestamp_to_utc_date_str(creation_date))


def date_taken(filepath):
    try:
        im = Image.open(filepath)
        exif = im.getexif()
        if exif is not None:
            date = exif.get(EXIF_DATATIME)
            if date is not None:
                return (date.split(' ')[0]).replace(":", "-")
    except Exception as ex:
        print('No date taken:', ex)
        #  None

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


def update_file_location(source_root, dest_root, exclude, include_regex, verbose):
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

            creation_timestamp = os.path.getctime(filepath)
            date_local = filestamp_to_local_date_str(creation_timestamp)
            date_utc = filestamp_to_utc_date_str(creation_timestamp)
            date_taken_exif = date_taken(filepath)

            if date_taken_exif is not None and date_taken_exif != date_utc:
                print("date taken not utc", filepath,
                      date_taken_exif, date_utc, date_local)

            if date_taken_exif is not None:
                date_to_use = date_taken_exif
            else:
                date_to_use = date_utc

            _, filename = os.path.split(filepath)

            #  print(filepath, date_local, date_utc, date_taken_exif)

            dest_file_old = os.path.join(dest_root, date_local, filename)
            dest_file_new = os.path.join(dest_root, date_to_use, filename)
            photo_dir = os.path.join(dest_root, date_to_use)

            if verbose:
                print(filepath, dest_file_new)

            if not os.path.exists(dest_file_new):
                if not os.path.exists(photo_dir):
                    os.makedirs(photo_dir)
                if not os.path.exists(dest_file_old):
                    print(dest_file_old, "does not exist and therefore can't be moved")
                else:
                    print("move", dest_file_old, " ===> ", dest_file_new)
                    res = shutil.move(dest_file_old, photo_dir)
                    #
                    if os.path.exists(dest_file_new):
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
    update_file_location(os.path.expanduser(args.source), os.path.expanduser(
        args.dest), args.exclude, args.include, args.verbose)


if __name__ == '__main__':
    main()
