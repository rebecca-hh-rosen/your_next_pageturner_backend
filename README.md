# Your Next Page Turner (Backend)

Your Next Page Turner is a book recommendation system that sources from the top 200 books of the last 200 years, as determined by Goodreads users and data. 

Information on nearly 20,000 books - including title, author, description and cover image -  was scraped from Goodreads in January 2020 using Selenium. Details on the scraping process can be found in the file entitled "clean_scrape.ipynb".

The present recommendation system implements a content-based model to suggest books based on the similarity scores of their associated "bag of words". Details on this process can be found throughout the "cleaning_and_eda.ipynb" file, as well as in the "book_functions.py" file.



The resulting recommendation system is currently implemented and running through a Flask/Yarn enabled frontend, as a collaboration with software engineer, James Sharpe. This full site can be found at [his website](<https://your-next-page-turner.firebaseapp.com/>). Below are a few images highlighting the process of the site:

## 1. Browsing the collection:
!['select a book'](https://github.com/rebecca-hh-rosen/your_next_pageturner_backend/blob/master/book_images/book_select.png)

## 2. Choosing a novel:
!['view description'](https://github.com/rebecca-hh-rosen/your_next_pageturner_backend/blob/master/book_images/book_info.png)


## 3. Gettin a recommendation:
!['seek recommendation'](https://github.com/rebecca-hh-rosen/your_next_pageturner_backend/blob/master/book_images/book_rec.png)



Enjoy, and read on!


*Feel free to reach out to me at rebeccahhrosen@gmail.com for any questions, inquiries or comments. If you liked this, please check out my Medium page at https://medium.com/@rebeccahhrosen.*
