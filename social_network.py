# BUG
# Problem: Last page for watched is 256 - cannot go past that.


# Imports
import re
from numpy import mean

# Local Imports
from session import SESSION, make_soup


def __get_people(soup):
    """ Scrapes the profile links (original usernames) of all people on a given person's followers/following page. """
    return [person.find('a').get('href').replace('/', '') for person in soup.find_all("td", class_="table-person")]

def get_following(username=SESSION.username):
    """ Returns a list of the users a given user follows. """
    request = SESSION.request("GET", f"{username}/following/")
    soup = make_soup(request)
    return __get_people(soup)

def get_followers(username=SESSION.username):
    """ Returns a list of the users a given user is followed by. """
    request = SESSION.request("GET", f"{username}/followers/")
    soup = make_soup(request)
    return __get_people(soup)

def get_blocked():
    """ Returns a list of the users in your block list.
    NOTE: You can only see who you've blocked, hence there is no
    username argument for this function unlike following and followers. """
    username = SESSION.username
    request = SESSION.request("GET", f"{username}/blocked/")
    soup = make_soup(request)
    return __get_people(soup)
    
    
class FilmRaters():
    """ Given a film name and optional min/max rating, returns all the
    raters of that film. You can also provide a limit for number
    of pages to scrape. 
    NOTE: there are 25 users on a full page. """

    def __init__(self, film, rating_range=(None, None), limit=None):
        min_rating, max_rating = rating_range

        ## Award default values
        if not min_rating: min_rating = 0.5
        if not max_rating: max_rating = 5

        ## Edge cases
        if min_rating > max_rating:
            raise Exception("Min rating must be less than max rating!")
        rating_range = tuple([int(i*2) for i in (min_rating, max_rating)])
        if any([r not in range(1,11) for r in rating_range]):
            raise Exception("Min/Max values must be within inclusive range 0.5 to 5")

        self.film = film
        self.min_rating, self.max_rating = rating_range
        self.limit = limit

    @property
    def sort_by(self):
        """ The method by which the page should be sorted: 
        either by rating or by revese-rating. 
        The latter is used if it would be more efficient to start from the bottom due to 
        the min_rating being lower than the max_rating is high. """
        average = mean([self.min_rating, self.max_rating])
        if average < 5.5:
            return "lowest"
        return "highest"

    @property
    def suburl_part(self):
        """ Returns the main part of the suburl, without the page_number,
        which is calculated elsewhere. """
        string = f"film/{self.film}/members/by/member-rating"
        if self.sort_by == "lowest":
            string += "-lowest"
        return string + '/'

    def __get_first_result(self, page_num):
        print(f"Attempting to get first result for page {page_num}")
        
        for i in self.scrape_page(page_num):
            print(i)

        return self.scrape_page(page_num).__next__()[1]

    def build_url(self):
        pass

    @property
    def first_page(self):
        """ Locate the page from which to start the scraping process. """
        start, end = self.min_rating, self.max_rating

        page_num = 1
        change_page_num = None

        # Going forward through pages, doubling each time until
        # finds a result in the acceptable range (between self.min_rating and self.max_rating)
        while True:
            first_rating = self.__get_first_result(page_num)
            if first_rating > end:
                print(first_rating, end)
                # The first result is already greater than the end
                return None
            elif first_rating in range(start, end+1):
                # The first result is in the range we're interested in
                break

            # first_rating < start
            # In other words, we haven't reached a rating within the range yet
            change_page_num = 1 if not change_page_num else change_page_num * 2
            page_num += change_page_num
            
        # There is no result before page 1, 
        # so we know that's our true starting point
        if page_num == 1: return page_num

        change_page_num //= 2
        found = False
        while not found:

            if first_rating > end:
                if change_page_num == 1:
                    # This avoids never-ending loop
                    return page_num - 1
                # Needs to decrement
                page_num -= change_page_num

            elif first_rating in range(start, end+1):
                # Needs to decrement
                page_num -= change_page_num

            elif first_rating < start:
                # Needs to increment
                page_num += change_page_num
           
            change_page_num //= 2
            first_rating = self.__get_first_result(page_num)

    @staticmethod
    def get_person(tr):
        return tr.find('td').find('a').get('href').replace('/', '')

    @staticmethod
    def get_rating(tr):
        rating = tr.find_all('td')[1].find('span', class_=re.compile(r"rating rated-\d{1,2}"))
        class_ = rating.get('class')
        if len(class_) != 2:
            raise Exception("Unexpected result for class_:", class_)

        pattern = r"rated-(\d{1,2})"
        try:
            return int(re.findall(pattern, class_[1])[0])
        except:
            raise Exception("Could not extract rating from class_", class_)

    def scrape_page(self, page_num):
        """ Scrape an indvidual page of the search,
        grabbing every result within ratings range. """
        suburl = f"{self.suburl_part}page/{page_num}/"
        request = SESSION.request("GET", suburl)
        soup = make_soup(request)

        table_rows = soup.find('table', class_=['person-table', 'film-table']).find_all('tr')

        for tr in table_rows[1:]:
            if not (rating := self.get_rating(tr)):
                continue
            person = self.get_person(tr)
            yield (person, rating)




if __name__ == "__main__":
    
    f = FilmRaters(
        film="the-happening",
        rating_range=(1.5, 3),
        limit=3
        )

    print(f.first_page)

#     def page_locate():
        
#         # Start from the first page
#         page_num = 1
#         increase = 1

#         while True:
#             # Make request
#             suburl = suburl_part + f"page/{page_num}/"
#             request = SESSION.request("GET", suburl)
#             soup = make_soup(request)
#             _, result = __get_review_rating(soup).__next__
#             if result == 3:


# # if mean(min_rating, max_rating) < 4.25: sort_by += "-lowest"




                



                





            


            

        


        


    
    