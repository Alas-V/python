import webbrowser


def validator(func):
    def wrapper(url):
        if "https://" in url:
            func(url)
            print("Tank me later")
        else:
            print("This is not even a link")

    return wrapper


@validator
def open_url(url):
    webbrowser.open(url)


open_url("https://t.me/sentrybuster")
