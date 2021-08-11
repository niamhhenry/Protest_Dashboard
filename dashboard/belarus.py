import numpy as np
import pandas as pd
import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score
from stqdm import stqdm

states_blr = ["COM", "BRO", "GOO", "GRO", "MOO", "MIO", "VIO"]

state_names = ['Vitebsk Region', 'Mogilev Region', 'Minsk Region', 'Gomel Region', 'Brest Region', 'Hrodna Region']
abbreviations_blr = {
    'City of Minsk': 'COM',
    'Brest Oblast': 'BRO',
    'Gomel Oblast': 'GOO',
    'Grodno Oblast': 'GRO',
    'Mogilev Oblast': 'MOO',
    'Minsk Oblast': 'MIO',
    'Vitebsk Oblast': 'VIO'
}

def get_dates(start_date, end_date):
    """
    returns list of dates between now (today) and end_date
    
    variables
    start_date: (required) string, formatted year-month-day. must be lesser than end_date. ex: "1998-03-08"
    end_date: (required) string, formatted year-month-day. ex: "1998-03-08"
    """
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    today = datetime.datetime.today()
    dates = []
    date = start_date
    while date <= end_date:
        dates.append(datetime.datetime.strftime(date.date(), "%Y-%m-%d"))
        date = date + datetime.timedelta(days=1)
    return dates

def init_dict(dates):
    d = {}
    for date in dates:
        d[date] = {}
        for state in state_names:
            d[date][state] = 0
    return d

def construct_dataset(data, start_date, end_date):
    """
    constructs ACLED datasets into dataset that shows protest frequencies across time, per state.
    
    variables
    data: (required) dataframe, should be formatted like ACLED data
    """ 
    dates = get_dates(start_date, end_date)
    d = init_dict(dates)

    for date in dates:
        values = data[data.DATE == date]
        for state in values["STATE"]:
            d[date][state] += 1
    return d

def get_week_dates(start_date, end_date):
    """
    returns dates of first day of every week between now (today) and end_date
    
    variables
    end_date: (required) string, formatted year-month-day. ex: "1998-03-08"
    """
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    today = datetime.datetime.today()
    dates = []
    date = start_date
    while date <= end_date:
        dates.append(datetime.datetime.strftime(date.date(), "%Y-%m-%d"))
        date = date + datetime.timedelta(days=7)
        
    return dates

def sum_week(state, data):    
    state = data[data.state == state]
    state_p = list(state['protests'])
    n = 7
    l = [state_p[i * n:(i + 1) * n] for i in range((len(state_p) + n - 1) // n )] 
    weekly = []
    
    for week in l:
        weekly.append(sum(week))

    return weekly

def do(data, states, start_date, end_date):
    weeks = get_week_dates(start_date, end_date)
    output = pd.DataFrame()
    temp = pd.DataFrame()
    
    for state in states:
        protests = sum_week(state, data)
        temp['date'] = weeks
        temp['state'] = state
        temp['protests'] = protests
        temp = temp.set_index('date')
        output = output.append(temp)
    
    output = output.sort_index()
    return output

def correlate_trend(data):
    d = {}
    for state in state_names:
        state_df = data[data.state == state]
        corr = state_df['protests'].corr(state_df['corrected'])
        d[state] = corr
    
    df = pd.DataFrame.from_dict(d, orient='index')
    df = df.rename(columns={0:'correlation'})
    return df

def regression(data, X, y, transform = None, degrees = 3):
    """
    Function that applies regression to dataset, and returns a dataframe of state R2 scores. 
    
    variables:
    data: (required) dataframe, should contain at least columns X and y
    X: (required) string, column name to be selected as X data
    y: (required) string, column name to be selected as y data
    transform: (optional) string, default None, options are "log" and "sqrt", the transformation to be applied to X axis data
    degrees: (optional) int, default 3, amount of degrees on polynomial regression. Use 1 for linear regression. 
    """
    if isinstance(data, pd.DataFrame) == False:
        print("data should be a dataframe")
        return False
    
    d = {}
    for state in stqdm(state_names):
        state_name = state
        state = data[data.state == state]
        
        if transform == 'log':
            state[X] = state[X].transform('log')
        elif transform == 'sqrt':
            state[X] = state[X].transform('sqrt')
        
        X_data = np.array(state[X])
        y_data = np.array(state[y])

        regression = np.poly1d(np.polyfit(X_data, y_data, degrees))
        score = r2_score(y_data, regression(X_data))
        d[state_name] = score, regression
        
    #df = pd.DataFrame.from_dict(d, orient='index')
    #df = df.rename(columns={0:'R2'})
    return d

def prepare(trends, protests, start_date, end_date):
    protests = protests[['DATE', 'STATE']]

    protest_freq = construct_dataset(protests, start_date, end_date)
    data_dict = {}
    for date in protest_freq:
        data_dict[date] = pd.DataFrame.from_dict(protest_freq[date], orient = "index")
        data_dict[date]['date'] = date
        data_dict[date]['state'] = data_dict[date].index
        data_dict[date] = data_dict[date].set_index('date')

    final_df = pd.DataFrame()
    for week in data_dict:
        final_df = final_df.append(data_dict[week])
    final_df = final_df.rename(columns={0: 'protests'})

    state_df = do(final_df, state_names, start_date, end_date)            
    trends = trends.set_index('date')

    combined = state_df.merge(trends, on = ['date', 'state'])
    return combined

def predict(regressions_dict, data):
    d = {}
    for state in regressions_dict:
        regression = regressions_dict[state][1]
        state_data = float(data['corrected'][data['state'] == state])
        prediction = max(regression(state_data), 0)
        d[state] = prediction
    
    df = pd.DataFrame.from_dict(d, orient='index')
    df = df.rename(columns={0:'protests'})
    return df