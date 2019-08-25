import subprocess as subprocess
from datetime import datetime
from SimpleAudioIndexer import SimpleAudioIndexer as sai

class AudioMuter:

    def ExtractAudio(self, videoFile, start, end):
        startTime = datetime.strptime(start, "%H:%M:%S")
        endTime = datetime.strptime(end, "%H:%M:%S")
        duration = endTime - startTime
        subprocess.call(["ffmpeg", "-ss", start, "-i", videoFile, "-t",str(duration) , "-ab", "160k" , "-ac", "2", "-ar", "44100", "-vn", "TempAudio.wav"])

    def FindWordLocation(self, wordtoFind, audioFile):
        indexer = sai(audioFile, "cmu")
        result = indexer.search_gen(wordtoFind)
        return result