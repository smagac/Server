import sqlite3, atexit, random
import schedule
from flask import Flask, request, session, g, jsonify
from datetime import datetime
from contextlib import closing

# configuration
DATABASE = './sm_daily.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# application definition
app = Flask(__name__)
app.config.from_object(__name__)

# Dungeon specifications
_TYPES = ["Other", "Audio", "Image", "Compressed", "Video", "Executable"]
_SEEDSIZE = 63

_dungeon = {
    'seed':0,
    'difficulty':0,
    'type':None
}

    
def create_dungeon():
    seed = random.getrandbits(_SEEDSIZE)
    filetype = random.choice(_TYPES)
    difficulty = random.randint(1, 5)
    _dungeon['seed'] = seed
    _dungeon['type'] = filetype
    _dungeon['difficulty'] = difficulty
    # make sure the deaths table is clean when a new dungeon is made
    init_db()

# also make sure a dungeon is defined when the app starts
@app.before_first_request
def prepare():
    create_dungeon()

# create a new dungeon every day at midnight
schedule.every().day.at("00:00").do(create_dungeon)

def connect_to_database():
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def get_db():
    g.db = connect_to_database()
    g.db.row_factory = sqlite3.Row

# make sure to close the db connection        
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
        g.db = None

# make sure the schema exists for the app when we start
def init_db():
    db = connect_to_database()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()
        
@app.route('/daily', methods=['GET'])
def index():
    # on a GET we return the daily dungeon specification
    return (jsonify(**_dungeon), 200, {'Content-Type':'application/json'})
       
@app.route('/daily/<int:depth>', methods=['GET', 'POST'])
def dead(depth):
    cur = g.db.cursor()        
    # on a GET we return a small set of dead players from the floor
    if request.method == 'GET':
        cur.execute('SELECT ifnull(steam_name, "Adventurer") steam_name, ifnull(steam_id, -1) steam_id, x, y, dead_to, level FROM deaths WHERE level = ? ORDER BY RANDOM() LIMIT 20', (depth,))
        result_set = cur.fetchall()
        dead = [dict(row) for row in result_set]
        data = {
            "dead" : dead
        }
        return (jsonify(data), 200, {'Content-Type':'application/json'})
        
    # on a POST request, we add data to the database
    if request.method == 'POST':
        print(request.get_json(force=True))
        form = request.get_json(force=True)
        seed = form['seed'] #use daily dungeon seed for validation
        if seed != _dungeon['seed']:
            print("%d : %d" % (seed, _dungeon['seed']))
            return (jsonify({"error":"Seed does not match"}), 400)
        
        steam_id = form['steam_id']
        steam_name = form['steam_name']
        level = form['level']
        dead_to = form['dead_to']
        x = form['x']
        y = form['y']
        cur.execute('INSERT OR REPLACE INTO deaths(steam_id, steam_name, dead_to, level, x, y) VALUES (?,?,?,?,?,?)', (steam_id, steam_name, dead_to, level, x, y))
        g.db.commit()
        return (jsonify({}), 200)
            
if __name__ == '__main__':
    schedule.run_pending()
    app.run()