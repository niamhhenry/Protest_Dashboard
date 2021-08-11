#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests

import pandas as pd
import numpy as np


# In[2]:


# necessary for the countlove clean-up

states_dict = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PR': 'Puerto Rico',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
}


# In[3]:


def download_csv(url):
    csv_url = url
    
    req = requests.get(csv_url)
    url_content = req.content
    csv_file = open('downloaded.csv', 'wb')

    csv_file.write(url_content)
    csv_file.close()
    
def download_xlsx(url):
    xlsx_url = url

    req = requests.get(xlsx_url)
    url_content = req.content
    xlsx_file = open('downloaded.xlsx', 'wb')

    xlsx_file.write(url_content)
    xlsx_file.close()            


# In[23]:


# 3 separate functions to first download, read-in and clean the specific dataset. 



# In[ ]:


# attempt at wrapping the entire integration into a single function. A for loop runs through a list of urls, 
# an if-statement verifies the url being processed to pick the right download and cleaning function. 
# The error if you try to use it is currently ValueError: too many values to unpack (expected 3)

"""
def integrate_data(urls):
    for url in urls:
        if url == 'https://mappingpoliceviolence.org/s/MPVDatasetDownload.xlsx':
            download_xlsx(url)  
            df_police_violence = pd.read_excel('downloaded.xlsx')
            df_police_violence = clean_police(df_police_violence)
            return df_police_violence
        elif url == 'https://acleddata.com/download/22846/':
            download_xlsx(url)
            df_acled = pd.read_excel('downloaded.xlsx')
            df_acled = clean_acled(df_acled)
            return df_acled
        else:
            download_csv(url)
            df_countlove = pd.read_csv('downloaded.csv')
            df_countlove = clean_countlove(df_countlove)
            return df_countlove 
"""


# In[5]:


def clean_countlove(df):
    df = df.rename(columns= {'Date':'DATE', 'Location':'LOCATION', 'Attendees': 'ATTENDEES', 'Source': 'ARTICLE'})
    df['DATE']=pd.to_datetime(df['DATE'])
    df['LOCATION'] = df["LOCATION"].apply(lambda x: x.split(","))
    df['CITY'] = df['LOCATION'].apply(lambda x: " ".join(x[0].split()[0:]))
    df['STATE'] = df['LOCATION'].apply(lambda x: x[-1].split()[0])
    df = df.drop(['LOCATION'], axis=1).reset_index(drop=True)
    df = df[df.STATE.isin(states_dict.keys())]
    df['STATE'] = df['STATE'].apply(lambda x: states_dict[x])
    return df

#function to obtain count_protests(COUNTLOVE) file
def count_protests(data):
    data = data[['DATE', 'STATE']]
    data['Year']=data.DATE.dt.year
    data['Month']=data.DATE.dt.month
    data['WeekNr']=data.DATE.dt.weekofyear
    data['index']=data.index
    #count protests per month and year in each state
    data = data.merge(data.groupby([data.STATE, data.Year, data.Month])['index'].count(),
                      how='left', left_on=[data.STATE, data.Year, data.Month],
                      right_index=True).rename(columns={'index_y':'NrProtestPerMonthByState', 'index_x': 'index'})
    #count protests per week and year in each state
    data = data.merge(data.groupby([data.STATE, data.Year, data.WeekNr])['index'].count(),
                      how='left', left_on=[data.STATE, data.Year, data.WeekNr],
                      right_index=True).rename(columns={'index_y':'NrProtestPerWeekNrByState', 'index_x': 'index'})
    data = data.drop(['index'], axis=1).reset_index(drop=True)
    return data


# In[6]:


#function to obtain ACLED_final
def clean_acled(df):
    df = df.drop(['ISO', 'EVENT_ID_NO_CNTY', 'TIME_PRECISION', 'ADMIN3', 'REGION', 'COUNTRY', 'YEAR'], axis=1).reset_index(drop=True)
    df['INTER1'] = df['INTER1'].replace([0, 1, 2, 3, 4, 5, 6, 7, 8], 
                                        ['NaN','State Forces', 'Rebel Groups', 'Political Militias', 'Identity Militias',
                                              'Rioters', 'Protesters', 'Civilians', 'Other Forces'])
    df['INTER2'] = df['INTER2'].replace([0, 1, 2, 3, 4, 5, 6, 7, 8], ['NaN','State Forces', 'Rebel Groups', 'Political Militias', 'Identity Militias',
                                              'Rioters', 'Protesters', 'Civilians', 'Other Forces'])
    df['INTERACTION_VALUE'] = df['INTERACTION'].replace([10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 22, 23, 24, 25, 
                                                 26, 27, 28, 30, 33, 34, 35, 36, 37, 38, 40, 44, 45, 46, 47, 48, 50, 55, 56, 57, 58, 60, 
                                                66, 67, 68, 78, 80], ['SOLE MILITARY ACTION', 'MILITARY VERSUS MILITARY', 'MILITARY VERSUS REBELS', 'MILITARY VERSUS POLITICAL MILITIA', 'MILITARY VERSUS COMMUNAL MILITIA',
                                                                      'MILITARY VERSUS RIOTERS', 'MILITARY VERSUS PROTESTERS', 'MILITARY VERSUS CIVILIANS', 'MILITARY VERSUS OTHER', 'SOLE REBEL ACTION', 'REBELS VERSUS REBELS', 
                                                                      'REBELS VERSUS POLITICAL MILIITA', 'REBELS VERSUS COMMUNA MILITIA', 'REBELS VERSUS RIOTERS', 'REBELS VERSUS PROTESTERS', 'REBELS VERSUS CIVILIANS', 
                                                                      'REBELS VERSUS OTHERS', 'SOLE POLITICAL MILITIA ACTION', 'POLITICAL MILITIA VERSUS POLITICAL MILITIA', 'POLITICAL MILITIA VERSUS COMMUNAL MILITIA',
                                                                      'POLITICAL MILITIA VERSUS RIOTERS', 'POLITICAL MILITIA VERSUS PROTESTERS', 'POLITICAL MILITIA VERSUS CIVILIANS', 'POLITICAL MILITIA VERSUS OTHERS',
                                                                      'SOLE COMMUNAL MILITIA ACTION', 'COMMUNAL MILITIA VERSUS COMMUNAL MILITIA', 'COMMUNAL MILITIA VERSUS RIOTERS', 'COMMUNAL MILITIA VERSUS PROTESTERS',
                                                                      'COMMUNAL MILITIA VERSUS CIVILIANS', 'COMMUNAL MILITIA VERSUS OTHER', 'SOLE RIOTER ACTION', 'RIOTERS VERSUS RIOTERS', 'RIOTERS VERSUS PROTESTERS', 
                                                                      'RIOTERS VERSUS CIVILIANS', 'RIOTERS VERSUS OTHERS', 'SOLE PROTESTER ACTION', 'PROTESTERS VERSUS PROTESTERS', 'PROTESTERS VERSUS CIVILIANS', 'PROTESTERS VERSUS OTHER',
                                                                      'OTHER ACTOR VERSUS CIVILIANS', 'SOLE OTHER ACTION'])
    #df['EVENT_DATE'] = pd.to_datetime(df['EVENT_DATE'])
    df.rename(columns = {'ADMIN1':'STATE', 'ADMIN2': 'COUNTY', 'LOCATION': 'CITY', 'EVENT_DATE': 'DATE'}, inplace = True)

    #finds counter protests
    df.loc[:, 'COUNTER PROTESTS'] = df.apply(lambda row: 1 if ((((str(row['ASSOC_ACTOR_1']).startswith('BLM')) | 
                                                                                                                                (str(row['ASSOC_ACTOR_1']).startswith('African'))|
                                                                                                                                (str(row['ASSOC_ACTOR_1']).startswith('Antifa'))) 
                                                           & ((str(row['ASSOC_ACTOR_2']).startswith('White')) | (str(row['ASSOC_ACTOR_2']).startswith('Proud Boys')) |
                                                              (str(row['ASSOC_ACTOR_2']).startswith('Patriot Prayer')) | (str(row['ASSOC_ACTOR_2']).startswith('Free Ohio Now')) |
                                                              (str(row['ASSOC_ACTOR_2']).startswith('Boogaloo Bois')) | (str(row['ASSOC_ACTOR_2']).startswith('Oath Keepers')) |
                                                              (str(row['ASSOC_ACTOR_2']).startswith('KKK')) |(str(row['ASSOC_ACTOR_2']).startswith('ACB'))))) |
                                             ((((str(row['ASSOC_ACTOR_2']).startswith('BLM')) | 
                                                                                                                                (str(row['ASSOC_ACTOR_2']).startswith('African'))|
                                                                                                                                (str(row['ASSOC_ACTOR_2']).startswith('Antifa'))) 
                                                           & ((str(row['ASSOC_ACTOR_1']).startswith('White')) | (str(row['ASSOC_ACTOR_1']).startswith('Proud Boys')) |
                                                              (str(row['ASSOC_ACTOR_1']).startswith('Patriot Prayer')) | (str(row['ASSOC_ACTOR_1']).startswith('Free Ohio Now')) |
                                                              (str(row['ASSOC_ACTOR_1']).startswith('Boogaloo Bois')) | (str(row['ASSOC_ACTOR_1']).startswith('Oath Keepers')) |
                                                              (str(row['ASSOC_ACTOR_1']).startswith('KKK')) |(str(row['ASSOC_ACTOR_1']).startswith('ACB')))))
                                                                             else 0, axis=1)
    df['DAYS_SINCE_LAST']=df.groupby('CITY')['DATE'].diff(-1)* (-1)
    df = df[['DATE','EVENT_TYPE','SUB_EVENT_TYPE','ACTOR1', 'ASSOC_ACTOR_1','INTER1','ACTOR2','ASSOC_ACTOR_2','INTER2','INTERACTION','INTERACTION_VALUE','STATE','COUNTY',
             'CITY','LATITUDE','LONGITUDE','COUNTER PROTESTS','DAYS_SINCE_LAST','FATALITIES', 'NOTES']]
    return df


# In[7]:


#function to obtain clean_PoliceViolence file
def clean_police(df):
    df.drop(df.columns[[1, 2, 4, 6, 9, 12, 18,19, 21]], axis = 1, inplace = True) 
    df.drop(df.columns[[9,10,11,12,13,14,15,16,17,18,19]], axis = 1, inplace = True)
    df.drop(df.columns[[9,10,11,12,13,14,15]], axis = 1, inplace = True) 
    df.columns = ["Name", "Race", 'Event_Date', 'City', 'State', 'County', 'Agency', 'Cause of death', 'Brief Description']
    df['Event_Date'] = pd.to_datetime(df['Event_Date'])
    df = df.dropna(subset=['City'])
    return df


# In[20]:


def clean_belarus(df):
    df = df.drop(['iso', 'event_id_cnty', 'time_precision', 
                  'admin3', 'region', 'country', 'year', 'data_id', 
                  'event_id_no_cnty', 'geo_precision', 
                  'source', 'source_scale', 'timestamp', 'iso3'], axis=1).reset_index(drop=True)
    
    df['inter1'] = df['inter1'].replace([0, 1, 2, 3, 4, 5, 6, 7, 8], 
                                        ['NaN','State Forces', 'Rebel Groups', 'Political Militias', 'Identity Militias',
                                              'Rioters', 'Protesters', 'Civilians', 'Other Forces'])
    df['inter2'] = df['inter2'].replace([0, 1, 2, 3, 4, 5, 6, 7, 8], ['NaN','State Forces', 'Rebel Groups', 'Political Militias', 'Identity Militias',
                                              'Rioters', 'Protesters', 'Civilians', 'Other Forces'])
    df['interaction'] = df['interaction'].replace([10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 22, 23, 24, 25, 
                                                 26, 27, 28, 30, 33, 34, 35, 36, 37, 38, 40, 44, 45, 46, 47, 48, 50, 55, 56, 57, 58, 60, 
                                                66, 67, 68, 78, 80], ['SOLE MILITARY ACTION', 'MILITARY VERSUS MILITARY', 'MILITARY VERSUS REBELS', 'MILITARY VERSUS POLITICAL MILITIA', 'MILITARY VERSUS COMMUNAL MILITIA',
                                                                      'MILITARY VERSUS RIOTERS', 'MILITARY VERSUS PROTESTERS', 'MILITARY VERSUS CIVILIANS', 'MILITARY VERSUS OTHER', 'SOLE REBEL ACTION', 'REBELS VERSUS REBELS', 
                                                                      'REBELS VERSUS POLITICAL MILIITA', 'REBELS VERSUS COMMUNA MILITIA', 'REBELS VERSUS RIOTERS', 'REBELS VERSUS PROTESTERS', 'REBELS VERSUS CIVILIANS', 
                                                                      'REBELS VERSUS OTHERS', 'SOLE POLITICAL MILITIA ACTION', 'POLITICAL MILITIA VERSUS POLITICAL MILITIA', 'POLITICAL MILITIA VERSUS COMMUNAL MILITIA',
                                                                      'POLITICAL MILITIA VERSUS RIOTERS', 'POLITICAL MILITIA VERSUS PROTESTERS', 'POLITICAL MILITIA VERSUS CIVILIANS', 'POLITICAL MILITIA VERSUS OTHERS',
                                                                      'SOLE COMMUNAL MILITIA ACTION', 'COMMUNAL MILITIA VERSUS COMMUNAL MILITIA', 'COMMUNAL MILITIA VERSUS RIOTERS', 'COMMUNAL MILITIA VERSUS PROTESTERS',
                                                                      'COMMUNAL MILITIA VERSUS CIVILIANS', 'COMMUNAL MILITIA VERSUS OTHER', 'SOLE RIOTER ACTION', 'RIOTERS VERSUS RIOTERS', 'RIOTERS VERSUS PROTESTERS', 
                                                                      'RIOTERS VERSUS CIVILIANS', 'RIOTERS VERSUS OTHERS', 'SOLE PROTESTER ACTION', 'PROTESTERS VERSUS PROTESTERS', 'PROTESTERS VERSUS CIVILIANS', 'PROTESTERS VERSUS OTHER',
                                                                      'OTHER ACTOR VERSUS CIVILIANS', 'SOLE OTHER ACTION'])
    
    
    
    df.rename(columns = {'admin1':'state', 'admin2': 'county', 'location': 'city', 'event_date': 'date'}, inplace = True)

    df = df.iloc[1:]
    df['date'] = pd.to_datetime(df['date'])
        
    df['days_since_last']=df.groupby('city')['date'].diff(-1)*(-1)
    
    return df

def integrate_police_data(url):
    download_xlsx(url)  
    df_police_violence = pd.read_excel('downloaded.xlsx')
    df_police_violence = clean_police(df_police_violence)
    return df_police_violence

def integrate_acled_data(url):
    print("Downloading data...")
    download_xlsx(url)
    print("Reading data...")
    df_acled = pd.read_excel('downloaded.xlsx')
    print("Cleaning data...")
    df_acled = clean_acled(df_acled)
    print("Done, returning")
    return df_acled

def integrate_countlove_data(url):
    download_csv(url)
    df_countlove = pd.read_csv('downloaded.csv')
    df_countlove = clean_countlove(df_countlove)
    return df_countlove

def integrate_belarus_data(url):
    download_csv(url)
    df_belarus = pd.read_csv('downloaded.csv')
    df_belarus = clean_belarus(df_belarus)
    return df_belarus