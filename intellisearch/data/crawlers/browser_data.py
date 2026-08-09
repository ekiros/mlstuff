import logging
import os
import json
from datetime import datetime
from datetime import timedelta
from db import db_utils

# NOTE: 
# 1) Safari users need to give our app permission to access file
#       https://stackoverflow.com/questions/58479686/permissionerror-errno-1-operation-not-permitted-after-macos-catalina-update
# 
# 2) SQLite Browser fails to show hidden files in Mac - use cmd+shit+. to see hidden files in Mac

#logging.basicConfig(filename="browser.log", 
#                    filemode="a", 
#                    format="{asctime} - {levelname} - {message}", 
#                    style="{",datefmt="%Y-%m-%d %H:%M")

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

#TODO All these can be dispatched in parallel
def get_all_browser_data():
    get_browser_history_data()
    get_browser_bookmark_data()

def get_browser_history_data():
    logger.info("Starting to get browser history...")
    get_chrome_history() # store_history_data(browser_name, data)
    get_safari_history()
    get_firefox_history()
    get_edge_history()
    logger.info("Done with getting browsing history data")

def get_browser_bookmark_data():
    logger.info("Getting Bookmarks....")
    get_chrome_bookmarks() # store_bookmark_data(browser_name, data)
    get_safari_bookmarks()
    get_edge_bookmarks()
    get_firefox_bookmarks()
    logger.info("Done getting bookmarks")

def get_chrome_history():
    # Locate Chrome's History file
    history_db_path = ""
    if os.name == "nt":  # Windows
        history_db_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\History")
    elif os.name == "posix":  # macOS/Linux
        history_db_path = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/History")
        if not os.path.exists(history_db_path):  # Linux path fallback
            history_db_path = os.path.expanduser("~/.config/google-chrome/Default/History")
    
    # Check if the history file exists
    if not os.path.exists(history_db_path):
        logger.warning("Chrome history file not found.")
        return
    
    #db_utils.setup_db(env="test",db_name="History", db_path=history_db_path)

    # Check help here: https://www.codejam.info/2021/10/bypass-sqlite-exclusive-lock.html
    # new sqlite3.Database('file:db.sqlite?immutable=1', sqlite3.OPEN_READONLY | sqlite3.OPEN_URI)
    #conn_uri = "file:"+history_db_path+"?immutable=1, sqlite3.OPEN_READONLY | sqlite3.OPEN_URI"
    logger.info("=====CHROME DB PATH = "+history_db_path)

    # Query to fetch URL, title, and visit time
    query = """
    SELECT urls.url, urls.title, visits.visit_time
    FROM urls
    JOIN visits ON urls.id = visits.url
    ORDER BY visits.visit_time DESC
    LIMIT 1000;  -- Fetch the latest 100 records
    """
    
    try:
        rows = db_utils.db_read_op(history_db_path,query)
        
        # Process the data
        history = []
        for url, title, visit_time in rows:
            # Convert Chrome's timestamp to readable datetime
            # Chrome's timestamp is in microseconds since January 1, 1601
            visit_time_dt = datetime(1601, 1, 1) + timedelta(microseconds=visit_time)
            history.append({"url": url, "title": title, "visit_time": visit_time_dt})

        # Print the results
        for entry in history:
            logger.info(f"Visited: {entry['visit_time']} | Title: {entry['title']} | URL: {entry['url']}")

    except Exception as e:
        logger.error(f"An error occurred while accessing the database: {e}")

    #return history

def get_safari_history():
    # Locate Safari's History.db file
    history_db_path = os.path.expanduser("~/Library/Safari/History.db")

    # Check if the History.db file exists
    if not os.path.exists(history_db_path):
        logger.warning("Safari history database file not found.")
        return

    # Connect to the SQLite database
    #conn_uri = "file:"+history_db_path+"?immutable=1, sqlite3.OPEN_READONLY | sqlite3.OPEN_URI"
    logger.info("=====SAFARI DB PATH = "+history_db_path)

    # Query to fetch URL, title, and visit time
    query = """
    SELECT history_items.url, history_visits.visit_time, history_visits.title
    FROM history_items
    JOIN history_visits ON history_items.id = history_visits.history_item
    ORDER BY history_visits.visit_time DESC
    LIMIT 1000;  -- Fetch the latest 100 records
    """

    try:
        rows = db_utils.db_read_op(history_db_path,query)
        
        # Process the data
        history = []
        for url, visit_time, title in rows:
            # Convert Safari's timestamp to readable datetime
            # Safari's timestamp is in seconds since January 1, 2001
            visit_time_dt = datetime(2001, 1, 1) + timedelta(seconds=visit_time)
            history.append({"url": url, "title": title, "visit_time": visit_time_dt})

        # Print the results
        for entry in history:
            logger.info(f"Visited: {entry['visit_time']} | Title: {entry['title']} | URL: {entry['url']}")

    except Exception as e:
        logger.error(f"An error occurred while accessing the database: {e}")

    #return history

def get_firefox_history():
    # Locate Firefox's profile directory and places.sqlite file
    firefox_profile_dir = ""

     # Find the profile folder
    
    if os.name == "nt":  # Windows
        firefox_profile_dir = os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")
    elif os.name == "posix":  # macOS/Linux
        firefox_profile_dir = os.path.expanduser("~/Library/Application Support/Firefox/Profiles")
        if not os.path.exists(firefox_profile_dir):  # Linux path fallback
            firefox_profile_dir = os.path.expanduser("~/.mozilla/firefox")
    
    if not os.path.exists(firefox_profile_dir):
        logger.warning(f"Unable to find FF Profile directory. Looks like FF may not be installed.")
        return 
    
    profile_folders = [f for f in os.listdir(firefox_profile_dir) if f.endswith(".default") or f.endswith(".default-release")]
    if not profile_folders:
        logger.warning(f"Firefox profile folder not found: {profile_folders}")
        return
   
    places_db_path = os.path.join(firefox_profile_dir, profile_folders[0], "places.sqlite")

    # Check if the places.sqlite file exists
    if not os.path.exists(places_db_path):
        logger.warning("Firefox places.sqlite file not found.")
        return

    # Connect to the SQLite database
    #conn_uri = "file:"+places_db_path+"?immutable=1, sqlite3.OPEN_READONLY | sqlite3.OPEN_URI"
    logger.info("=====FF DB PATH = "+places_db_path)
    
    # Query to fetch URL, title, and visit time
    query = """
    SELECT moz_places.url, moz_places.title, moz_historyvisits.visit_date
    FROM moz_places
    JOIN moz_historyvisits ON moz_places.id = moz_historyvisits.place_id
    ORDER BY moz_historyvisits.visit_date DESC
    LIMIT 1000;  -- Fetch the latest 100 records
    """
    
    try:
        rows = db_utils.db_read_op(places_db_path,query)
        
        # Process the data
        history = []
        for url, title, visit_date in rows:
            # Convert Firefox's timestamp (microseconds since epoch) to readable datetime
            visit_date_dt = datetime(1970, 1, 1) + timedelta(microseconds=visit_date)
            history.append({"url": url, "title": title, "visit_time": visit_date_dt})

        # Print the results
        for entry in history:
            logger.info(f"Visited: {entry['visit_time']} | Title: {entry['title']} | URL: {entry['url']}")

    except Exception as e:
        logger.error(f"An error occurred while accessing the database: {e}")
    
    #return history


def get_edge_history():
    # Locate Edge's History database
    history_db_path = ""
    if os.name == "nt":  # Windows
        history_db_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\History")
    elif os.name == "posix":  # macOS/Linux
        history_db_path = os.path.expanduser("~/Library/Application Support/Microsoft Edge/Default/History")
        if not os.path.exists(history_db_path):  # Linux path fallback
            history_db_path = os.path.expanduser("~/.config/microsoft-edge/Default/History")

    # Check if the history file exists
    if not os.path.exists(history_db_path):
        logger.warning("Edge history database file not found.")
        return

    # Connect to the SQLite database
    #conn_uri = "file:"+history_db_path+"?immutable=1, sqlite3.OPEN_READONLY | sqlite3.OPEN_URI"
    logger.info("=====EDGE DB PATH = "+history_db_path)

    # Query to fetch URL, title, and visit time
    query = """
    SELECT urls.url, urls.title, visits.visit_time
    FROM urls
    JOIN visits ON urls.id = visits.url
    ORDER BY visits.visit_time DESC
    LIMIT 1000;  -- Fetch the latest 100 records
    """
    
    try:
        rows = db_utils.db_read_op(history_db_path,query)
        
        # Process the data
        history = []
        for url, title, visit_time in rows:
            # Convert Edge's timestamp to readable datetime
            # Edge (like Chrome) uses microseconds since January 1, 1601
            visit_time_dt = datetime(1601, 1, 1) + timedelta(microseconds=visit_time)
            history.append({"url": url, "title": title, "visit_time": visit_time_dt})

        # Print the results
        for entry in history:
            logger.info(f"Visited: {entry['visit_time']} | Title: {entry['title']} | URL: {entry['url']}")

    except Exception as e:
        logger.error(f"An error occurred while accessing the database: {e}")
    
    #return history

def get_chrome_bookmarks():
    logger.info("====Bookmarks for Chrome====")

    # Locate Chrome's Bookmarks file
    bookmarks_file_path = ""
    if os.name == "nt":  # Windows
        bookmarks_file_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Bookmarks")
    elif os.name == "posix":  # macOS/Linux
        bookmarks_file_path = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Bookmarks")
        if not os.path.exists(bookmarks_file_path):  # Linux path fallback
            bookmarks_file_path = os.path.expanduser("~/.config/google-chrome/Default/Bookmarks")

    # Check if the bookmarks file exists
    if not os.path.exists(bookmarks_file_path):
        logger.warning("Chrome bookmarks file not found.")
        return

    # Open and parse the JSON file
    try:
        with open(bookmarks_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Extract bookmarks
        bookmarks = []
        def extract_bookmarks(bookmark_folder):
            for item in bookmark_folder.get('children', []):
                if item['type'] == 'url':
                    bookmarks.append({'name': item['name'], 'url': item['url']})
                elif item['type'] == 'folder':
                    extract_bookmarks(item)

        # Start from the 'roots' section of the JSON
        roots = data.get('roots', {})
        for root in roots.values():
            if isinstance(root, dict) and 'children' in root:
                extract_bookmarks(root)

        # Print the bookmarks
        for bookmark in bookmarks:
            logger.info(f"Name: {bookmark['name']} | URL: {bookmark['url']}")

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing bookmarks file: {e}")
    except Exception as e:
         logger.error(f"An error occurred: {e}")

    #return bookmarks

def get_edge_bookmarks():
    # Locate Edge's Bookmarks file
    logger.info("====Bookmarks for Edge====")

    bookmarks_file_path = ""
    if os.name == "nt":  # Windows
        bookmarks_file_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Bookmarks")
    elif os.name == "posix":  # macOS/Linux
        bookmarks_file_path = os.path.expanduser("~/Library/Application Support/Microsoft Edge/Default/Bookmarks")
        if not os.path.exists(bookmarks_file_path):  # Linux path fallback
            bookmarks_file_path = os.path.expanduser("~/.config/microsoft-edge/Default/Bookmarks")

    # Check if the bookmarks file exists
    if not os.path.exists(bookmarks_file_path):
        logger.warning("Edge bookmarks file not found.")
        return

    # Open and parse the JSON file
    try:
        with open(bookmarks_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Extract bookmarks
        bookmarks = []
        def extract_bookmarks(bookmark_folder):
            for item in bookmark_folder.get('children', []):
                if item['type'] == 'url':
                    bookmarks.append({'name': item['name'], 'url': item['url']})
                elif item['type'] == 'folder':
                    extract_bookmarks(item)

        # Start from the 'roots' section of the JSON
        roots = data.get('roots', {})
        for root in roots.values():
            if isinstance(root, dict) and 'children' in root:
                extract_bookmarks(root)

        # Print the bookmarks
        for bookmark in bookmarks:
            logger.info(f"Name: {bookmark['name']} | URL: {bookmark['url']}")

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing bookmarks file: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

    #return bookmarks

def get_safari_bookmarks():
    logger.info("====Bookmarks for Safari====")

    import plistlib
    # Locate Safari's Bookmarks.plist file
    bookmarks_file_path = os.path.expanduser("~/Library/Safari/Bookmarks.plist")

    # Check if the Bookmarks.plist file exists
    if not os.path.exists(bookmarks_file_path):
        logger.warning("Safari bookmarks file not found.")
        return

    # Open and parse the plist file
    try:
        with open(bookmarks_file_path, 'rb') as file:
            data = plistlib.load(file)

        # Extract bookmarks
        bookmarks = []
        def extract_bookmarks(bookmark_node):
            if isinstance(bookmark_node, dict):
                # If it's a folder, process its children
                if 'Children' in bookmark_node:
                    for child in bookmark_node['Children']:
                        extract_bookmarks(child)
                # If it's a URL, extract the details
                elif 'URLString' in bookmark_node:
                    bookmarks.append({
                        'name': bookmark_node.get('URIDictionary', {}).get('title', 'No Title'),
                        'url': bookmark_node['URLString']
                    })

        # Start processing from the 'Children' key in the root
        if 'Children' in data:
            for child in data['Children']:
                extract_bookmarks(child)

        # Print the bookmarks
        for bookmark in bookmarks:
            logger.info(f"Name: {bookmark['name']} | URL: {bookmark['url']}")

    except Exception as e:
        logger.error(f"An error occurred while processing the bookmarks: {e}")
    
    return bookmarks

def get_firefox_bookmarks():
    logger.info("========Getting FireFox Bookmark data")
    # Locate the Firefox profile folder
    profile_path = ""
    if os.name == "nt":  # Windows
        profile_path = os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")
    elif os.name == "posix":  # macOS/Linux
        profile_path = os.path.expanduser("~/Library/Application Support/Firefox/Profiles")
        if not os.path.exists(profile_path):  # Linux path fallback
            profile_path = os.path.expanduser("~/.mozilla/firefox")

    if not os.path.exists(profile_path):
        logger.warning(f"Unable to find FF Profile directory. Looks like FF may not be installed.")
        return 
    
    # Locate the places.sqlite file
    places_db_path = ""
    for profile in os.listdir(profile_path):
        possible_db = os.path.join(profile_path, profile, "places.sqlite")
        if os.path.exists(possible_db):
            places_db_path = possible_db
            break

    if not places_db_path:
        logger.warning("Firefox places.sqlite database file not found.")
        return

    #conn_uri = "file:"+places_db_path+"?immutable=1, sqlite3.OPEN_READONLY | sqlite3.OPEN_URI"
    logger.info("=====FF DB PATH = "+places_db_path)

    # Query to fetch bookmarks
    query = """
    SELECT moz_bookmarks.title AS bookmark_title, 
           moz_places.url AS url, 
           moz_bookmarks.dateAdded / 1000000 AS date_added
    FROM moz_bookmarks
    JOIN moz_places ON moz_bookmarks.fk = moz_places.id
    WHERE moz_bookmarks.type = 1  -- 1 indicates a bookmark
    ORDER BY date_added DESC
    LIMIT 100;  -- Fetch the latest 100 bookmarks
    """

    try:
        # Connect to the SQLite database
        rows = db_utils.db_read_op(places_db_path,query)
        
        # Process and display the bookmarks
        bookmarks = []
        for title, url, date_added in rows:
            date_added_dt = datetime(1970, 1, 1) + timedelta(seconds=date_added)
            #bookmarks.append({'title': title, 'url': url, 'date_added': date_added_dt})
            bookmarks.append({'name': title, 'url': url})

        # Print the bookmarks
        for bookmark in bookmarks:
            #logger.info(f"Title: {bookmark['title']} | URL: {bookmark['url']} | Date Added: {bookmark['date_added']}")
            logger.info(f"Name: {bookmark['title']} | URL: {bookmark['url']}")

    except Exception as e:
        logger.error(f"An error occurred while accessing the database: {e}")
    
    #return bookmark

#if __name__ == '__main__':
#    main()