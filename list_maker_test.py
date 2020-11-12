import unittest
import list_maker

class TestCalc(unittest.TestCase):

    my_list_name = "Bad Movie Watchlist (1000+)"

    def test_get_names(self):
        """ 
        Test of the list_maker.get_names_of_entries() func
        In other words, that a list of film_ids can be used to get the respective list_names
        
        The function should return a dict:
        {2943: 'film_name'} where 2943 is the film_id
        """
        film_dict = list_maker.get_names_of_entries([464637, 148319, 363298, 364249, 456634, 65519])

        self.assertEqual(
            film_dict,
            {
            464637: 'Romina', 
            148319: "I'm in Love with a Church Girl", 
            363298: 'The Hurricane Heist', 
            364249: 'The Perfect Stalker', 
            456634: 'The Silence', 
            65519: '11/11/11'
            }
        )

    def test_load_list(self):
        """ Test that an existing LetterboxdList can be loaded into memory so that
        it can subsequently be modified. """
        self.my_list = list_maker.LetterboxdList(self.my_list_name)

    def test_update_list(self):
        """ Update the values of a list
        e.g. change the description. """
        self.my_list.update(public=False)
        self.my_list.update(ranked=True)

    def test_update_entries(self):
        """ Update a list specifically with new_entries. 
        NOTE: The update_entries() method of the Letterboxd class
        also has the option to display changes as a comment.
        This is also tested.
        """
        pass



if __name__ == "__main__":
    unittest.main()