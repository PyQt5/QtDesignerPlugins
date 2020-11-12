import re

class InputScanner:
    def __init__(self, input_string):
        self.__six = __import__("six")
        if input_string is None:
            input_string = ''
        self.__input = input_string
        self.__input_length = len(self.__input)
        self.__position = 0

    def restart(self):
        self.__position = 0

    def back(self):
        if self.__position > 0:
            self.__position -= 1

    def hasNext(self):
        return self.__position < self.__input_length

    def next(self):
        val = None
        if self.hasNext():
            val = self.__input[self.__position]
            self.__position += 1

        return val

    def peek(self, index=0):
        val = None
        index += self.__position
        if index >= 0 and index < self.__input_length:
            val = self.__input[index]

        return val

    def test(self, pattern, index=0):
        index += self.__position
        return index >= 0 and index < self.__input_length and bool(
            pattern.match(self.__input, index))

    def testChar(self, pattern, index=0):
        # test one character regex match
        val = self.peek(index)
        return val is not None and bool(pattern.match(val))

    def match(self, pattern):
        pattern_match = None
        if self.hasNext():
            pattern_match = pattern.match(self.__input, self.__position)
            if bool(pattern_match):
                self.__position = pattern_match.end(0)
        return pattern_match

    def read(self, starting_pattern, until_pattern=None, until_after=False):
        val = ''
        pattern_match = None
        if bool(starting_pattern):
            pattern_match = self.match(starting_pattern)
            if bool(pattern_match):
                val = pattern_match.group(0)

        if bool(until_pattern) and \
                (bool(pattern_match) or not bool(starting_pattern)):
            val += self.readUntil(until_pattern, until_after)

        return val

    def readUntil(self, pattern, include_match=False):
        val = ''
        pattern_match = None
        match_index = self.__position
        if self.hasNext():
            pattern_match = pattern.search(self.__input, self.__position)
            if bool(pattern_match):
                if include_match:
                    match_index = pattern_match.end(0)
                else:
                    match_index = pattern_match.start(0)
            else:
                match_index = self.__input_length

            val = self.__input[self.__position:match_index]
            self.__position = match_index

        return val

    def readUntilAfter(self, pattern):
        return self.readUntil(pattern, True)

    def get_regexp(self, pattern, match_from=False):
        result = None
        # strings are converted to regexp
        if isinstance(pattern, self.__six.string_types) and pattern != '':
            result = re.compile(pattern)
        elif pattern is not None:
            result = re.compile(pattern.pattern)
        return result

    # css beautifier legacy helpers
    def peekUntilAfter(self, pattern):
        start = self.__position
        val = self.readUntilAfter(pattern)
        self.__position = start
        return val

    def lookBack(self, testVal):
        start = self.__position - 1
        return start >= len(testVal) and \
            self.__input[start - len(testVal):start].lower() == testVal
