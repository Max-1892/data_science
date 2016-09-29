import requests
import re
import pdb
import sqlite3
from bs4 import BeautifulSoup

''' { year: { tropical_storms, hurricanes, major_hurricanes, deaths, damage, notes } 
       .
       .
       .
    }
    *Damage doesn't start until the 1900s
    *Notes doesn't start until 1880s
        *Add Strongest storm and retired storms to this column
    *table name should be atlantic_hurricanes
    *table file should be hurricanes.db
'''
data = {}
numeric_col_names = ['number of tropical storms', 
                     'deaths', 
                     'number of hurricanes', 
                     'number of major hurricanes', 
                     'year', 
                     'damage usd']

def parse_table(table):
    '''This method parses an HTML table from the wikipedia page for Atlantic hurricanes.'''
    rows = table.find_all('tr')
    col_names = []
    for row_idx, row_content in enumerate(rows):
        record = {}
        if row_idx == 0:
            # Column headers, strip out HTML tags and whitespace
            pattern = re.compile('(\t|\r|\n)')
            col_names = \
                [pattern.sub(' ', ele.text.strip()).lower() for ele in row_content.find_all('th')]
        else:
            # Populate map with columns of data found under the headers
            for col_idx, col_value in enumerate(row_content.find_all('td')):
                ''' If data is part of a numeric column (defined above),
                    try to read it in as a float. This will fail if the 
                    we are trying to read values like '$25.4 million', which
                    is dealt with in the except block.
                '''
                if col_names[col_idx] in numeric_col_names:
                    try:
                        record[col_names[col_idx]] = float(col_value.text)
                    except ValueError:
                        value = col_value.text
                        if value == "Not known" or value == "Numerous" or value == "Unknown":
                            value = "NULL"
                        elif value == "None":
                            value = 0
                        else:
                            pattern = re.compile('(,|\+|\$| |~|>)')
                            value = pattern.sub('', value)
                            value = value.replace(u'\xa0', '')
                            if "million" in value:
                                value = float(value.replace("million", "")) * 1000000
                            elif "billion" in value:
                                value = float(value.replace("billion", "")) * 1000000000
                            elif "trillion" in value:
                                value = float(value.replace("trillion", "")) * 1000000000000
                            value = float(value)
                        record[col_names[col_idx]] = value
                else:
                    pattern = re.compile('("|\')')
                    record[col_names[col_idx]] = pattern.sub('"', col_value.text)
            data[int(record[col_names[0]])] = record

# Parse HTML into a soup
soup = BeautifulSoup(open('hurricanes.html'), 'html.parser')
tables = soup.find_all("table", class_="wikitable sortable")
for table in tables:
    '''Parse tables, which include the hurricane-related data
       we're interested in and populate the data list
    '''
    parse_table(table)

# Load up the sqlite3 db
conn = sqlite3.connect('hurricanes.db')
conn.execute('''CREATE TABLE ATLANTIC_HURRICANE
    (YEAR INT KEY NOT NULL,
    TROPICAL_STORMS INT,
    HURRICANES INT,
    MAJOR_HURRICANES INT,
    DEATHS INT,
    DAMAGE REAL,
    NOTES TEXT)''')

insert_scaffold = '''INSERT INTO ATLANTIC_HURRICANE
    (YEAR, TROPICAL_STORMS, HURRICANES,
    MAJOR_HURRICANES, DEATHS, DAMAGE, NOTES)
    VALUES ('''
for year in data:
    # Concatenate 'notes', 'strongest storm' and 'retired names' 
    # into one field
    notes = data[year]['notes'] if 'notes' in data[year] else ""
    notes += ("\nStrongest storm: " + data[year]['strongest storm'])
    notes += ("\nRetired names: " + data[year]['retired names']) if 'retired names' in data[year] else ""
    insert_str = insert_scaffold + \
        "%f, %f, %f, %f, %s, %s, %s)" % \
            (data[year]['year'],
            data[year]['number of tropical storms'],
            data[year]['number of hurricanes'],
            data[year]['number of major hurricanes'],
            data[year]['deaths'],
            data[year]['damage usd'] if 'damage usd' in data[year] else "NULL",
            "\'" + notes + "\'")
    conn.execute(insert_str)
conn.commit()
conn.close()
