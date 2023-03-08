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

    return cmdline

#  source_root = os.path.expanduser('/media/praful/disk/DCIM')
#  dest_root = os.path.expanduser('~/Pictures')


def move_files(source_root, dest_root):
    file_count = files_copied = files_exist = file_errors = 0

    for filepath in glob.iglob(source_root + '**/**', recursive=True):

        creation_date = os.path.getctime(filepath)

        if os.path.isfile(filepath):
            file_count += 1

            year, month, day, hour, minute, second = time.localtime(creation_date)[
                :-3]
            date = "%d-%02d-%02d" % (year, month, day)
            _, filename = os.path.split(filepath)

            dest_file = os.path.join(dest_root, date, filename)
            photo_dir = os.path.join(dest_root, date)
            print(filepath, dest_file)

            if not os.path.exists(dest_file):
                print('copying', filepath)
                if not os.path.exists(photo_dir):
                    os.makedirs(photo_dir)
                res = shutil.copy2(filepath, photo_dir)
                if os.path.exists(dest_file):
                    print('====> Done:', res)
                    files_copied += 1
                else:
                    print('====> FAILED:', res)
                    file_errors += 1
            else:
                print('====> Skipping: file already exists in destination folder')
                files_exist += 1

    print(
        f'Total files: {file_count}\nCopied: {files_copied}\nSkipped: {files_exist}\nErrors: {file_errors}')


def main():
    """
    Processing begins here if script run directly
    """
    args = setup_command_line().parse_args()
    print(args)
    move_files(os.path.expanduser(args.source), os.path.expanduser(args.dest))


if __name__ == '__main__':
    main()
