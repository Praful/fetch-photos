# Fetch photos from camera
This program copies files from one location to another, grouping them by their creation dates. It was written to copy photos from my camera.

```
Usage: fetch-photos.py [-h] --from SOURCE --to DEST

Fetch photos and put them into date folders

options:
  -h, --help     show this help message and exit
  --from SOURCE  Folder to copy from
  --to DEST      Folder to copy to
```

For example,
```
python fetch-photos.py --from /media/user/disk/DCIM --to ~/Pictures
```
This will copy photos from `/media/user/disk/DCIM` (and sub-folders) to `~/Pictures`. 
In `~/Pictures` folders will be created for the date of each photo, eg all files from 
21 March 2022 will be copied into `~/Pictures/2022-03-21`.

Files in the destination folder (`--to` ) are _not_ overwritten. So you can run the program many times and it will pick up where it left off, skipping the files already copied (or happen to already exist).

When finished, the program prints out the total number of files found, the number copied, the number skipped (because they already exist in the destination folder) and the number of errors.

Although written to get photos from a camera, it can be used for any source folder whose files you want to classify by their creation date.