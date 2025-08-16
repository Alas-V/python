class Solution:
    def romanToInt(self, s: str) -> int:
        list_of_roman = [roman_number for roman_number in str(s)]
        answer = 0
        for num, next_num in zip(list_of_roman, list_of_roman[1:] + [None]):
            if num == "I" and (next_num == "V" or next_num == "X"):
                answer -= 1
            elif num == "I":
                answer += 1
            if num == "V":
                answer += 5
            if num == "X" and (next_num == "L" or next_num == "C"):
                answer -= 10
            elif num == "X":
                answer += 10
            if num == "L":
                answer += 50
            if num == "C" and (next_num == "D" or next_num == "M"):
                answer -= 100
            elif num == "C":
                answer += 100
            if num == "D":
                answer += 500
            if num == "M":
                answer += 1000
        return answer
