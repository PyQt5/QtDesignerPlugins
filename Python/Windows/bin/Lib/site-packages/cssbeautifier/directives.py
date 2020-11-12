
import re


class Directives:

    def __init__(self, start_block_pattern, end_block_pattern):

        self.__directives_block_pattern = re.compile(start_block_pattern + r' beautify( \w+[:]\w+)+ ' + end_block_pattern)
        self.__directive_pattern = re.compile(r' (\w+)[:](\w+)')

        self.__directives_end_ignore_pattern = re.compile(start_block_pattern + r'\sbeautify\signore:end\s' + end_block_pattern)

    def get_directives(self, text):
        if not self.__directives_block_pattern.match(text):
            return None

        directives = {}
        directive_match = self.__directive_pattern.search(text)

        while directive_match:
            directives[directive_match.group(1)] = directive_match.group(2)
            directive_match = self.__directive_pattern.search(
                text, directive_match.end())


        return directives

    def readIgnored(self, input):
        return input.readUntilAfter(self.__directives_end_ignore_pattern)
