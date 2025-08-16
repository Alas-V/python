questions = [
    {"question": "Столица России?", "answer": "москва"},
    {"question": "Столица Турции?", "answer": "анкара"},
    {"question": "Столица Великобритании?", "answer": "лондон"},
    {"question": "Столица США?", "answer": "вашингтон"},
    {"question": "Столица Казахстана?", "answer": "астана"},
]
score = 0

for q in questions:
    user_answer = input(q["question"] + " ")
    if user_answer.lower() == q["answer"]:
        score += 1

if score > 3:
    result_massage = "Поздравляем"
else:
    result_massage = "Попробуйте еще раз"


TOTAL_QUESTION = 5

print(
    f"Вы ответили правильно на {score} вопросов из {TOTAL_QUESTION}. {result_massage}"
)
