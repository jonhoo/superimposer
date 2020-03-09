#!/bin/env python

from PyPDF2 import PdfFileWriter, PdfFileReader
from shutil import copyfile

import argparse
import math
import os
import os.path
import subprocess
import sys
import tempfile

def main():
    """Where it all began."""

    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=argparse.FileType('rb'), help="video of the speaker")
    parser.add_argument("slides", type=argparse.FileType('rb'), help="slides in pdf format")
    parser.add_argument("output", type=argparse.FileType('wb'), help="superimposed video output file")
    parser.add_argument("-n", "--dry-run", action='store_true', help="don't run the final encoding pass")
    parser.add_argument("--height", type=int, help="height of output video (defaults to 1080)", default=1080)
    parser.add_argument("--crop", help="box to crop video from (w:h:x:y)")
    parser.add_argument("--fraction", type=float, help="size of speaker box relative to video", default=1/3.0)
    parser.add_argument("-t", type=argparse.FileType('r', encoding='UTF-8'), help="path to the file that specifies the slide transitions", default='transitions.txt')
    parser.add_argument("--end", help="timestamp to end video at")
    parser.add_argument('remaining', nargs=argparse.REMAINDER, help="additional arguments to pass to ffmpeg as output options")
    args = parser.parse_args()
    args.video.close()
    args.output.close()

    slides = tempfile.TemporaryDirectory("slides")
    segments = tempfile.TemporaryDirectory("segments")
    segment_list = tempfile.NamedTemporaryFile('w')

    # get all the transitions
    transitions = []
    with open('transitions.txt', 'r') as t:
        for line in t.readlines():
            line = line.strip()
            if line.startswith('#'):
                continue
            fields = line.split()
            if len(fields) >= 2:
                transitions.append((fields[0], int(fields[1])))

    # split the pdf
    inputpdf = PdfFileReader(args.slides)
    size = None
    for i in range(inputpdf.numPages):
        page = inputpdf.getPage(i)
        if size is None:
            size = page.mediaBox
        elif size != page.mediaBox:
            print("pdf page sizes differ.")
            sys.exit(1)
            return
        output = PdfFileWriter()
        output.addPage(page)
        with open("%s/%d.pdf" % (slides.name, i + 1), "wb") as outputStream:
            output.write(outputStream)

    if size is None:
        print("no slides?")
        sys.exit(1)
        return

    # get info about the video
    end = int(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", args.video.name], capture_output=True).stdout.strip()))
    if args.end:
        parts = args.end.split(":")
        s = int(parts.pop())
        if len(parts) != 0:
            s += int(parts.pop()) * 60
        if len(parts) != 0:
            s += int(parts.pop()) * 60 * 60
        end = s
    fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "V", "-show_entries", "stream=r_frame_rate", "-of", "default=noprint_wrappers=1:nokey=1", args.video.name], capture_output=True, encoding="UTF-8").stdout.strip()
    transitions.append((end, transitions[-1][1]))

    # h * 192 / 72 = 1080
    # h * r / 72 = target_h
    # r = 72 * target_h / h
    height = args.height
    # search for next pdf scale that produces divisible-by-two width and height
    while True:
        pdf_scale = int(72.0 * args.height / float(size.upperLeft[1] - size.lowerLeft[1]))
        width = float(size.upperRight[0] - size.upperLeft[0]) * pdf_scale / 72.0
        # print(width, height, pdf_scale)
        if math.ceil(width) % 2 == 0:
            break
        height += 1

    print("pdf page size is", size.lowerRight[0], "by", size.upperRight[1], "and will be scaled with DPI", pdf_scale)
    print("output will be %dx%d, and %s long (at %s fps)" % (width, height, pretty_time_delta(end), fps))
    print("transitions:")
    print("\n".join([" - slide % 3d @ %s" % (slide, time) for (time, slide) in transitions[:-1]]))

    print("---")
    print("==> producing slide video segments")

    i = 0
    since = 0
    show = None
    for (time, slide) in transitions:
        if type(time) == type(end):
            s = time
        else:
            parts = time.split(":")
            s = int(parts.pop())
            if len(parts) != 0:
                s += int(parts.pop()) * 60
            if len(parts) != 0:
                s += int(parts.pop()) * 60 * 60

        if s > end:
            if since >= end:
                # no point in encoding things after this
                break
            # run this slide until the end time
            s = end

        # create a png for the slide we're supposed to show
        subprocess.run(["pdftoppm", "-singlefile", "-png", "-r", "%d" % pdf_scale, "%s/%d.pdf" % (slides.name, slide), "%s/%d" % (segments.name, i)])

        if show is not None:
            # loop that png frame for the currently shown frame until this time
            print(" -> loop slide %d for %s" % (i - 1, pretty_time_delta(s - since)))
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "image2", "-loop", "1", "-framerate", "1", "-pattern_type", "none", "-i", "%s/%d.png" % (segments.name, i - 1),
                "-r", "1", "-t", "%d" % (s - since), "-vcodec", "png", "-an",
                "%s/%d.mov" % (segments.name, i - 1)
            ])
            segment_list.write("file '%s/%d.mov'\n" % (segments.name, i - 1))

        since = s
        show = slide
        i += 1

    filter_complex = []
    filter_complex.append("[1] fps=%s [slides]" % fps)

    if args.crop is None:
        filter_complex.append("[0] scale=-1:%d [pip]" % (int(height * args.fraction)))
    else:
        filter_complex.append("[0] crop=%s,scale=-1:%d [pip]" % (args.crop, int(height * args.fraction)))

    filter_complex.append("[slides][pip] overlay=main_w-overlay_w-10:main_h-overlay_h-10")

    segment_list.flush()

    print("==> producing slide video")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", segment_list.name, "-c", "copy", "%s/all.mov" % segments.name])

    if args.dry_run:
        copyfile("%s/all.mov" % segments.name, "all.mov")

    encoding_args = ["ffmpeg", "-y",
        "-i", args.video.name,
        "-i", "all.mov" if args.dry_run else "%s/all.mov" % segments.name,
        "-filter_complex", "; ".join(filter_complex),
        "-t", "%d" % end,
        "-pix_fmt", "yuv420p",
        "-r", "%s" % fps,
        *args.remaining,
        args.output.name]

    print("==> superimposing video onto slides")
    if args.dry_run:
        print(" -> would run:")
        print(encoding_args)
        print(" -> but skipping since this is a dry run.")
    else:
        subprocess.run(encoding_args)

def pretty_time_delta(seconds):
    seconds = int(seconds)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if hours > 0:
        return '%02d:%02d:%02d' % (hours, minutes, seconds)
    else:
        return '%02d:%02d' % (minutes, seconds)

if __name__ == "__main__":
    main()
