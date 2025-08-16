my_dict = {
    "a": 34,
    "b": 66,
    "c": 1,
    "d": 9000,
}


def two_biggest(dict):
    sorted_dict = sorted(dict.values(), reverse=True)
    return (
        next(key for key, val in dict.items() if val == sorted_dict[0]),
        next(key for key, val in dict.items() if val == sorted_dict[1]),
    )


print(two_biggest(my_dict))
