class building:
    year = None
    city = None

    def __init__(self, year, city):
        self.year = year
        self.city = city


def get_data(self):
    print("Year: ", self.year, "In the city of: ", self.city)


class school(building):
    pupils = 0

    def __init__(self, pupils, year, city):
        super(school, self).__init__(year, city)
        self.pupils = pupils


VNG = school(1532, 1996, "Novosibirsk")

get_data(VNG)
