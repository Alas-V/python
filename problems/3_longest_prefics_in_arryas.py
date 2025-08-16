from typing import List


class Solution:
    def longestCommonPrefix(self, strs: List[str]) -> str:
        words = [words for words in strs]
        word_1, word_2 = words
        list_word = [char for word in strs for char in word]
        length_1_words = len(word_1)
        length_2_words = len(word_2) + length_1_words
        if (
            list_word[0] == list_word[length_1_words]
            and list_word[0] == list_word[length_2_words]
        ):
            answer = list_word[0]
        print(answer, list_word, length_2_words, length_1_words)

    longestCommonPrefix(1, strs=["flower", "flow", "flight"])
