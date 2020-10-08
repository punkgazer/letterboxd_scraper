
from session import SESSION, MAIN_URL
from util import make_soup
import re

class ObscureFilmRating():
    def __init__(self, film="reptisaurus"):
        self.film = film

    @property
    def rating(self):
        """ Scrapes the user's Letterboxd profile to get the 
        number of times they have rated a film each score between 0.5 and 5.0
        Returns a dict of each score and the corresponding the user has rated that score.
        r-type: dict. """

        
        full_url = f"{MAIN_URL}csi/film/{self.film}/rating-histogram/"
        request = SESSION.get(full_url)
        soup = make_soup(request)

        print(soup.prettify())
        quit()
        
        token = SESSION.cookies['com.xk72.webparts.csrf']
        cookie_params = {'__csrf': token}

        full_url = f'{MAIN_URL}film/{self.film}/'

        request = SESSION.post(full_url, data=cookie_params)
        soup = make_soup(request)

        print(soup.prettify())
        quit()

        ratings_section = soup.find('div', class_=['rating-histogram clear rating-histogram-exploded']).find('ul')

        """ There are 10 li tags, 1 for each score 0.5 -> 5
        Within these li tags, there is a link provided that the user has rated >1 film with that rating. """
        ratings_data = [i.find('a') for i in ratings_section.find_all('li', class_='rating-histogram-bar')]
        if len(ratings_data) != 10:
            raise ValueError("Number of possible rating scores should be 10, not", len(ratings_data))

        """ This link has an attribute 'title', at the start of which is the value for the number 
        of times the user has rated a movie that score. """
        score_count_pattern = r"\d+"
        get_quantity = lambda x: int(re.findall(score_count_pattern, x.get('title'))[0]) if x else 0
        score_quantities = [get_quantity(i) for i in ratings_data]

        # {0.5: 44, 1.0: 108... 5.0: 91}
        return {(score+1)/2: quantity for score, quantity in enumerate(score_quantities)}

    @property
    def total_ratings(self):
        """ Returns the total number of ratings. 
        NOTE: this should align with number on the user's profile. Though it is taken from reading
        the histogram data collected from self.ratings
        r-type: int """
        return sum(self.rating.values())

    @property
    def avg_rating(self, round_to=2):
        """ Computes the average of the ratings collected in self.ratings.
        r-type: float """
        pre_rounded_score = sum([s*q for s,q in self.rating.items()])/self.total_ratings
        return round(pre_rounded_score, round_to)

    @property
    def friends_rating(self):
        pass


if __name__ == "__main__":
    film = ObscureFilmRating()
    print(f"Rating: {film.rating}")
    print("-"*40)
    print(f"Total Ratings: {film.total_ratings}")
    print("-"*40)
    print(f"Avg Rating: {film.avg_rating}")