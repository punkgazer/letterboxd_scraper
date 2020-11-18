import json

# Lists with common applications
yes_list = ['y', 'yes', 'yeah', 'confirm']
no_list = ['n', 'no', 'back', 'cancel']
quit_list = ['q', 'quit', 'exit', 'quit()', 'exit()', 'cls']

def load_json_data(file_name):
    """ Loads the data from a json file, returns it.
    r-type: dict 
    """
    with open(f"data/{file_name}.json") as jf:
        content = json.load(jf)
    return content

def yn(msg=None):
    """ While user's response is not in no/yes list, keeps prompting
    if in yes_list -> True
    elif in no_list -> False. """
    pre_string = "y/n:\n> "
    string = f"{msg} {pre_string}" if msg else pre_string
    while True:
        user_response = input(string)
        if user_response in quit_list:
            quit()
        elif user_response in yes_list:
            return True
        elif user_response in no_list:
            return False
        print("Sorry, I didn't understand your response!")

def replace_dict(a, b):
    """ Replace the values of keys in A, where those keys 
    also appears in B. """
    changed_keys = set(a.keys()) & set(b.keys())
    return {k:v if k not in changed_keys else b[k] for k,v in a.items()}

def merge_lists(*args):
    """ Merge two or more lists together. """
    # Edge cases
    if not all([isinstance(i, list) for i in args]):
        raise TypeError("All arguments must be lists")
    
    if not args:
        raise Exception(f"No arguments provided")
    elif len(args) == 1:
        return args[0]
    
    result = []
    [[result.append(i) for i in j] for j in args]
    return result

def merge_entries(*args):
    # Edge cases
    if not all([isinstance(i, list) for i in args]):
        raise TypeError("All arguments must be lists")
    if not args:
        raise Exception("No arguments provided")

    results = []
    [[results.append( {k:v for k,v in entry.items() if k=="filmId"} ) for entry in entries] for entries in args]

    unique_film_ids = set([i['filmId'] for i in results])
    return [{"filmId": x} for x in unique_film_ids]
    
if __name__ == "__main__":
    x = merge_entries(
        [{'filmId': 200, 'a': 5}, {'filmId': 201}, {'filmId': 204}],
        [{'filmId': 120}, {'filmId': 125}, {'filmId': 204}]
    )
    print(x)
