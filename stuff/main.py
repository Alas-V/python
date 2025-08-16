import locale
import datetime


try:
    user_locale = locale.getlocale()
    locale.setlocale(locale.LC_TIME, user_locale)
except (locale.Error, ValueError):
    locale.setlocale(locale.LC_TIME, "")


sample_time = datetime.datetime.now().strftime("%X")
uses_12h = "AM" in sample_time or "PM" in sample_time


name = input("enter your name pls: ").lower()
name_capitalize = name.capitalize()


current_time = datetime.datetime.now()
if uses_12h:
    formatted_time = current_time.strftime("%I:%M %p")
else:
    formatted_time = current_time.strftime("%H:%M")

if name.endswith("s"):
    possessive = name_capitalize + "'"
else:
    possessive = name_capitalize + "'s"


def greet():
    print("Hello there", name_capitalize)
    print("What a nice day. Do you want to do something today?")
    print(
        "Here I made for you some of the new news of",
        possessive,
        "photos on the " + formatted_time,
    )


greet()
