import json
import codecs
import pandas as pd
from flask import request, url_for
from flask_api import FlaskAPI, status, exceptions
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity

from book_functions import *

app = FlaskAPI(__name__)
CORS(app)

# loading in necessary variables
# with open('goodreads_updated.json') as json_file:  # is this still needed?
data = pd.read_json('goodreads_updated.json',
                    orient='index').reset_index(drop=True)

df = pd.read_csv('goodreads_updated.csv')

# get dot product of tfidf matrix on the transposition of itself to get the cosine similarity
tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 2),
                     min_df=0, stop_words='english')
tfidf_matrix = tf.fit_transform(data['bag_of_words'])
cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)


@app.route("/books", methods=['GET'])
def notes_list():
    return data.sample(50).to_json(orient='records')


@app.route('/books', methods=['POST'])
def returnTitle():
    text = request.json['text']
    text_json = {'data':  text}
    # here we could add an option to filter by length & popularity - "filter_args" respectively
    list_of_recs = recommendations(
        text, data, cosine_sim, filter_args=(None, None))
    return list_of_recs.to_json(orient='records')


# # Filter helper functions

# def return_pop_df(popularity, df):
#     '''
#     returns population filtered dataframe - options are:
#         deep cut: < 27,000
#         well known: between 80,000 and 27,000
#         super popular: > 80,000
#     '''
#     if popularity == 'deep cut':
#         return df[df['num_ratings'] < 27000]
#     if popularity == 'well known':
#         return df[(df['num_ratings'] < 80000) & (df['num_ratings'] > 27000)]
#     if popularity == 'super popular':
#         return df[df['num_ratings'] > 80000]

# def filter_df(length, popularity, df):
#     '''
#     returns length and popularity filtered dataframe -

#     length options are:
#         long: >= 350
#         short: < 350

#     popularity options are:
#         deep cut: < 27,000
#         well known: between 80,000 and 27,000
#         super popular: > 80,000
#     '''
#     if length != None:
#         if length == 'long':
#             df = df[(df['pages'] >= 350)]
#         elif length == 'short':
#             df = df[(df['pages'] < 350)]

#     if popularity != None:
#         df = return_pop_df(popularity, df)

#     return df


# # Final recommendation system - includes option of filter arguments

# def recommendations(title, df, sim_matrix, filter_args=(None,None), list_length=11, suppress=True):
#     '''
#     Return recommendations based on a "bag of words" comprised of book author, genres and description.
#     Function takes in title, list length, a dataframe, a similarity matrix and an option to add filters or suppress output.
#     filter_args is (length, popularity) :

#     length options are:
#         long: >= 350
#         short: < 350

#     popularity options are:
#         deep cut: < 27,000
#         well known: between 80,000 and 27,000
#         super popular: > 80,000

#     See filter_df() for further workings on this function.
#     '''

#     recommended_books = []

#     # creating a Series for the movie titles so they are associated to an ordered numerical list
#     indices = pd.Series(list(range(len(df))), index=df.index)

#     # getting the index of the book that matches the title
#     idx = indices[title]

#     # creating a Series with the similarity scores in descending order
#     score_series = pd.Series(sim_matrix[idx]).sort_values(ascending = False)

#     # getting the indexes of the 10 most similar movies
#     top_10_indexes = list(score_series.iloc[1:list_length+1].index)

#     # populating the list with the titles of the best 10 matching movies
#     for i in top_10_indexes:
#         recommended_books.append(list(df.index)[i])

#     if suppress == False:
#         print (f"\n We recommend: ")
#         for book_num in range(len(recommended_books)):
#             print (book_num +1, recommended_books[book_num])

#     if filter_args != (None,None):
#         return filter_df(filter_args[0],filter_args[1],df.loc[recommended_books])

#     return df.loc[recommended_books]


# # addition - simple rec system (just filters based on genre, length and popularity)

# def simple_rec(genre, length, popularity, df):
#     '''
#     use a  genre_id_dict and df_simple
#     '''
#     #make genres into dictionary with titles as index
#     genre_dict = dict(df.genre)

#     # put sub-genres into a main genres dictionary
#     genre_id_dict = {'Scifi': [], 'Romance':[], 'Thriller':[], 'Comics':[], 'Biography':[], 'Nonfiction':[], 'Self_help':[], 'Young_Adult':[], 'Family':[], 'Fiction':[]}

#     for k,v in genre_dict.items():  # where k=book_name and v=genre_category
#         if ('Fantasy' in v) or ('Science' in v):
#             genre_id_dict['Scifi'].append(k)
#         if ('Romance' in v) or ('Chick Lit' in v) or ('Erotic' in v) or ('Contemporary' in v) or ('Drama' in v):
#             genre_id_dict['Romance'].append(k)
#         if ('Thriller' in v) or ('Mystery' in v) or ('Crime' in v) or ('Horror' in v):
#             genre_id_dict['Thriller'].append(k)
#         if ('Comic' in v) or ('Graphic' in v) or ('Manga' in v):
#             genre_id_dict['Comics'].append(k)
#         if ('Biography' in v) or ('Autobiography' in v) or ('Memoir' in v) or ('Sport' in v):
#             genre_id_dict['Biography'].append(k)
#         if ('Nonfiction' in v) or ('History' in v) or ('Politics' in v) or ('Cooking' in v) or ('Art' in v):
#             genre_id_dict['Nonfiction'].append(k)
#         if ('Self Help' in v) or ('Religion' in v):
#             genre_id_dict['Self_help'].append(k)
#         if ('Young Adult' in v):
#             genre_id_dict['Young_Adult'].append(k)
#         if ('Childrens' in v) or ('Family' in v):
#             genre_id_dict['Family'].append(k)
#         if ('Fiction' in v):
#             genre_id_dict['Fiction'].append(k)


#     poss_books = genre_id_dict[genre]

#     return filter_df(length, popularity, df.loc[poss_books])
