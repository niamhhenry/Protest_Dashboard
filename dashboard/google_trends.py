import pandas as pd
import numpy as np
from pytrends.request import TrendReq
import datetime
pytrends = TrendReq(hl="en-US", tz=360)

states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", 
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

def get_week_dates(end_date):
    """
    returns dates of first day of every week between now (today) and end_date
    
    variables
    end_date: (required) string, formatted year-month-day. ex: "1998-03-08"
    """
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    today = datetime.datetime.today()
    weeks = []
    date = end_date
    while date < today:
        weeks.append(date.date())
        date = date + datetime.timedelta(days=7)
    return weeks

def create_timeframe(end_date, kw_list, country):
    """
    returns a timeframe usable in Pytrends functions between now (today) and end_date
    
    variables
    end_date: (required) string, formatted year-month-day. ex: "1998-03-08"
    """
    start = datetime.datetime.today().date().strftime("%Y-%m-%d")
    timeframe = end_date + ' ' + start
    pytrends.build_payload(kw_list, cat=0, timeframe=timeframe, geo='', gprop='')
    return timeframe

def collect_weeks(weeks, kw_list):
    """
    returns google trends data for input weeks
    caution: function might take a while to run (22 seconds on my machine)
    
    variables
    weeks: (required) list, should contain datetime objects of first day of desired weeks.
    """
    d = {}
    for i in range(len(weeks)-1):
        #set timeframe
        end = weeks[i].strftime("%Y-%m-%d")
        start = weeks[i+1].strftime("%Y-%m-%d")
        timeframe = end + ' ' + start
        
        #initialise pytrends API request
        pytrends.build_payload(kw_list, 
                               cat=0, 
                               timeframe=timeframe, 
                               geo='US',
                               gprop=''
                              )
        
        #retrieve data using pytrends API
        regional = pytrends.interest_by_region(resolution='REGION', inc_low_vol=True, inc_geo_code = False)
        
        #update dictionary with first day of week as key and data as value
        d[weeks[i]] = regional
    
    #return data in dataframe
    #df = pd.DataFrame.from_dict(d, orient='index')
    return d

def collect_trend(end_date, kw_list, country):
    """
    returns google trends data between now (today) and end_date, which returns a value per week
    """
    create_timeframe(end_date, kw_list)
    trend = pytrends.interest_over_time()
    return trend

def calculate_weekly(data, trend):
    """
    returns adjusted weekly data based on trend 
    
    variables:
    data: (required) dictionary, keys are datetime objects and values are dataframes of weekly data for all states
    trend: (required) dataframe, with date on the index and keyword interest on the first column. 
    """
    values = trend['Protest']
    values = [list(values[x:x+7]) for x in range(0, len(values), 7)]
    values = [np.mean(x) for x in values] 

    if len(values) < len(data):
        print('Not enough trend data to map to data')
        return 1;

    d = {}
    for i, date in enumerate(data):
        dates = [date for i in range(len(data[date]))]
        df = data[date]
        df['corrected'] = df['Protest'] * values[i]
        df['date'] = dates
        df['state'] = df.index
        df = df.set_index('date')
        d[date] = df
        
    return d
    
def get_trends(end_date, keywords):
    """
    end_date should be the first date in the ACLED data. Sorry.
    keywords should be list of strings. 
    """
    kw_list = keywords
    weeks = get_week_dates(end_date)
    timeframe = create_timeframe(end_date, kw_list)
    data = collect_weeks(weeks, kw_list)
    trend = collect_trend(end_date, kw_list)
    corrected = calculate_weekly(data, trend)
    df = pd.DataFrame.from_dict(corrected, orient='index')
    final_df = pd.DataFrame()

    for week in corrected:
        final_df = final_df.append(corrected[week])

    final_df['corrected'] = final_df['corrected'].apply(lambda x: x/final_df['corrected'].max())
    final_df = final_df[final_df.state != "District of Columbia"]
    final_df = final_df.drop(columns=["Protest"])

    last_week = str(final_df.index.max())

    filepath = 'google_trends_' + last_week + '.csv'

    final_df.to_csv(filepath)

    return filepath