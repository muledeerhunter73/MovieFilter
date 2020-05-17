import pysrt as pysrt
import re as re
import string

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
            sub.text = sub.text.lower()
            if("he'll" in sub.text):
               sub.text = sub.text.replace("he'll", "NotaSwear") 
            sub.text = sub.text.translate(str.maketrans('', '', string.punctuation)) # Remove punctuation from text.
            for word in self.WordsToFilter:
                if(self.IsWordInString(sub.text.upper(), word.OffensiveWord)):
                    temp = FilterWordAndLocation()
                    temp.Subtitle = sub
                    temp.Word = word.OffensiveWord
                    if(len(self.SubsWithLanguageList) != 0):
                        last_found = self.SubsWithLanguageList[-1]
                        if(last_found.Subtitle.start != sub.start):
                            self.SubsWithLanguageList.append(temp)
                    else:
                       self.SubsWithLanguageList.append(temp) 
    
    def IsWordInString(self, string1, word):
        if re.search(r"\b" + re.escape(word) + r"\b", string1):
            return True
        return False
    
    # Probably don't need this function
    def ConvertToMilliseconds(self, subTime):
        return ((subTime.hours * subTime.HOURS_RATIO) + (subTime.minutes * subTime.MINUTES_RATIO) + 
                (subTime.seconds * subTime.SECONDS_RATIO) + subTime.milliseconds)

    def SaveResultsToFile(self,filename):
        with open(filename, 'w') as infile:
            for item in self.SubsWithLanguageList:
                infile.write(str(item.Subtitle.start).split(",", 1)[0])
                infile.write("\n\t" + item.Word + "\n")
