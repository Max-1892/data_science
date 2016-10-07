import numpy as np
import pandas as pd
import sqlalchemy
import pdb
import re

# Read in xls, indices are 1,...,37
dict_of_df = pd.read_excel('data.xls', sheetname=None, parse_cols=[0,1,2])
contractors = []
actions_df = pd.DataFrame(columns=['Number of Actions', 'Dollars Obligated', 'department', 'contractor_id'])
for department_name in dict_of_df.keys():
    if department_name != "Federal":
        # Record contractor names
        names = dict_of_df[department_name]['Global Vendor Name'].values
        for name in names:
            if not name in contractors:
                contractors.append(name)
        # Get id of contractor names
        contractor_ids = []
        for contractor in dict_of_df[department_name]['Global Vendor Name']:
            contractor_ids.append(contractors.index(contractor))
        contractor_ids = pd.Series(contractor_ids)
        # Create a dataframe with department, # of actions, dollars obligated, and contractor ids 
        new_department_df = pd.DataFrame( 
            dict_of_df[department_name].loc[:,['Number of Actions', 'Dollars Obligated']])
        new_department_df['department'] = department_name
        new_department_df['contractor_id'] = contractor_ids
        actions_df = actions_df.append(new_department_df, ignore_index=True)

# Create and connect to DB
conn = sqlalchemy.create_engine('sqlite:///government_jobs')

# Create CONTRACTORS table
contractors = pd.DataFrame(contractors)
contractors.columns = ['contractor']
contractors.to_sql('contractors', conn, if_exists='replace', 
    dtype={'contractor':sqlalchemy.types.String})

# Create ACTIONS table
actions_df.columns = ['actions', 'dollars', 'department', 'contractor_id']
actions_df.to_sql('actions', conn, flavor='sqlite', if_exists='replace', 
    dtype={'department': sqlalchemy.types.String,
        'actions': sqlalchemy.types.Integer,
        'dollars': sqlalchemy.types.Float,
        'contractor_id': sqlalchemy.types.Integer})

