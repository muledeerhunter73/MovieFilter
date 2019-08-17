import subprocess as subprocess

class AudioMuter:

    def ExtractAudio(self, videoFile, start, end):
        subprocess.call(["ffmpeg", "-ss", start, "-endpos", end,"-oac", "copy", "-ovc", "copy", videoFile, "-o", "Temp.mp4" ])