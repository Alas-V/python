import json
import datetime


def current_time():
    datetime.datetime.now().strftime("%H:%M - %d/%m/%Y")


def menu():
    while True:
        print("\n1. Add note.\n2. Find note\n3. Exit")
        try:
            choice = int(input("\nYour choice (1-3): "))
            if choice == 109:
                log_menu()
                break
            elif choice < 1 or choice > 3:
                print("\nError! Please enter a valid value (1-3)")
                continue
            elif choice == 1:
                add_note()
                break
            elif choice == 2:
                find_note()
                break
            elif choice == 3:
                exit()
        except ValueError:
            print("\nError! Please enter a valid value (1-3)")
            continue


def add_note():
    note_name = input("\nPLease, enter the note name: ")
    json_for_read = open_json_for_read()
    if note_name in json_for_read["name"]:
        print("\nNote with this name already exist")
        while True:
            try:
                exist_choice = input(
                    f"\nDo you want to open {note_name} note? (Yes/No)"
                )
                if exist_choice.lower() == "yes" or exist_choice.lower() == "y":
                    open_note(note_name)
                    break
                elif exist_choice.lower() == "no" or exist_choice.lower() == "n":
                    add_note()
                    break
            except ValueError:
                print("\nError! Please choose the correct answer (Yes/no)")
                continue
    note_value = input("\nPlease, enter your note: ")
    json_for_read["name"][note_name] = note_value
    dump_json_file(json_for_read)
    time_now = current_time()
    json_for_read["log"]["added"][note_name] = f"Added at {time_now}"
    dump_json_file(json_for_read)
    while True:
        print("\nNote added.\n1.Add another one note\n2.All notes\n3.Menu\n4.Exit")
        try:
            added_choice = int(input("\nEnter your choice (1-4):"))
            if added_choice < 0 or added_choice > 4:
                print("\nError. Please enter the valid choice (1-4)")
                continue
            elif added_choice == 1:
                add_note()
                break
            elif added_choice == 2:
                find_note()
                break
            elif added_choice == 3:
                return
            elif added_choice == 4:
                exit()
                break
        except Exception:
            print("\nError. Please enter the valid choice (1-4)")
            continue


def find_note():
    data = open_json_for_read()
    name_of_notes = list(data["name"].keys())
    if not name_of_notes:
        print("\nNo notes was found")
        menu()
    print("\nYour notes")
    for i, name in enumerate(name_of_notes, 1):
        print(f"{i}. {name}")
    while True:
        try:
            choice_note = int(input(f"Chose the note you want to open (1-{i}): "))
            if choice_note < 1 or choice_note > len(name_of_notes):
                print(f"\nError, please enter the valid answer: (1-{i})")
                continue
            if 1 <= choice_note <= len(name_of_notes):
                selected_note = name_of_notes[choice_note - 1]
                open_note(selected_note)
                break
        except ValueError:
            print(f"\nError. You must choose (1-{i})")


def open_note(name):
    data = open_json_for_read()
    print(f"\nSelected note: {name}")
    print("Content:", data["name"][name])
    print("\n1.Edit note\n2.Delete note\n3.Menu\n4.Exit")
    while True:
        try:
            first_choice = int(input("\nPlease choose the action (1-4): "))
            if first_choice < 0 or first_choice > 4:
                print("\nError. Please choose the valid answer (1-4)")
                continue
            elif first_choice == 1:
                edit_existed_note(name)
                break
            elif first_choice == 2:
                while True:
                    try:
                        second_choice = input(
                            "\nAre you sure you want to delete the note (Yes/No):"
                        )
                        if second_choice.lower() == "yes" or second_choice == "y":
                            if name in data["log"]["added"].items():
                                del data["log"]["added"][name]
                            del data["name"][name]
                            print("\nNote deleted")
                            time_now = current_time()
                            data["log"]["deleted"][name] = f"Deleted at {time_now}"
                            with open("notes.json", "w") as json_file:
                                json.dump(data, json_file, indent=4)
                            menu()
                            break
                        elif (
                            second_choice.lower() == "no"
                            or second_choice.lower() == "n"
                        ):
                            open_note(name)
                            break
                    except ValueError:
                        print("\nError. PLease enter the valid choice (Yes/No)")
                    continue
            elif first_choice == 3:
                menu()
                break
            elif first_choice == 4:
                exit()
                break
        except ValueError:
            print("\nError. Please enter the valid choice (1-4)")
            continue


def edit_existed_note(name):
    editing_note = input("Enter the new note content: ")
    data = open_json_for_read()
    data["name"][name] = editing_note
    dump_json_file(data)
    time_now = current_time()
    data["log"]["edited"][name] = f"Note was edit las time at {time_now}"
    dump_json_file(data)
    print("\nNote was successfully edited!")
    open_note(name)


def log_menu():
    print("\n\nWelcome to the log menu.\n1.Open the logs.\n2.Main menu\n3.Exit")
    log_choice = int(input("\nWhat do you want to do? (1-3): "))
    while True:
        try:
            if log_choice < 0 or log_choice > 3:
                print("\nError! You must enter number (1-3)")
            elif log_choice == 1:
                which_log()
                break
            elif log_choice == 2:
                menu()
                break
            elif log_choice == 3:
                exit()
                break
        except ValueError:
            print("\nError! You must enter number (1-3)")
            continue


def which_log():
    print(
        "\nAccessible logs info\n1.Notes adding logs\n2.Notes editing logs\n3.Notes deleting logs\n4.Back"
    )
    while True:
        try:
            which_choice = int(input("\nPlease, select a menu section (1-4): "))
            data = open_json_for_read()
            if which_choice < 0 or which_choice > 4:
                print("\nError! You must select number (1-4)")
                continue
            elif which_choice == 1:
                logs = "added"
                work_with_logs(data, logs)
                break
            elif which_choice == 2:
                logs = "edited"
                work_with_logs(data, logs)
                break
            elif which_choice == 3:
                logs = "deleted"
                work_with_logs(data, logs)
                break
            elif which_choice == 4:
                log_menu()
                break
        except ValueError:
            print("\nError! You must select number (1-4)")
            continue


def work_with_logs(data, logs):
    data_logs = data["log"][logs]
    if not data_logs.items():
        print("\nNo logs was found")
        which_log()
    for name, time in data_logs.items():
        print(f"{name} - {time}")
    print(f"\n1.Delete {logs} notes logs\n2.Back\n3.Main menu")
    while True:
        try:
            choice_inside_log = int(input("\nChoose the action (1-3): "))
            if choice_inside_log < 0 or choice_inside_log > 3:
                print("\nError! You must choose number (1-3)")
                continue
            elif choice_inside_log == 1:
                data["log"][logs] = {}
                dump_json_file(data)
                print("\nLogs deleted.")
                which_log()
                break
            elif choice_inside_log == 2:
                which_log()
                break
            elif choice_inside_log == 3:
                return
        except ValueError:
            print("\nError! You must choose number (1-3)")


def open_json_for_read():
    with open("notes.json", "r") as json_for_read:
        data = json.load(json_for_read)
    return data


def dump_json_file(data):
    with open("notes.json", "w") as json_file:
        json.dump(data, json_file, indent=4)


menu()
