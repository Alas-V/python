TAX_RATE = 0.10

while True:
    try:
        first_meal_price = float(input("Введите стоимость основного блюда: "))
        beverage_price = float(input("Введите стоимость напитка: "))
        dessert_price = float(input("Введите стоимость десерта: "))
        if first_meal_price < 0 or beverage_price < 0 or dessert_price < 0:
            print("Стоимость не может быть отрицательной")
            continue
        break
    except ValueError:
        print("Ошибка! Нужно ввести число.")

price = first_meal_price + beverage_price + dessert_price

print("\n-------------------------------------------")
print(f"Цена за позиции без учета налога и чаевых {price:.2f} руб.")


print("Выберите процент чаевых")
print("1 - 5%")
print("2 - 10%")
print("3 - 15%")
print("4 - Свой вариант")
while True:
    try:
        choice = int(input("Ваш выбор (1-4): "))
        if choice not in [1, 2, 3, 4]:
            print("Пожалуйста, введите число от 1 до 4")
            continue
        break
    except ValueError:
        print("Пожалуйста, введите корректное число от 1 до 4")

if choice < 4:
    tips_procent = {1: 5, 2: 10, 3: 15}[choice]
else:
    while True:
        try:
            tips_procent = float(input("Введите процент чаевых: "))
            if tips_procent < 0:
                raise ValueError("Вы не можете вписать отрицательные чаевые")
            if tips_procent > 100:
                print("Чаевые не могут быть больше 100%")
                continue
            break
        except ValueError:
            print("Ошибка! Введите корректное число.")

tips = price * tips_procent / 100
tax = price * TAX_RATE
total_price = price + tips + tax


print("\n-------------------------------------------")
print(f"Налог (10%) = {tax:.2f}")
print(f"Чаевые ({tips_procent}%) = {tips:.2f} руб.")
print("-------------------------------------------")
print(f"Итог к оплате: {total_price:.2f}")
