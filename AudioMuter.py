import os
import json
import string
import subprocess as subprocess
from datetime import datetime
from google.cloud import speech_v1
from google.cloud.speech import types
from Bio import pairwise2
from Bio.pairwise2 import format_alignment
from fuzzywuzzy import fuzz

class FilterTimes:
    startTime = ""
    endTime = ""

class MuteStringTimes:
    startPhraseTime = 0
    startWordTime = 0
    endWordTime = 0

class AudioMuter:

    muteString = ""

    def ExtractVideo(self, videoFile, start, end):
        #durTime = (end - start)
        duration = str(end).split(",", 1)[0]
        #startTime = str(start).split(",", 1)[0]
        subprocess.call(["ffmpeg","-y","-hide_banner","-loglevel", "panic", "-ss", start, "-i", videoFile, "-t",duration , "-vcodec", "copy" , "-acodec", "copy", "TempVideo.mp4"])

    def ExtractAudio(self, videoFile, start, end):
        if os.path.exists("TempAudio.flac"):
            os.remove("TempAudio.flac")
        durTime = end - start
        duration = str(durTime).replace(',', '.')
        startTime = str(start).replace(',', '.')
        subprocess.call(["ffmpeg","-y","-hide_banner", "-loglevel", "panic", "-ss", startTime, "-i", videoFile, "-t",duration , "-c:a", "flac", "TempAudio.flac"])

    def FindWordLocationGoogle(self, wordtoFind, audioFile, resultFilename, subPhrase):
        client = speech_v1.SpeechClient()
        language_code = "en-US"
        config = {
            "enable_word_time_offsets": True,
            "language_code": language_code,
            "audio_channel_count": 2,
            "max_alternatives": 3,
            "enable_separate_recognition_per_channel": True,
            "speech_contexts": [{"phrases": wordtoFind}],
            "model": "video",
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
            # Go through all alernatives until found
            for alternative in result.alternatives:
                self.SaveToFile(resultFilename, alternative.transcript)
                times = self.GetStartAndEndTime(alternative.words, wordtoFind.lower())
                if(times != False):
                    return times
            
            #Find profanity with string alignment
            googlePhrase = result.alternatives[0].transcript.lower()
            googlePhrase = googlePhrase.translate(str.maketrans('', '', string.punctuation))
            googleWordList = result.alternatives[0].words
            startEnd = self.AlignStrings(googlePhrase, subPhrase, wordtoFind.lower())
            if(startEnd != False):
                times = self.setStartAndEnd(googleWordList[startEnd[0]], googleWordList[startEnd[1]])
                return times
        
        return False

    def SaveToFile(self, filename, data):
        with open(filename, 'a') as outFile:
            outFile.write(str(data) + "\n")

    def ReadFromJsonFile(self, filename):
        with open(filename) as inFile:
            return json.load(inFile)

    def GetStartAndEndTime(self, phrase, filterWord):
        if (' ' in filterWord):
            splitString = filterWord.split(' ')
            for i in range(len(phrase)):
                if(splitString[0] in self.UpdateGoogleWord(phrase[i].word.lower())):
                    endLocation = -1
                    counter = 1
                    while True:
                        if(counter < len(splitString)):
                            if(splitString[counter] in self.UpdateGoogleWord(phrase[i + counter].word.lower())):
                                endLocation = i + counter
                                counter = counter + 1
                            else:
                                break
                        else:
                            return self.setStartAndEnd(phrase[i], phrase[endLocation])
        else:
            for word in phrase:
                if(filterWord == self.UpdateGoogleWord(word.word.lower())):
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

    def convertTimes(self, startTimeOfPhrase, wordPosition):
        return (startTimeOfPhrase + (wordPosition / 1000000)) / 1000
        
    def addWordTimesToString(self, startTimeOfPhrase, startOfWord, endOfWord, startOffset, endOffset, movieName):
        startMute = "{:.2f}".format(self.convertTimes(startTimeOfPhrase, startOfWord) + startOffset)
        endMute = "{:.2f}".format(self.convertTimes(startTimeOfPhrase, endOfWord) + endOffset)

        if (self.muteString == ""):
            self.muteString = "volume=enable='between(t," + str(startMute) +"," + str(endMute) +")':volume=0"
        else:
            self.muteString = self.muteString + ", volume=enable='between(t," + str(startMute) +"," + str(endMute) +")':volume=0"

        self.WriteWordTimesToFile(startTimeOfPhrase, startOfWord, endOfWord, movieName)
        with open("muteString" + movieName + ".txt", 'w') as infile:
            infile.write(self.muteString)

    def WriteWordTimesToFile(self, startTimePhrase, startWordTime, endWordTime, movieName):
        with open("muteStringTimes" + movieName + ".txt", 'a') as outfile:
            outfile.write(str(startTimePhrase) + "," + str(startWordTime) + "," + str(endWordTime) + "\n")
    
    def ReadWordTimesFromFile(self, movieName):
        fileTimes = []
        with open("muteStringTimes" + movieName + ".txt") as infile:
            for line in infile:
                tempTimes = MuteStringTimes()
                line = line.rstrip()
                splitLine = line.split(',')
                tempTimes.startPhraseTime = float(splitLine[0])
                tempTimes.startWordTime = float(splitLine[1])
                tempTimes.endWordTime = float(splitLine[2])
                fileTimes.append(tempTimes)
        return fileTimes

    def UpdateGoogleWord(self, word):
        word = word.translate(str.maketrans('', '', string.punctuation)) # Remove punctuation from text.
        with open("WordsToReplace.txt") as infile:
            for line in infile:
                line = line.rstrip()
                splitline = line.split(',')
                if(word == splitline[0]):
                    return splitline[1]
        return word

    def AlignStrings(self, googlePhrase, subPhrase, whatToFilter):
        if(fuzz.partial_ratio(googlePhrase, subPhrase) > 65):
            subWordList = subPhrase.split(' ')
            googleWordList = googlePhrase.split(' ')
            alignment = pairwise2.align.globalxx(googlePhrase,subPhrase)
            googleAligned = alignment[0][0]
            subAligned = alignment[0][1]
            return self.FindPhraseStartAndEnd(googleAligned, subAligned,whatToFilter)
        return False      

    def FindPhraseStartAndEnd(self,googleAligned, subAligned, filterPhrase):
        googleStartCounter = 0
        googleEndCounter = 0
        phraseCounter = 0
        googleWordCounter = 0
        for i, char in enumerate(subAligned):
            if(googleAligned[i] == ' '):
                googleWordCounter += 1
            if(phraseCounter == len(filterPhrase) - 1):
                googleEndCounter = googleWordCounter
                return [googleStartCounter, googleEndCounter]
            if(phraseCounter == 0 and subAligned[i] == filterPhrase[0]):
                googleStartCounter = googleWordCounter
                phraseCounter += 1
            elif(phraseCounter > 0 and subAligned[i] == filterPhrase[phraseCounter]):
                phraseCounter += 1
            elif(phraseCounter > 0 and subAligned[i] == '-' ):
                continue
            else:
                googleStartCounter = 0
                phraseCounter = 0
        return False
