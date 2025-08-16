USD_COURSE = 75
EUR_COURSE = 85

last_1_usd = 0
last_1_eur = 0

usd_operation = 0
conversion_usd = 0
eur_operation = 0
conversion_eur = 0


def def_conversion_usd(usd_operation, conversion_usd, eur_operation, conversion_eur):
    while True:
        try:
            print(f"\nКурс конвертации: 1RUB = {USD_COURSE} USD")
            usd_operation = float(input("Введите количество рублей для конвертации: "))
            if usd_operation < 0:
                print(
                    "\nОшибка! Количество рублей для конвертации не может быть отрицательным. Введите корректное значение."
                )
                continue
            if usd_operation > 0:
                conversion_usd = int(usd_operation / USD_COURSE)
                print(
                    f"\nПри конверсии {usd_operation} RUB Вы получите: {conversion_usd:.2f} USD"
                )
                print("1. Показать историю операций. \n2.  Вернуться в меню. ")
                while True:
                    try:
                        choice_end = int(input("Выберите действие: "))
                        if choice_end > 2:
                            print("Ошибка! Выберите действие (1-2)")
                            continue
                        elif choice_end < 0:
                            print("Ошибка! Выберите действие (1-2)")
                            continue
                        if choice_end == 1:
                            history(
                                usd_operation,
                                conversion_usd,
                                eur_operation,
                                conversion_eur,
                                last_1_usd,
                                last_1_eur,
                            )
                            break
                        if choice_end == 2:
                            menu(
                                usd_operation,
                                conversion_usd,
                                eur_operation,
                                conversion_eur,
                            )
                            break
                    except ValueError:
                        print("Ошибка! Введите число (1-2)")
                        continue
        except ValueError:
            print(ValueError("Ошибка! Нужно ввести числовое значение."))
            continue
        return usd_operation, conversion_usd


def def_conversion_eur(usd_operation, conversion_usd, eur_operation, conversion_eur):
    while True:
        try:
            print("\nКурс конвертации: 1RUB = {EUR_COURSE} EUR")
            eur_operation = float(input("Введите количество рублей для конвертации: "))
            if eur_operation < 0:
                print(
                    "\nОшибка! Количество рублей для конвертации не может быть отрицательным. Введите корректное значение."
                )
                continue
            if eur_operation > 0:
                conversion_eur = int(eur_operation / EUR_COURSE)
                print(
                    f"\nПри конверсии {eur_operation} RUB Вы получите: {conversion_eur:.2f} EUR"
                )
                print("1. Показать историю операций. \n2.  Вернуться в меню. ")
                while True:
                    try:
                        choice_end = int(input("Выберите действие: "))
                        if choice_end > 2:
                            print("Ошибка! Выберите действие (1-2)")
                            continue
                        if choice_end < 0:
                            print("Ошибка! Выберите действие (1-2)")
                            continue
                        if choice_end == 1:
                            history(
                                usd_operation,
                                conversion_usd,
                                eur_operation,
                                conversion_eur,
                            )
                            break
                        if choice_end == 2:
                            menu(
                                usd_operation,
                                conversion_usd,
                                eur_operation,
                                conversion_eur,
                            )
                            break
                    except ValueError:
                        print("Ошибка! Введите число (1-2)")
                        continue
        except ValueError:
            print(ValueError("Ошибка! Нужно ввести числовое значение."))
            continue
        return eur_operation, conversion_eur


def history_usd(
    usd_operation,
    conversion_usd,
    last_1_usd,
):
    if last_1_usd == 0:
        last_1_usd = f"{usd_operation} RUB - {conversion_usd:.2} USD"
        if last_1_usd > 0:
            last_2_usd = f"{usd_operation} RUB - {conversion_usd:.2} USD"
            if last_2_usd > 0:
                last_3_usd = f"{usd_operation} RUB - {conversion_usd:.2} USD"
                if last_3_usd > 0:
                    last_4_usd = f"{usd_operation} RUB - {conversion_usd:.2} USD"
                    if last_4_usd > 0:
                        last_5_usd = f"{usd_operation} RUB - {conversion_usd:.2} USD"
                        if last_5_usd > 0:
                            last_1_usd = last_2_usd
                            last_2_usd = last_3_usd
                            last_3_usd = last_4_usd
                            last_4_usd = last_5_usd
                            last_5_usd = 0
    print(
        "\nИстория конвертаций RUB - USD: \n{Last_1_usd}\n{last_2_usd}\n{last_3_usd}\n{last_4_usd}\n{last_5_usd}"
    )
    return usd_operation, conversion_usd


def history_eur(eur_operation, conversion_eur, last_1_eur):
    if last_1_eur == 0:
        last_1_eur = f"{eur_operation} RUB - {conversion_eur:.2} EUR"
        if last_1_eur > 0:
            last_2_eur = f"{eur_operation} RUB - {conversion_eur:.2} EUR"
            if last_2_eur > 0:
                last_3_eur = f"{eur_operation} RUB - {conversion_eur:.2} EUR"
                if last_3_eur > 0:
                    last_4_eur = f"{eur_operation} RUB - {conversion_eur:.2} EUR"
                    if last_4_eur > 0:
                        last_5_eur = f"{eur_operation} RUB - {conversion_eur:.2} EUR"
                        if last_5_eur > 0:
                            last_1_eur = last_2_eur
                            last_2_eur = last_3_eur
                            last_3_eur = last_4_eur
                            last_4_eur = last_5_eur
                            last_5_eur = 0
        print(
            "\nИстория конвертаций RUB - EUR: \n{Last_1_eur}\n{last_2_eur}\n{last_3_eur}\n{last_4_eur}\n{last_5_eur}"
        )
    return eur_operation, conversion_eur


def history(
    usd_operation, conversion_usd, eur_operation, conversion_eur, last_1_usd, last_1_eur
):
    print(
        "\nВыберите валюту для просмотра истории операций \n1. USD\n2. EUR\n3. Вернуться в меню."
    )
    while True:
        try:
            choice_history = int(input("Ваш выбор: "))
            if choice_history < 0 or choice_history > 3:
                print("Ошибка! Выберите число (1-3)")
                continue
            elif choice_history == int(1):
                history_usd(usd_operation, conversion_usd, last_1_usd)
                break
            elif choice_history == int(2):
                history_eur(eur_operation, conversion_eur, last_1_eur)
                break
            elif choice_history == 3:
                menu(
                    usd_operation,
                    conversion_usd,
                    eur_operation,
                    conversion_eur,
                    last_1_usd,
                    last_1_eur,
                )
        except ValueError:
            print("Ошибка! Нужно ввести число.")
            continue
    return (
        usd_operation,
        conversion_usd,
        eur_operation,
        conversion_eur,
        last_1_usd,
        last_1_eur,
    )


def menu(
    usd_operation, conversion_usd, eur_operation, conversion_eur, last_1_usd, last_1_eur
):
    print(
        "\n1. Конвертировать в USD\n2. Конвертировать в EUR\n3. Показать историю конвертаций\n4. Выход"
    )
    while True:
        try:
            choice = int(input("Выберите действие (1-4): "))
            if choice < 0 or choice > 4:
                print("\nВыберите число от 1 до 4")
                continue
            if choice == 1:
                def_conversion_usd(
                    usd_operation,
                    conversion_usd,
                    eur_operation,
                    conversion_eur,
                )
                break
            if choice == 2:
                def_conversion_eur(
                    usd_operation,
                    conversion_usd,
                    eur_operation,
                    conversion_eur,
                )
                break
            if choice == 3:
                history(
                    usd_operation,
                    conversion_usd,
                    eur_operation,
                    conversion_eur,
                    last_1_usd,
                    last_1_eur,
                )
                break
            if choice == 4:
                print("Всего доброго! Будем Вас ждать!")
                exit()
        except ValueError:
            print("Ошибка! Нужно ввести число.")
    return (
        usd_operation,
        conversion_usd,
        eur_operation,
        conversion_eur,
        last_1_usd,
        last_1_eur,
    )


print("Добрый день! Добро пожаловать в конвертор валют")
menu(
    usd_operation, conversion_usd, eur_operation, conversion_eur, last_1_usd, last_1_eur
)
