# imports 
import json, codecs
import pandas as pd
from flask import request, url_for
from flask_api import FlaskAPI, status, exceptions
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity

from book_functions import *


app = FlaskAPI(__name__)
CORS(app)

# load in data and transform as needed

# data = pd.read_json('updating_df.json',orient='records') # later
data = pd.read_json('goodreads_updated.json',orient='records').reset_index(drop=True).drop_duplicates()

james_data = data[['id','authors', 'titles', 'description', 'img', 'genre']]
james_data.genre = james_data.genre.apply(lambda x: x.split(', '))

tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 2),min_df=0, stop_words='english')
tfidf_matrix = tf.fit_transform(data['bag_of_words'])
cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

# routing information


# input: < string > search query
# output: < [<json>] > list of books. LIMIT = 50
@app.route("/query", methods=['POST'])
def handleSearch():
    query = request.json['query']


# input: < string > page number
# output: < [<json>] > list of books. LIMIT = 50
@app.route("/books/<page_num>", methods=['GET'])
def getBooks(page_num):
    return page_num


# output: < [<json>] > list of first 50 books.
@app.route("/books", methods=['GET'])
def notes_list():
    return data.iloc[0:5].to_json(orient='records')


@app.route('/books', methods=['POST'])
def returnTitle():
    text = request.json['text']
    text_json = {'data':  text}
    # here we could add an option to filter by length & popularity - "filter_args" respectively
    list_of_recs = recommendations(
        text, data, cosine_sim, filter_args=(None, None))
    return list_of_recs.to_json(orient='records')