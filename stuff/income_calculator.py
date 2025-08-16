incomes_history = {}
incomes_value_list = []
incomes_names_list = []
expenses_names_list = []
expenses_value_list = []
expenses_history = {}


def menu():
    print(
        "\n1. Добавить доход.\n2. Добавить расход.\n3. Показать статистику.\n4. Выход."
    )
    while True:
        try:
            menu_choice = int(input("Выш выбор (1-4): "))
            if menu_choice < 0 or menu_choice > 4:
                print("\nОшибка! Выберите число (1-4): ")
                continue
            if menu_choice == 1:
                add_income()
                break
            if menu_choice == 2:
                add_expenses()
                break
            if menu_choice == 3:
                show_statistic()
                break
            if menu_choice == 4:
                exit()
                break
        except ValueError:
            print("\nОшибка! Выберите число (1-4): ")


def add_income():
    print("\nДобавление статьи дохода")
    category = input("Категория дохода: ").lower().capitalize()
    incomes_names_list.append(category)
    while True:
        try:
            income_value = int(input("Сумма дохода: "))
            if income_value < 0:
                print("Доход не может быть отрицательным")
                continue
            if income_value > 0:
                incomes_history[category] = income_value
                incomes_value_list.append(income_value)
                print(
                    "\nДоход успешно добавлен.\n1. Добавит новый доход.\n2. Вернуться в меню.\n3. Выход."
                )
                while True:
                    try:
                        income_menu_or_exit_choice = int(input("Выберите действие: "))
                        if (
                            income_menu_or_exit_choice < 0
                            or income_menu_or_exit_choice > 3
                        ):
                            print("Ошибка! Выберите корректное значение (1-3): ")
                            continue
                        if income_menu_or_exit_choice == 1:
                            add_income()
                            break
                        if income_menu_or_exit_choice == 2:
                            menu()
                            break
                        if income_menu_or_exit_choice == 3:
                            exit()
                            break
                    except ValueError:
                        print("Ошибка! Выберите действие (1-3)")
                        continue
                break
        except ValueError:
            print("Введите корректное значение дохода")
            continue


def add_expenses():
    print("\nДобавление статьи расхода")
    category = input("Категория расхода: ").lower().capitalize()
    expenses_names_list.append(category)
    while True:
        try:
            expenses_value = int(input("Сумма расхода: "))
            if expenses_value < 0:
                print("Расход не может быть отрицательным")
                continue
            if expenses_value > 0:
                expenses_history[category] = expenses_value
                expenses_value_list.append(expenses_value)
                print(
                    "\nРасход успешно добавлен.\n1. Добавит новый расход.\n2. Вернуться в меню.\n3. Выход."
                )
                while True:
                    try:
                        expenses_menu_or_exit_choice = int(input("Выберите действие: "))
                        if (
                            expenses_menu_or_exit_choice < 0
                            or expenses_menu_or_exit_choice > 3
                        ):
                            print("Ошибка! Выберите корректное значение (1-3): ")
                            continue
                        if expenses_menu_or_exit_choice == 1:
                            add_expenses()
                            break
                        if expenses_menu_or_exit_choice == 2:
                            menu()
                            break
                        if expenses_menu_or_exit_choice == 3:
                            exit()
                            break
                    except ValueError:
                        print("Ошибка! Выберите действие (1-3)")
                        continue
                break
        except ValueError:
            print("Введите корректное значение дохода")
            continue


def def_incomes_history():
    total = sum(incomes_value_list)
    for name, value in incomes_history.items():
        print(f"{name} - {value} руб.")
    print("\nСумма доходов - ", total)
    while True:
        try:
            print("\n1. Назад.\n2. Меню")
            income_history_choice = int(input("Выберите действие: "))
            if income_history_choice < 0 or income_history_choice > 2:
                print("Введите число(1-2)")
            if income_history_choice == 1:
                show_statistic()
                break
            if income_history_choice == 2:
                menu()
                break
        except ValueError:
            print("Ошибка! Выберите действие (1-2)")
            continue


def def_expenses_history():
    total = sum(expenses_value_list)
    for name, value in expenses_history.items():
        print(f"{name} - {value} руб.")
    print("\nСумма расходов - ", total)
    while True:
        try:
            print("\n1. Назад.\n2. Меню")
            expenses_history_choice = int(input("Выберите действие: "))
            if expenses_history_choice < 0 or expenses_history_choice > 2:
                print("Введите число(1-2)")
            if expenses_history_choice == 1:
                show_statistic()
                break
            if expenses_history_choice == 2:
                menu()
                break
        except ValueError:
            print("Ошибка! Выберите действие (1-2)")
            continue


def balance():
    total_income = sum(incomes_value_list)
    total_expenses = sum(expenses_value_list)
    print("\nБаланс")
    print("\nДоходы - ", total_income, "руб.")
    print("Расходы - ", total_expenses, "руб.")
    print("\nОстаток средств - ", total_income - total_expenses, "руб.")
    print("\n1. Меню.\n2. Выход")
    while True:
        try:
            balance_choice = int(input("\nВыберите действие (1-2)"))
            if balance_choice < 0 or balance_choice > 2:
                print("Ошибка! Выберите число (1-2)")
                continue
            if balance_choice == 1:
                menu()
                break
            if balance_choice == 2:
                exit()
                break
        except ValueError:
            print("Ошибка! Введите корректное значение.")
            continue


def show_statistic():
    print(
        "\n1. Показать доходы.\n2. Показать расходы.\n3. Показать остаток средств.\n4. Вернуться в меню."
    )
    while True:
        try:
            show_statistic_choice = int(input("Выбор действия: "))
            if show_statistic_choice < 0 or show_statistic_choice > 4:
                print("Ошибка! Выберите действие (1-4)")
                continue
            if show_statistic_choice == 1:
                def_incomes_history()
                break
            if show_statistic_choice == 2:
                def_expenses_history()
                break
            if show_statistic_choice == 3:
                balance()
                break
            if show_statistic_choice == 4:
                menu()
                break
        except ValueError:
            print("Ошибка! Выберите действие (1-4)")
            continue


menu()
