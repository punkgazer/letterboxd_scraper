
from session import SESSION, make_soup
import re

class FilmRating():


    def __init__(self, film_link):
        self.film_link = film_link
        self.__make_rating_soup()
        self.__check_if_obscure()

    def __make_rating_soup(self):
        """ Returns the rating soup for the film, from which ratings can be extracted. """
        suburl = f"csi/film/{self.film_link}/rating-histogram/"
        request = SESSION.request("GET", suburl)
        self.rating_soup = make_soup(request)

    def __check_if_obscure(self):
        """ Checks the ratings soup to ensure that the film does not have enough ratings
        to be given a standard rating - otherwise creating an instance of this class
        is pointless because grabbing the standard rating would be easier. """
        if not self.ratings:
            self.is_obscure = True
        else:
            self.is_obscure = bool(self.rating_soup.find('a', title=re.compile("Not enough ratings")))

    @property
    def ratings(self):
        """ Scrapes the user's Letterboxd profile to get the 
        number of times they have rated a film each score between 0.5 and 5.0
        Returns a dict of each score and the corresponding the user has rated that score.
        r-type: dict. """
        if not self.rating_soup.text:
            return None

        """ There are 10 li tags, 1 for each score 0.5 -> 5
        Within these li tags, there is a link provided that the user has rated >1 film with that rating. """
        ratings_data = [i.find('a') for i in self.rating_soup.find_all('li', class_='rating-histogram-bar')]
        if len(ratings_data) != 10:
            raise ValueError("Number of possible rating scores should be 10, not", len(ratings_data))
        
        """ This link has an attribute 'title', at the start of which is the value for the number 
        of times the user has rated a movie that score. """
        score_count_pattern = r"[\d,]+"
        get_quantity = lambda x: int(re.findall(score_count_pattern, x.get('title'))[0].replace(',', '')) if x else 0
        score_quantities = [get_quantity(i) for i in ratings_data]

        return {score+1: quantity for score, quantity in enumerate(score_quantities)} # {0.5: 44, 1.0: 108... 5.0: 91}

    @property
    def total_ratings(self, rating=None):
        """ Returns the total number of ratings. 
        NOTE: this should align with number on the user's profile. Though it is taken from reading
        the histogram data collected from self.ratings
        r-type: int """
        if not self.ratings:
            return 0
        return sum(self.ratings.values())

    @property
    def avg_rating(self, round_to=2):
        """ Computes the average of the ratings collected in self.ratings.
        r-type: float """
        if not self.ratings:
            return None
        pre_rounded_score = sum([s*q for s,q in self.ratings.items()])/self.total_ratings
        return round(pre_rounded_score, round_to)   


if __name__ == "__main__":

    my_film = FilmRating('black-swan')
    print(my_film.ratings)
    print(my_film.total_ratings)
    print(my_film.avg_rating)
    print(my_film.is_obscure)

    # print(f"\n{'-'*40}\n")

    # my_film = FilmRating('three-tales-of-terror')
    # print(my_film.ratings)
    # print(my_film.total_ratings)
    # print(my_film.avg_rating)
    # print(my_film.is_obscure)

    print(f"\n{'-'*40}\n")

    my_film = FilmRating('mortmain')
    print(my_film.ratings)
    print(my_film.total_ratings)
    print(my_film.avg_rating)
    print(my_film.is_obscure)
