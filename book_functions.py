import pandas as pd
import numpy as np
import re

# pip install rake-nltk  # run code if working in a new environment and getting errors on Rake()
from rake_nltk import Rake
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import string
from fuzzywuzzy import fuzz
from signin_config import *

# File is organized chronologically : scraping, processing, filtering, recommending



# Scraping functions

def get_urls():
    '''gets all the urls from GoodReads top ~200 books from years 1909 to 2019'''
    url = []
    for i in range(1909,2020):
        url.append(f'https://www.goodreads.com/book/popular_by_date/{i}/')
    return url


def initial_gr_signin(driver):
    ''' Signs into goodreads with non-existant account to avoid ensuing pop-ups '''
    driver.get('https://www.goodreads.com/')

    email = driver.find_element_by_xpath('//*[@id="userSignInFormEmail"]')
    email.click()
    email.send_keys(username)

    passwrd = driver.find_element_by_xpath('//*[@id="user_password"]')
    passwrd.click()
    passwrd.send_keys(pswd)

    signin = driver.find_element_by_xpath('//*[@id="sign_in"]/div[3]/input[1]')
    signin.click()
    

def clean_ratings(split_block_text):
    ratin = False
    avg_rating = np.nan
    tot_rating = np.nan
    for i in split_block_text:
        if ratin == False:
            try:
                #trying to convert i to float
                avg_rating = float(i)
                ratin = True
                #break the loop if i is the first string that's successfully converted
            except:
                continue
        else:
            try:
                #trying to convert i to float
                tot_rating = int(i.replace(',',''))
                #break the loop if i is the first string that's successfully converted
                break
            except:
                continue
    return {'avg_rating':avg_rating, 'tot_rating': tot_rating}


def goodreads_list_scrape(driver, site):
    ''' 
    Takes in a driver pointed to a top ~200 page, and returns initial info (title, authors, num_ratings and id) on 
    all books on the page in the form of a list of dictionaries. Prints progress updates every 50 books.
    '''
    list_of_book_dicts = []
    
    titles_blocks = driver.find_elements_by_class_name('bookTitle')
    
    authors_blocks = driver.find_elements_by_class_name('authorName')
  
    ratings_blocks = driver.find_elements_by_class_name('minirating')
    
    num_blocks = driver.find_elements_by_class_name('minirating')
    
    for i in range(len(titles_blocks)):
        gs_dict = {}
        
        gs_dict['titles'] = titles_blocks[i].text
        
        gs_dict['authors'] = authors_blocks[i].text

        idx = re.search(r'\d+',titles_blocks[i].get_attribute('href')).group()
        
        gs_dict['id'] = int(idx)

        gs_dict.update(clean_ratings(num_blocks[i].text.split()))

        gs_dict['year_pub'] = site[-5:-1]

        list_of_book_dicts.append(gs_dict)
        
    print ('scraping done')
    return list_of_book_dicts


def get_imgs(driver):
    '''
    Takes in a driver and returns the source image (coverImage) for the page that the driver is currently pointed at. 
    Returns a NaN for instances where the information is not found
    '''
    try:
        img = driver.find_element_by_id('coverImage')
        img = img.get_attribute('src')
        return img
    except:
        try:
            img = driver.find_element_by_class('mainBookCover')
            img = img.get_attribute('src')
            return img
        except:
            try:
                img = driver.find_element_by_xpath('/html/body/div[2]/div[3]/div[1]/div[2]/div[2]/div[1]/div[1]/div[1]/div[1]/a/img')
                img = img.get_attribute('src')
                return img
            except:
                return np.nan

def get_description(driver):
    '''
    Takes in a driver and returns the book description for the page that the driver is currently pointed at. 
    Returns a NaN for instances where the information is not found
    '''
    more = driver.find_elements_by_xpath('//*[@id="description"]/a')
    try:
        # handling errors to do with an extended description
        more[0].click()
        try:
            describe = driver.find_element_by_id('description').text[:-7].strip()
            descrip = ' '.join(describe.split('\n'))
        except:
            descrip = np.nan

    except:
        # if there is no "more" button
        try:
            describe = driver.find_element_by_id('description').text[:-7].strip()
            descrip = ' '.join(describe.split('\n'))
        except:
            descrip = np.nan
    return descrip            
            


def get_genre(driver):
    ''' returns a string of genre titles associated with a book '''
    genre = np.nan
    try:
        genre_blocks = driver.find_elements_by_class_name('actionLinkLite.bookPageGenreLink')
        genre = []
        for genre_block in genre_blocks:
            if genre_block.text[0].isdigit() == False:
                genre.append(genre_block.text)
        genre = ', '.join(genre)
    except:
        pass
    
    return genre

    
def get_form_page_isbn(driver):
    ''' Returns book format, number of pages and isbn number, in that order. '''
    form = np.nan
    page = np.nan
    isbn = np.nan

    try:
        details = driver.find_element_by_id('details')
        span = details.find_elements_by_css_selector('span')

        for word in span:
            if 'hardcover' in word.text.lower() or 'paperback' in word.text.lower():
                form = word.text.lower()
            if 'pages' in word.text.lower():
                page = int(word.text.split()[0])
            if 'ISBN' in word.text:
                isbn = word.text
                isbn = int(isbn.split()[1][:-1])
    except:
        pass

    return form, page, isbn



def secondary_scrape(gr_id, driver):
    '''
    Scrapes the goodreads website with given dic.id to get img (img src link), description, genre, format, pages and isbn. 
    Funciton returns the variables together as a dictionary in above order.
    '''

    site = f"https://www.goodreads.com/book/show/{gr_id}"
    driver.get(site)
    
    img = get_imgs(driver)
    description = get_description(driver)
    genre = get_genre(driver)
    form, page, isbn = get_form_page_isbn(driver)
        
    return {'img':img, 'description':description, 'genre':genre,'format':form, 'page':page, 'isbn':isbn}



def save_those_50(latest, last_50): 
    '''saves 'latest' as “last_50”: will overwrite the existing "last_50" json and csv files with the current 50 (as latest)'''
    latest.to_csv(f'{last_50}.csv',index=False)
    latest.to_json(f'{last_50}.json',orient='records')
    return 1
    
    
def add_to_saved_df(latest, saved_filename): 
    ''' returns a concatenated dataframe with the last 50 appended onto it, to be used before saving'''
    old = pd.read_csv(saved_filename, index_col=[0])
    return old.append(latest, sort=True)


def update_saved(updated_df, saved_filename): 
    '''saves updated_df as the current saved_filename: will overwrite the existing json and csv files with the given df'''
    updated_df.to_csv(f'{saved_filename}.csv',index=False)
    updated_df.to_json(f'{saved_filename}.json',orient='records')
    return 1


def push_to_git(last_50, saved_filename, message): 
    '''
    pushes given files to github:
    - in future, would take in a list of filenames to add to commit and make a bash file to auto commit
    - presently, has preexisting bash file name , commit message and runs an auto-commit function by calling the 
    bash file in the terminal
    '''
    return 0






# Processing functions (helpers to more complex rec system)


def make_keywords(description):
    '''Makes keywords of description using "Rake" '''
    # instantiating Rake, by default is uses english stopwords from NLTK
    # and discard all puntuation characters
    r = Rake()

    # extracting the words by passing the text
    r.extract_keywords_from_text(description)

    # getting the dictionary with key words and their scores
    key_words_dict_scores = r.get_word_degrees()
    
    # return the key words
    return list(key_words_dict_scores.keys())


def process_and_almost_bag(row_dict):
    ''' 
    Takes in author, genre and cleaned description (as a series or dictionary) and returns a cleaned column of 
    author and genre combined, as well as the keywords in description. To be used in conjuction with make_bow() for full use.
    '''
    authors, genre, desc_clean = row_dict['authors'], row_dict['genre'], row_dict['description']

    # get rid of nan errors by setting nan values to empty strings
    if genre == 'set()' or type(genre) == float:
        genre = ''
    if type(authors) == float:
        authors = ''
    if type(desc_clean) == float:
        desc_clean = ''
        
    
    # create a clean, author + genre column
    au_ge = authors.lower().replace(' ','').replace('.','') + ' ' + genre.lower().replace(' ','').replace(',',' ')
    
    # clean description for keyword search
    for c in string.punctuation + '”' + '“':
        if c == '`' or c == "'": 
            desc_clean = desc_clean.replace(c,"")
        else:
            desc_clean = desc_clean.replace(c," ")
            
    for s in string.digits:
        desc_clean = desc_clean.replace(s,"")

    # get keywords using clean description in make_keywords() function
    key_words = ' '.join(make_keywords(desc_clean))
        

    return au_ge, key_words



def make_bow(au_ge, key_words):
    '''create a bag of words that combines the clean author/genre and keywords from process_and_almost_bag '''
    if type(au_ge)==float:
        au_ge = ''
    if type(key_words)==float:
        key_words = ''
        
    return au_ge + ' ' + key_words


def clean_and_bag_words(row_dict):
    '''
    Takes in a 'row' (a dictionary of book information) and combines helper functions to clean description, 
    make keywords and a final bag of words (Bag_of_Description) for the 'row'.
    '''
    au_ge, key_words = process_and_almost_bag(row_dict)
    bow = make_bow(au_ge, key_words)
    
    return {'au_ge':au_ge, 'key_words':key_words, 'bow':bow }



# Rec system helper functions

def simple_rec_read(item_id, num, results, ds):
    ''' Helper function for simple_rec in notebook environments: simply reads the results out of the dictionary. '''
    item_id = ds.iloc[item_id]['id']
    print("Recommending " + str(num) + " products similar to " + item(item_id, ds) + "...")
    print("-------")
    recs = results[item_id][:num]
    for rec in recs:
        print (rec[1])
        print("Recommended: " + item(rec[1], ds) + " (score:" + str(rec[0]) + ")")

def fail_to_find(df):
    '''  
    helper function for interfacing with the final recommendation system in notebook environments : allows for infinite user input on title, ends interface if
    user submits 'quit!' and returns find_title if title is found
    '''
    final = input("That title did not match any of our books! Please try again, or enter 'quit!' to stop playing.")
    if final == 'quit!':
        return 0
    else:
        return find_title(final, df)
        
def find_title(guess, df):
    ''' 
    helper function for interfacing with the final recommendation system in notebook environments : 
    searches for book title within given dataframe and calls.
    Calls fail_to_find for greater user input if title not initially found.
     '''
    guess = guess.lower()
    final = []
    titles_list = {x.lower(): x for x in df.index}
    for possible in list(titles_list.keys()):
        if guess in possible:
               final.append(possible)
    if len(final) == 0:
        return fail_to_find(df)
    if len(final) == 1:
        print (f"\n Great! Looking for recomendations for the book: {titles_list[final[0]]}")
        return titles_list[final[0]]
    elif len(final) > 1:
        maybe = input(f"We found {len(final)} books that matched your search! Would you like to look thru them? If so enter'yes', otherwise enter 'no'.")
        if maybe == 'yes':
            print ("Is your book in this list? \n")
            maybe = input(f"{final}\n")
        for poss in final:
            end = input(f"Is your book {titles_list[poss]}? If so enter 'yes' and if not enter 'no'.")
            if end == 'yes':
                print (f"\n Great! Looking for recomendations for the book: {titles_list[poss]}")
                return titles_list[poss]
        return fail_to_find(df)
                                                                                    
                      
def return_pop_df(popularity, df):
    '''
    Filter helper function : returns population filtered dataframe - options are:
        deep cut: < 27,000
        well known: between 80,000 and 27,000
        super popular: > 80,000
    '''
    if popularity == 'deep cut':
        return df[df['num_ratings'] < 27000]
    if popularity == 'well known':
        return df[(df['num_ratings'] < 80000) & (df['num_ratings'] > 27000)]
    if popularity == 'super popular':
        return df[df['num_ratings'] > 80000]
    
def filter_df(length, popularity, df):
    '''
    Filter helper function : returns length and popularity filtered dataframe - 
    
    length options are:
        long: >= 350
        short: < 350
        
    popularity options are:
        deep cut: < 27,000
        well known: between 80,000 and 27,000
        super popular: > 80,000
    '''
    if length != None:
        if length == 'long':
            df = df[(df['pages'] >= 350)]
        elif length == 'short':
            df = df[(df['pages'] < 350)]
        
    if popularity != None:
        df = return_pop_df(popularity, df)

    return df



## Recommendation Functions


# Most simple reco - filter only

def filter_books_rec(genre, length, popularity, df):
    ''' 
    Most simple recommendation system: uses a dictionary and dataframe to filter based on user's length, genre and popularity preferences 
    '''
    #make genres into dictionary with titles as index
    genre_dict = dict(df.genre)
    
    # put sub-genres into a main genres dictionary
    genre_id_dict = {'Scifi': [], 'Romance':[], 'Thriller':[], 'Comics':[], 'Biography':[], 'Nonfiction':[], 'Self_help':[], 'Young_Adult':[], 'Family':[], 'Fiction':[]}

    for k,v in genre_dict.items():  # where k=book_name and v=genre_category
        if ('Fantasy' in v) or ('Science' in v):
            genre_id_dict['Scifi'].append(k)
        if ('Romance' in v) or ('Chick Lit' in v) or ('Erotic' in v) or ('Contemporary' in v) or ('Drama' in v):
            genre_id_dict['Romance'].append(k)
        if ('Thriller' in v) or ('Mystery' in v) or ('Crime' in v) or ('Horror' in v):
            genre_id_dict['Thriller'].append(k)
        if ('Comic' in v) or ('Graphic' in v) or ('Manga' in v):
            genre_id_dict['Comics'].append(k)
        if ('Biography' in v) or ('Autobiography' in v) or ('Memoir' in v) or ('Sport' in v):
            genre_id_dict['Biography'].append(k)
        if ('Nonfiction' in v) or ('History' in v) or ('Politics' in v) or ('Cooking' in v) or ('Art' in v):
            genre_id_dict['Nonfiction'].append(k)
        if ('Self Help' in v) or ('Religion' in v):
            genre_id_dict['Self_help'].append(k)
        if ('Young Adult' in v):
            genre_id_dict['Young_Adult'].append(k)
        if ('Childrens' in v) or ('Family' in v):
            genre_id_dict['Family'].append(k)
        if ('Fiction' in v):
            genre_id_dict['Fiction'].append(k)        
    

    poss_books = genre_id_dict[genre]
    
    return filter_df(length, popularity, df.loc[poss_books])


# second tier rec system - only cosine similarity, doesn't include filtration option

def get_recs_simple(title, dff, sim_matrix, testing=False):
    '''
    Rec system using only description: 
    Takes in a title and dataframe (use dff), then makes an abbreviated df containing only the titles and index number. 
    Returns top 10 similar books based on cosine similarity of vectorized description.
    '''
    if testing == True:
        title = find_title(title, dff)

    # create a new dataframe with titles as index, and index as a feature
    indices = pd.Series(list(range(len(dff))), index=dff.index)
    idx = indices[title]

    sim_scores = list(enumerate(sim_matrix[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:31]
    movie_indices = [i[0] for i in sim_scores]

    return dff.loc[indices[movie_indices].index][:11]



# Server functions

# Final recommendation system - includes option of filter arguments
                      
def recommendations(title, df, sim_matrix, filter_args=(None,None), list_length=11, suppress=True):
    '''
    Return recommendations based on a "bag of words" comprised of book author, genres and description.
    Function takes in title, list length, a dataframe, a similarity matrix and an option to add filters or suppress output.
    filter_args is (length, popularity) : 

    length options are:
        long: >= 350
        short: < 350
        
    popularity options are:
        deep cut: < 27,000
        well known: between 80,000 and 27,000
        super popular: > 80,000
    
    See filter_df() for further workings on this function.
    '''
    
    recommended_books = []
    
    # creating a Series for the movie titles so they are associated to an ordered numerical list
    indices = pd.DataFrame(df.titles, index=df.index)
    
    # getting the index of the book that matches the title
    idx = indices[indices.titles == title].index[0]

    # creating a Series with the similarity scores in descending order
    score_series = pd.Series(sim_matrix[idx]).sort_values(ascending = False)

    # getting the indexes of the 10 most similar movies
    top_10_indexes = list(score_series.iloc[1:list_length+1].index)
    
    # populating the list with the titles of the best 10 matching movies
    for i in top_10_indexes:
        recommended_books.append(list(df.index)[i])
    
    if suppress == False:
        print (f"\n We recommend: ")
        for book_num in range(len(recommended_books)):
            print (book_num +1, recommended_books[book_num])
        
    if filter_args != (None,None):
        return filter_df(filter_args[0],filter_args[1],df.loc[recommended_books])

    return df.loc[recommended_books]
                      

def return_query(query,df):
    ''' Takes in a string and returns a df with 50 most similar titles '''
    matching_books = []
    for k, v in df.iterrows():
        title = v.titles
        ratio_set = fuzz.token_set_ratio(title.lower(), query.lower())
        if ratio_set > 70:
            matching_books.append(k)

    return df.iloc[matching_books]