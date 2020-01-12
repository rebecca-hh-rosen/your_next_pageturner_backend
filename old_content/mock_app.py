#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 16 13:19:07 2019

@author: rebeccarosen
"""



@app.route('/books', methods=['POST'])
def returnTitle():
    text = request.json['text']
    text_json = {'data':  text}
    list_of_recs = recommendations(text_json.data, df, list_length=11)
    return json.dumps(list_of_recs)

