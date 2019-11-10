import os
import subprocess as subprocess
from datetime import datetime
from google.cloud import speech_v1
from google.cloud.speech import types

class FilterTimes:
    startTime = ""
    endTime = ""

class AudioMuter:

    muteString = ""

    def convertTimes(self, startTimeOfPhrase, wordPosition):
        return (startTimeOfPhrase + (wordPosition / 1000000)) / 1000

    def ExtractAudio(self, videoFile, start, end):
        durTime = end - start + 2000
        duration = str(durTime).split(",", 1)[0]
        startTime = str(start).split(",", 1)[0]
        subprocess.call(["ffmpeg","-y", "-ss", startTime, "-i", videoFile, "-t",duration , "-q:a", "0" , "-map", "a", "TempAudio.mp3"])
        self.convertAudio()

    def convertAudio(self):
        subprocess.call(["ffmpeg","-y", "-i", "TempAudio.mp3", "-c:a", "flac", "TempAudio.flac"])

    def FindWordLocationGoogle(self, wordtoFind, audioFile):
        client = speech_v1.SpeechClient()
        language_code = "en-US"
        config = {
            "enable_word_time_offsets": True,
            "language_code": language_code,
            "audio_channel_count": 2,
            "enable_separate_recognition_per_channel": True,
        }

        with open(audioFile, 'rb') as audio_file:
            content = audio_file.read()
            audio = types.RecognitionAudio(content=content)
         
        response = client.recognize(config, audio)

        if (len(response.results) == 0):
            print("Unable to transcribe audio")
        else:
            # The first result includes start and end time word offsets
            result = response.results[0]
            ''' Need to account for phrase words to filter'''
            # First alternative is the most probable result
            alternative = result.alternatives[0]
            times = self.GetStartAndEndTime(alternative.words, wordtoFind.lower())
            return times
        return False

    def GetStartAndEndTime(self, phrase, filterWord):
        if (' ' in filterWord):
            splitString = filterWord.split(' ')
            for i in range(len(phrase)):
                if(phrase[i].word.lower() == splitString[0]):
                    endLocation = -1
                    counter = 1
                    while True:
                        if(counter < len(splitString)):
                            if(phrase[i + counter].word.lower() == splitString[counter]):
                                endLocation = i + counter
                                counter = counter + 1
                            else:
                                break
                        else:
                            return self.setStartAndEnd(phrase[i], phrase[endLocation])
        else:
            for word in phrase:
                if(word.word.lower() == filterWord):
                    return self.setStartAndEnd(word, word)
        return False

    def setStartAndEnd(self, wordStart, wordEnd):
        times = FilterTimes()
        times.startTime = (wordStart.start_time.seconds * 1000000000) + wordStart.start_time.nanos
        times.endTime = (wordEnd.end_time.seconds * 1000000000) + wordEnd.end_time.nanos
        if(times.startTime == times.endTime):
            # Add half a second to the end time
            times.endTime = times.endTime + 500000000
        return times

    def muteAudio(self, videoFile):
        editedVideoName = "{0}_{2}.{1}".format(*videoFile.rsplit('.', 1) + ["edited"])
        subprocess.call(["ffmpeg","-y", "-i", videoFile, "-af", self.muteString, editedVideoName])

    def addWordTimesToString(self, startTimeOfPhrase, startOfWord, endOfWord):
        startMute = self.convertTimes(startTimeOfPhrase, startOfWord)
        endMute = self.convertTimes(startTimeOfPhrase, endOfWord)

        if (self.muteString == ""):
            self.muteString = "volume=enable='between(t," + str(startMute) +"," + str(endMute) +")':volume=0"
        else:
            self.muteString = self.muteString + ", volume=enable='between(t," + str(startMute) +"," + str(endMute) +")':volume=0"

