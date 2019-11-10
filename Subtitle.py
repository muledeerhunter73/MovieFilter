import pysrt as pysrt
import re as re

class FilterWordAndLocation:
    Subtitle = ""
    Word = ""

class FilterWords:
    OffensiveWord = ""
    ReplacementWord = ""
    Category = ""

class SubtitleHandler:
    subtitleList = []
    SubsWithLanguageList = []
    LanguageList = []
    WordsToFilter = []

    def ReadWordsFromFilterFile(self): 
        with open("WordsToFilter.txt") as infile:
            for line in infile.readlines():
                tempWord = FilterWords()
                splitLine = line.rstrip().split(',')
                tempWord.OffensiveWord = splitLine[0]
                tempWord.ReplacementWord = splitLine[1]
                tempWord.Category = splitLine[2]
                self.WordsToFilter.append(tempWord)
                
    def ParseSubtitleFile(self, fileToParse):
        self.subtitleList = pysrt.open(fileToParse)

    def FindProfanity(self):
        for sub in self.subtitleList:
            for word in self.WordsToFilter:
                if(self.IsWordInString(sub.text.upper(), word.OffensiveWord)):
                    temp = FilterWordAndLocation()
                    temp.Subtitle = sub
                    temp.Word = word.OffensiveWord
                    self.SubsWithLanguageList.append(temp)
    
    def IsWordInString(self, string1, word):
        if re.search(r"\b" + re.escape(word) + r"\b", string1):
            return True
        return False
    
    def ConvertToMilliseconds(self, subTime):
        return ((subTime.hours * subTime.HOURS_RATIO) + (subTime.minutes * subTime.MINUTES_RATIO) + 
                (subTime.seconds * subTime.SECONDS_RATIO) + subTime.milliseconds)