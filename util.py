from bs4 import BeautifulSoup as bs

def make_soup(request):
    return bs(request.text, 'lxml')