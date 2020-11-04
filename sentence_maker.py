
# Imports
import re
from tqdm import tqdm
from collections import Counter
from operator import attrgetter

# Local imports
from session import SESSION, make_soup
from util import remove_full_stops


class FilmResult():
    
    def __init__(self, search_result, word):
        title = search_result.get('data-film-name')
        self.title = title.lower() if title else ''
        self.film_id = int(search_result.get('data-film-id'))
        self.div_classes = search_result.get('class')

        self.score = self.__get_score(word)

    def __bool__(self):
        return bool(self.score)

    @property
    def blank_poster(self):
        """ Returns True if the film does not have a poster, else False """
        return "no-poster" in self.div_classes

    def contains_word(self, word):
        if self.is_word: return True
        return f"{word} " in self.title

    def is_word(self, word):
        return word == self.title

    def __get_score(self, word):

        if not all([self.title, self.film_id]):
            return 0
        if not self.contains_word(word):
            return 0

        score = 3
        if not self.is_word(word):
            score -= 3 # was 2
        if self.blank_poster:
            score -= 1
        return score


class SentenceMaker():
    """ Builds a list based on sentence input. """

    def __init__(self, sentence):

        self.sentence = sentence
        self.__get_words()

    def __get_words(self):
        """ Convert the sentence into individual words. """
        sentence = self.sentence 

        # -- Attempt to ensure that sentence is of correct format ---
        sentence = remove_full_stops(sentence)
        unknown_chrs = "|".join(set([c for c in sentence if not any( [c.isalpha(), c.isnumeric(), c in (' ', '.')] )]))

        # If any unknown characters, remove them. This avoids errors in the URL
        if unknown_chrs:
            sentence = re.sub(unknown_chrs, " ", sentence)
            sentence = re.sub(" +", " ", sentence).strip()

        sentence = sentence.lower()

        self.words = sentence.split()

    def get_match(self, word, index=0):
        """ Get a full page of film results from searching a given word on Letterboxd.
        For example, searching for the word 'market' results in a series of films with
        market in their title (usually, sometimes the word is not in the title, but generally)
        
        word type: str
        
        r-type: int (if match found, otherwise False) """

        # Make search request for word
        suburl = f"search/{word}/"
        request = SESSION.request("GET", suburl)
        soup = make_soup(request)

        # Get film results in soup
        search_results = soup.find('ul', class_='results')
        divs = search_results.find_all('div', class_=["react-component", "film-poster"])

        # Make instances to determine how good of a match each result is
        results = [FilmResult(div, word) for div in divs]
        sorted_results = sorted(results, key=attrgetter('score'), reverse=True)

        best_match = None
        while sorted_results:
            if index:
                index -= 1
                sorted_results.pop(0)
                continue

            best_match = sorted_results.pop(0)
            break

        # If no suitable matches
        if not best_match.score:
            return None, word
        # Otherwise get the match's film_id
        else:
            return best_match.film_id, word

    def replacement(self, word):
        return input(f"Enter replacement {word} (or leave blank to omit)\n")

    def __call__(self):
        """ Conducts the search for each word in self.sentence. """
        matches = []
        counter = Counter()
        for word in self.words:
            if word not in counter:
                counter[word] = 1
            else:
                counter[word] += 1
            
            match = self.get_match(word, counter[word]-1)
            matches.append(match)

        while not all([match for match, _ in matches]):
            
            # Ask user for replacement word for any that were not found
            matches = [(match, word) if match else (None, self.replacement(word)) for (match, word) in matches]

            # If the user entered an empty string rather than a replacement word
            # Simply remove it from the list
            while '' in matches:
                matches.remove('')

            matches = [(match, word) if match else self.get_match(word) for (match, word) in matches]

        return [{"filmId": film_id} for film_id, _ in matches]


if __name__ == "__main__":
    S = SentenceMaker("Whale you are a great friend. Hope you have a good birthday, lots of love, loser")
            
        

    

        
        






    

