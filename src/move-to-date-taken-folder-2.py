"""
=============================================================================
File: move-to-date-taken-folder-2.py
Description: fetch-photos.py moved photos uses datetime exif field which is not
always the original photo date. If a camera photo has been modified on phone 
fetch-photos.py uses the modified date. Change so that original date is used.
This way if finding a photo in the camera dir, we can look at the equivalent date
folder in the phone dir.
This patch file corrects that situation by moving photos into the folder that
matches the date the photo was taken.
Author: Praful https://github.com/Praful/fetch-photos
Licence: GPL v3
=============================================================================
"""
# py ./move-to-date-taken-folder-2.py --dir /mnt/sd512/data/pictures/phone-s24ultra --exclude '.mp4'
#
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
EXIF_DATATIME_ORIGINAL = 36867
EXIF_OFFSET = 34665


def print_exif_ifd(exif):
    print("EXIF IFD ---------------------------------------")
    for key, value in TAGS.items():
        if value == "ExifOffset":
            break
    print("key is ", key)
    info = exif.get_ifd(key)

    for key, data in info.items():
        tag = TAGS.get(key, key)
        print(f"{tag:25}: {data} ({key})")


def test():
    filename = "/home/praful/data/pictures/sdcard/phone-s24ultra/2025-02-23/DSC05043~2.JPG"
    image = Image.open(filename)
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

    print("date taken original", date_taken_original(filename))
    #  print_exif_ifd(exifdata)


def test2(filepath):
    filepath = "/mnt/sd512/data/pictures/asia-2023/2023-04-20/DSC07489.JPG"
    creation_date = os.path.getctime(filepath)
    print(filestamp_to_local_date_str(creation_date))
    print(filestamp_to_utc_date_str(creation_date))


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
        print('No date taken:', ex)
        #  None

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


# the original way before exif_date_original was added
def get_creation_date2(filepath):
    date_exif = exif_date(filepath)

    if date_exif is not None:
        return date_exif
    else:
        creation_timestamp = os.path.getctime(filepath)
        #  date_local = filestamp_to_local_date_str(creation_timestamp)
        return filestamp_to_utc_date_str(creation_timestamp)


def setup_command_line():
    """
    Define command line switches
    """
    cmdline = argparse.ArgumentParser(
        prog='fetch-photos.py', description='Fetch photos and put them into date folders')
    cmdline.add_argument('--dir', dest='dir', type=str, required=True,
                         help='Folder to copy from')

    cmdline.add_argument('--exclude', dest='exclude', type=str, required=False,
                         help='Exclude paths containing this string')

    cmdline.add_argument('--include', dest='include', type=str, required=False,
                         help='Include paths containing this regex; overrides --exclude')

    cmdline.add_argument('--verbose', action=argparse.BooleanOptionalAction,
                         default=False, help='Provides verbose output')

    return cmdline


def must_include(filepath, regex):
    return re.search(rf'{regex}', filepath) is not None


def update_file_location(source_root, exclude, include_regex, verbose):
    file_count = files_copied = files_exist = file_errors = files_excluded = 0

    dest_root = source_root

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
            date_exif = exif_date(filepath)
            date_original_exif = exif_date_original(filepath)

            if date_original_exif is not None:
                date_to_use = date_original_exif
            elif date_exif is not None:
                date_to_use = date_exif
            else:
                date_to_use = date_utc

            _, filename = os.path.split(filepath)

            #  dest_file_old = os.path.join( dest_root, get_creation_date2(filepath), filename)
            dest_file_old = filepath
            dest_file_new = os.path.join(dest_root, date_to_use, filename)
            photo_dir = os.path.join(dest_root, date_to_use)

            if verbose:
                print(filepath, dest_file_new)

            if not os.path.exists(dest_file_new):
                if not os.path.exists(photo_dir):
                    os.makedirs(photo_dir)
                    print("making dir", photo_dir)
                if not os.path.exists(dest_file_old):
                    print(dest_file_old,
                          "does not exist and therefore can't be moved")
                else:
                    print("move", dest_file_old, " ===> ", dest_file_new)
                    res = shutil.move(dest_file_old, photo_dir)
                    #  res = 0
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
    update_file_location(os.path.expanduser(args.dir),
                         args.exclude, args.include, args.verbose)

    #  test()


if __name__ == '__main__':
    main()
