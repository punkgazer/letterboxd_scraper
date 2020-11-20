# LetterBoxd-Scraper


### NOTE:
I am inexperienced with programming. This is my second several hundred line project, 
so apologies that it is extremely unclear how to use this program. I hope to work on that over time.

## What is possible thus far
Disclaimer that the following have far from extensively been tested. 

### Users
- Get the following or followers of a given user
- Traverse the watched page of a given user in order to get the film_ids
    for a given set of criteria, or the entire watchlist
- Given a film, get the users who've rated it x/10 (some limitations)

### Films
- Get attributes of individual film (e.g. year, rating)
- Search for film_ids based on genre/year criteria
- Determine if a film is obscure (too few ratings to be awarded a score by Letterboxd)

### Lists
- Create a list
- Delete a list
- Modify a list's attribites
- Merge two or more lists together
- Remove list_ids from a list if they appear in another
- Comment on someone else's list
- Delete a comment on your list


## What may be possible in the future

### Films
- IMPORTANT: get a film's name based on its id (by method of creating a temporary list)

### Lists
- Updating at the same time as commenting information about the added/removed films

### Just for fun
- Sentence maker: creates a list based on a given sentence 
(I had this working sort of, but it broke during refactoring and has been low priority to fix)