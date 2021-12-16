import json
import requests
from bs4 import BeautifulSoup
import time
import sqlite3
import numpy as np
from flask import Flask, render_template, request

CACHE_FILE_NAME = 'cache.json'
CACHE_DICT = {}
tags_limits = 3
max_entries = 15
reviews_limits = 3
catagory_table = ['rpg', 'action', 'adventure_and_casual',
                'sports_and_racing', 'strategy','simulation']
language_table = ['Simplified Chinese', 'English', 'French', 'Russian', 'Japanese']
max_price = 999999

def open_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):

    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILE_NAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 
 

        
DB_NAME = 'games.sqlite'

def create_db():

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    drop_games_sql = 'DROP TABLE IF EXISTS "Games"'
    drop_details_sql = 'DROP TABLE IF EXISTS "Details"'
    
    create_games_sql = '''
        CREATE TABLE IF NOT EXISTS "Games" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT, 
            "TITLE" TEXT NOT NULL,
            "PRICE" INTEGER NOT NULL
        )
    '''

    create_details_sql = '''
        CREATE TABLE IF NOT EXISTS "Details" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT, 
            "TITLE" TEXT ,
            "URL" TEXT NOT NULL, 
            "DESCRIPTION" TEXT NOT NULL,
            "IMAGE_URL" TEXT NOT NULL,
            "RATE" INTEGER NOT NULL,
            "PRICE" INTEGER NOT NULL,
            "DEVELOPER" TEXT NOT NULL,
            "RELEASE_DATE" TEXT NOT NULL,
            "TAGS" TEXT NOT NULL,
            "REVIEW" TEXT NOT NULL,
            "LANGUAGES" TEXT NOT NULL,
            FOREIGN KEY(TITLE) REFERENCES Games(TITLE)
        )
    '''
    cur.execute(drop_details_sql)
    cur.execute(drop_games_sql)
    cur.execute(create_games_sql)
    cur.execute(create_details_sql)
    conn.commit()
    conn.close()

def load_games(game_dict):

    insert_games_sql = '''
        INSERT INTO Games
        VALUES (?,?,?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for game in game_dict:
        cur.execute(insert_games_sql,[
            game['game_id'],
            game['title'],
            game['price']
        ])
    conn.commit()
    conn.close()

def load_details(detail_dict, status=True):

    insert_details_sql = '''
        INSERT INTO Details
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for detail in detail_dict:
        if status:
            cur.execute(insert_details_sql,[
                detail['id'],
                detail['title'],
                detail['url'],
                detail['description'],
                detail['image_url'],
                detail['rate'],
                detail['price'],
                detail['developer'],
                detail['release_date'],
                ' '.join(detail['reviews']),
                ', '.join(detail['tags']),
                detail['language_options']
            ])
        else:
            cur.execute(insert_details_sql,[
                detail[0],
                detail[1],
                detail[2],
                detail[3],
                detail[4],
                detail[5],
                detail[6],
                detail[7],
                detail[8],
                detail[9],
                detail[10],
                detail[11]
            ])
    conn.commit()
    conn.close()

def get_db_results(method='1'):

    if method == '1':
        query = '''
        SELECT * FROM Details
        LIMIT 10 
        '''
    elif method == '2':
        query = '''
        SELECT * FROM Details
        WHERE PRICE <> 'None'
        ORDER BY PRICE ASC 
        LIMIT 10 
        '''
    elif method == '3':
        query = '''
        SELECT * FROM Details
        WHERE RATE <> 'None'
        ORDER BY RATE DESC 
        LIMIT 10 
        '''   
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    result = cursor.execute(query).fetchall()
    connection.close()

    return result


def make_request_with_cache(url, cache):

    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[url], True
    else:
        print("Fetching")
        time.sleep(0.5)
        response = requests.get(url)
        return response.text, False

def get_catagory_results(baseurl, catagory_term):

    catagory_url = baseurl + catagory_term
    
    response_text, status = make_request_with_cache(catagory_url, CACHE_DICT)
    if status:
        results = response_text
        return results, catagory_url, status
    else:
        soup = BeautifulSoup(response_text, 'html.parser')
        catagory_results = soup.find(id='NewReleasesRows')

        catagory_lists = catagory_results.find_all('a')
        results = []
        for game_info in catagory_lists:
            game_dict = {}
            if 'data-ds-appid' not in game_info.attrs.keys():
                continue
            else:
                game_dict['game_id'] = game_info.attrs['data-ds-appid']

            title = game_info.find('div', class_='tab_item_name').text
            game_dict['title'] = title if title is not None else 'None'
            
            #price = game_info.find('div',class_="discount_final_price")
            price = game_info.find('div',class_="discount_block tab_item_discount")
            if price is None:
                game_dict['price'] = 0
            else:
                game_dict['price'] = int(price.attrs['data-price-final'])

            results.append(game_dict)
        return results, catagory_url, status

def get_search_results(baseurl, search_term):

    search_url = baseurl + search_term

    response_text, status = make_request_with_cache(search_url, CACHE_DICT)
    if status:
        return response_text, search_url, status
    else:
        soup = BeautifulSoup(response_text, 'html.parser')
        search_results = soup.find(id='search_resultsRows')
        if search_results is None:
            return None, None, None
        else:
            search_lists = search_results.find_all('a')
            results = []
            for game_info in search_lists:
                game_dict = {}
                if 'data-ds-appid' not in game_info.attrs.keys():
                    continue
                else:
                    game_dict['game_id'] = game_info.attrs['data-ds-appid']

                title = game_info.find('span', class_='title').text
                game_dict['title'] = title if title is not None else 'None'
                
                #price = game_info.find('div',class_="search_price")
                price = game_info.find('div',class_="col search_price_discount_combined responsive_secondrow").attrs['data-price-final']
                if price is None:
                    game_dict['price'] = 0
                else:
                    game_dict['price'] = int(price)
                    '''
                    price = price.text.strip()
                    if price == "Free" or price == "Free To Play" or price == "Free to Play":
                        game_dict['price'] = 0
                    else:
                        price_str = ''.join(price.split(' ')[-1].split(','))
                        if price_str.isnumeric():
                            game_dict['price'] = int(price_str)
                        else:
                            game_dict['price'] = max_price'''


                results.append(game_dict)
            return results, search_url, status

def get_detail_results(game_dicts):

    results =[]
    url = 'https://store.steampowered.com/app/'
    num_games = 0
    for game_info in game_dicts:
        detail_dict = {}
        detail_dict['id'] = game_info['game_id']
        detail_dict['title'] = game_info['title']
        detail_dict['url'] = url + game_info['game_id']
        response_text, status = make_request_with_cache(detail_dict['url'], CACHE_DICT)
        if status:
            detail_dict = response_text
        else:
            soup = BeautifulSoup(response_text, 'html.parser')
            # note that sometimes there is no description
            # We wat to add 1. tag (top3), 2. Review
            large_block = soup.find('div', class_='block')

            description = large_block.find('div', class_='game_description_snippet')
            if description is None:
                detail_dict['description'] = 'None'
                #break
            else:
                detail_dict['description'] = description.text.strip()
            
            rate = large_block.find('span',class_="responsive_reviewdesc_short")
            if rate == None:
                detail_dict['rate'] = 0
            else:
                detail_dict['rate'] = int(rate.text.strip()[1:3])

            date = large_block.find('div',class_="release_date")
            if date == None:
                detail_dict['release_date'] = 'None'
            else:
                detail_dict['release_date'] = date.find('div',class_='date').text.strip()

            price = game_info['price']
            detail_dict['price'] = price

            image_url = large_block.find('img', class_='game_header_image_full')['src']
            detail_dict['image_url'] = image_url

            developer = large_block.find('div', id="developers_list")
            if developer == None:
                detail_dict['developer'] = "None"
            else:
                developer=developer.find('a').text.strip()
                detail_dict['developer'] = developer
            
            
            tags = large_block.find_all('a', class_='app_tag')
            num_tags = 0; tag_list = []
            if tags == None:
                detail_dict['tags'] = 'None'
            else:
                for tag in tags:
                    tag_list.append(tag.text.strip())
                    num_tags += 1
                    if num_tags>=tags_limits:
                        break
                detail_dict['tags'] = tag_list
            
            pop_review = soup.find('div',id = "game_area_description")
            review_sentences = pop_review.find_all('strong')
            num_reviews = 0; review_list = []
            if review_sentences == None:
                detail_dict['reviews'] = 'None'
            else:
                for review in review_sentences:
                    review_list.append(review.text.strip())
                    num_reviews += 1
                    if num_reviews>=reviews_limits:
                        break
                detail_dict['reviews'] = review_list

            # At last we need the language property
            print(detail_dict['title'])
            language = soup.find('table', class_ = "game_language_options")
            if language == None:
                detail_dict['language_options'] = 'None'
            else:
                language_options = language.find_all('td', class_ = "ellipsis")
                all_language = []
                for l_opt in language_options:
                    all_language.append(l_opt.text.strip())
                detail_dict['language_options'] = ', '.join(all_language)
            
            CACHE_DICT[detail_dict['url']] = detail_dict

        results.append(detail_dict)
        num_games += 1
        if num_games>=max_entries:
            break
    return results


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html') # just the static HTML

@app.route('/handle_form_catagory', methods=['POST'])
def handle_form_catagory():

    catagory = request.form["catagory"]
    url_cata = "https://store.steampowered.com/category/"
    real_catagory = catagory_table[int(catagory)-1]
    game_dict, url, status = get_catagory_results(url_cata, real_catagory)
    if status:
        load_database(game_dict, False)
        results = get_db_results()
        return render_template('show_detail.html', results=results)
    else:
        load_database(game_dict)
        game_dict = get_db_results()
        CACHE_DICT[url] = game_dict
        save_cache(CACHE_DICT)
        return render_template('show_detail.html', results=game_dict)

@app.route('/handle_form_search', methods=['POST'])
def handle_form_search():
    name = request.form["name"]
    url_search = "https://store.steampowered.com/search/?term="
    game_dict, url, status = get_search_results(url_search, name)
    if game_dict is None:
        return render_template('exceptions.html')
    else:
        if status:
            order = request.form["order"]
            load_database(game_dict, False)
            results = get_db_results(order)
            return render_template('show_detail.html', results=results)
        else:
            load_database(game_dict)
            order = request.form["order"]
            results = get_db_results(order)
            CACHE_DICT[url] = results
            save_cache(CACHE_DICT)
            return render_template('show_detail.html', results=results)


@app.route('/check_languages', methods=['POST'])
def construct_graph():
    cur_dicts = get_db_results()
    num_entry = len(cur_dicts)
    num_lang = len(language_table)
    bipart_graph = np.zeros((num_entry, num_lang),dtype=int)
    for n in range(num_entry):
        for l in range(num_lang):
            lang_l = language_table[l]
            if (cur_dicts[n][-1].find(lang_l)>=0):
                bipart_graph[n,l] = 1
    bipart_graph = bipart_graph.tolist()
    return render_template('languages.html', results=zip(cur_dicts, bipart_graph))

def load_database(game_dict, status=True):
    if status:
        details_dict = get_detail_results(game_dict)
        create_db()
        load_games(game_dict)
        load_details(details_dict)
    else:
        create_db()
        load_details(game_dict, False)



if __name__ == "__main__":
    CACHE_DICT = open_cache()
    app.run(debug=True)
