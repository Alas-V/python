import json

with open("work.json", "r") as json_file:
    using_json = json.load(json_file)

print(using_json["key_dict"]["key_in_dict"])

note_name = "random"
note_value = "yea, some random shit"


using_json["notes"] = [{note_name: note_value}]


with open("work.json", "w") as json_file:
    json.dump(using_json, json_file, indent=4)
