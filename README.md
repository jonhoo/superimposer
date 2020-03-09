# Superimposer — combine presentation videos with slides

**You have**: pdf slides and a video of you talking about them.

**You want**: a video of your slides with you in the corner.

**You need**: superimposer.

So, you presented something, and now have a recording of it, that's
awesome! But the slides are hard to read, or got cropped out somehow,
and you want to fix that. Fear not, superimposer has you covered! Just
tell it what slide to display when, point it at your slides and your
video, and it will generate a new video for you with the slides front
and center, and your video tucked away nicely in a corner.

To get up and running, you first need the video file for your
presentation (let's say it's `presentation.mp4`) and a PDF file with
your slides (let's say it's `slides.pdf`). Then, create a file called
`transitions.txt` and write:

```
00:00 1
```

You probably get the gist here. Play through your presentation, and
every time you change slides, write down a new line with the current
timestamp (the `O` hotkey in `mpv` is handy here) and the desired slide
number. When you're done, run:

```console
$ superimposer presentation.mp4 slides.pdf superimposed.mp4
```

This will eventually kick off `ffmpeg`, which will take a while to
encode your video. When it's done, `superimposed.mp4` should have what
you want!

Superimposer takes a bunch of handy command-line arguments to tweak the
output. Run `superimposer --help` to see them. If you're using H.264,
you may want to consider also giving:

```console
-- --tune stillimage
```

## Requirements

 - `ffmpeg` and `ffprobe` (usually installed with [`ffmpeg`](https://ffmpeg.org/))
 - `pdftoppm` (part of [Poppler](https://poppler.freedesktop.org/))

## Normalizing audio

If your audio is sad, try [`fmpeg-normalizer`] with something like:

```console
$ ffmpeg-normalize superimposed.mp4 -o superimposed-normalized.mp4 -c:a aac
```

## Hardware acceleration

You can pass additional parameters to the ffmpeg encoder by placing them
after `--` in the argument list to `superimposer`. You'll probably want
to read up on [hardware acceleration in ffmpeg], and maybe the [ffmpeg
VAAPI encoding docs].

  [hardware acceleration in ffmpeg]: https://trac.ffmpeg.org/wiki/HWAccelIntro
  [ffmpeg VAAPI encoding docs]: https://trac.ffmpeg.org/wiki/Hardware/VAAPI#Encoding
  [`ffmpeg-normalizer`]: https://github.com/slhck/ffmpeg-normalize
