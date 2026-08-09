import sqlite3, logging, os
from contextlib import closing

logging.basicConfig(filename="db.log", 
                    filemode="a", 
                    format="{asctime} - {levelname} - {message}", 
                    style="{",datefmt="%Y-%m-%d %H:%M")

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

DB_NAME = "pl.db"
DB_ENV  = "test"
DB_PATH = "~/playground/intellisearch/" 
DB_TENANT = "Default_tenant"

# TODO Externalize the ENV info and connection string
def setup_db(env=DB_ENV, db_name=DB_NAME, db_path=DB_PATH):
    '''
    Set up the SQLite database that is used to store some metadata about files.
    Parameters:
        env: str - name of the environment (defaults to test)
        db_name: str - the database name (defaults to mp.db) 
        db_path: str - the file path to the directory (this is a fully qualified path)
    Returns:
        A fully formed path to the database that can be used as a connection string
    '''

    # TODO: if the path does not exist, create it first
    intellisearch_db_path = ""
    if os.name == "nt":  # Windows
        intellisearch_db_path = os.path.expandvars(r"%LOCALAPPDATA%\intellisearch\db")
    elif os.name == "posix":  # macOS/Linux
        intellisearch_db_path = os.path.expanduser(db_path+db_name)
        if not os.path.exists(intellisearch_db_path):  # Linux path fallback
            intellisearch_db_path = os.path.expanduser("~/.config/...")
    
    # Check if the search db file exists
    if not os.path.exists(intellisearch_db_path):
        logger.warning(f"Intellisearch db file not found: {intellisearch_db_path}")
    #else: create DB
    
    return intellisearch_db_path

def db_read_op(conn_db_path, query):

    if conn_db_path == None: 
        logger.error("DB READ: No DB Connection (path) specified")
        return
    
    rows = []
    try:
        conn_uri = "file:"+conn_db_path+"?immutable=1, sqlite3.OPEN_READONLY | sqlite3.OPEN_URI"
        with closing(sqlite3.connect(conn_uri, uri=True, timeout=5)) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()

    except sqlite3.Error as e:
        logger.error(f"An error occurred while accessing the database for a read op: {e}")
   
    return rows

def db_read_fetchone_op(conn_db_path, query):

    if conn_db_path == None: 
        logger.error("DB READ: No DB Connection (path) specified")
        return
    
    row = None
    try:
        conn_uri = "file:"+conn_db_path+"?immutable=1, sqlite3.OPEN_READONLY | sqlite3.OPEN_URI"
        #print("The query = ", query)
        with closing(sqlite3.connect(conn_uri, uri=True, timeout=5)) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(query)
                row = cursor.fetchone()
    except sqlite3.Error as e:
        logger.error(f"An error occurred while accessing the database for a fetchone op: {e}")
   
    return row

def db_write_op(conn_db_path, query):
    
    if conn_db_path == None: 
        logger.error("DB WRITE: No DB Connection (path) specified")
        return
     
    try:
        conn_uri = "file:"+conn_db_path+"?sqlite3.OPEN_URI"
        with closing(sqlite3.connect(conn_uri, uri=True, timeout=10)) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(query)
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"An error occurred while writing to the database: {e}")
   
def db_update_op(conn_uri, query):
    db_write_op(conn_uri, query)

def db_delete_op(conn_uri, query):
    NotImplementedError("Deletes are discouraged - allow only updates with various status")