# def update_car_info(**car):
#    car["is_available"] = True
#    return car


# print(update_car_info(brand="BMW", price="$15000"))

# first_set = {1, 6, "Yes"}
# second_set = {1, False, "No"}
# print(first_set)

# print(first_set == second_set)

# second_set_2 = first_set.copy()

# print(first_set is second_set_2)


# print(1 in first_set, 1 in second_set, 6 in first_set)

# print(first_set, second_set, second_set_2)


# e = float(0.1)
# print(bool(e))


# my_list = [1, 23]
# my_second = ["d", "b"]

# print(len(my_list) < 0 or len(my_second) < 0)

# my_dict = {"price": 1500, "brand": "BMW"}
# my_second = {"brand": "BMW", "price": 1500}

# if my_dict == my_second:
#     print("Dictionaries are equal")

# if my_dict != my_second:
#     print("This is a bullshit")

# user_name = "jane"


# def greeting(greet):
#     return lambda name, time: f"{greet}, {name}! Time right now is {time}"


# morning_greeting = greeting("Good morning")


# print(morning_greeting(user_name.capitalize(), "10:00"))

# evening_greeting = greeting("Good evening")

# print(evening_greeting(user_name.capitalize(), "21:00"))


# def image_info(**image):
#     if ("image_title" not in image) or ("image_id" not in image):
#         raise TypeError("Error! Image has no title or ID")
#     return f"Image {image['image_title']} has id -  {image['image_id']}"


# photo = {
#     "image_title": "Cat",
#     "image_id": int(255),
#     "image_size": int(112),
# }


# try:
#     print(image_info(**photo))
# except Exception as e:
#     print(e)


# points = 100

# if points > 90:
#     print("Great")
# elif points > 80:
#     print("Good")
# elif points > 50:
#     print("Bad")

# route_stuff_user_1 = {
#     "distance": 1000,
# }
# route_stuff_user_2 = {
#     "speed": 20,
#     "time": 10,
# }
# route_stuff_user_3 = {
#     "place": "Paris",
#     "time": 20,
# }


# def route_info(**my_dict):
#     if ("distance" in my_dict) and isinstance(my_dict.get("distance"), int):
#         print(f"Distance to your destination is", my_dict["distance"], "km")
#     elif my_dict.get("speed") and my_dict.get("time"):
#         print(
#             f"Distance to your destination is", my_dict["speed"] * my_dict["time"], "km"
#         )
#     else:
#         print("No distance Data available")


# route_info(**route_stuff_user_1)
# route_info(**route_stuff_user_2)
# route_info(**route_stuff_user_3)


# string = "I am going to apply for a good job finally and get a nice payment"

# print("String is short") if len(string) < 70 else print("String is long")


# def dict_to_list(**my_dict):
#     list_for_shit = []
#     for key, value_num in my_dict.items():
#         if type(value_num) == int:
#             value_num *= 2
#         list_for_shit.append((key, value_num))
#     return list_for_shit


# number_dict = {
#     "First": 12,
#     "Second": 9,
#     "Last": True,
# }

# print(dict_to_list(**number_dict))


# def filter_list(list, peyt):
#     list_end = []
#     for objects in list:
#         if type(objects) == peyt:
#             list_end.append(objects)
#     return list_end


# my_listss = [12, True, "Last", 26, 24.65, "False shit", "yes", False]

# print(filter_list(my_listss, bool))

# while True:
#     number_one = float(input("Введите первое число: "))
#     number_two = float(input("Введите второе число: "))
#     print(number_one / number_two)
#     next_yes_no = str(input("Хотите продолжить ? (Yes/No) ")).lower()
#     if next_yes_no == "yes":
#         continue
#     elif next_yes_no == "no":
#         break

# my_didicus = {
#     "bre": "bre",
#     "be": "dicus",
#     "de": "dicus",
# }

# big_didicus = {k: v.upper() for k, v in my_didicus.items()}

# print(big_didicus)

# my_list_of_didicus = ["bre", "bre", "be dicus", "be bricus be dicus"]

# list_of_over_three_didicus = [value for value in my_list_of_didicus if len(value) > 3]

# print(list_of_over_three_didicus)
# import datetime

# note_time = datetime.datetime.now().strftime("%H:%M - %d/%m/%Y")
# print(note_time)


# note_value = input("\nPlease, enter your note: ")
#     data["name"][note_name] = note_value
#     with open("notes.json", "w") as json_file:
#         json.dump(data, json_file, indent=4)
#     data["log"]["added"][note_name] = f"Added at {note_time}"
#     with open("notes.json", "w") as json_file:
#         json.dump(data, json_file, indent=4)


name_of_notes = list(data["name"].keys())
        print("\nNo notes was found")
        menu()
    print("\nYour notes")
    for i, name in enumerate(name_of_notes, 1):
        print(f"{i}. {name}")