import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import datetime
import correlations as c
import google_trends as gt
import state_exploration as se
from stqdm import stqdm
from time import sleep
from states import states, abbreviations
import plotly.graph_objects as go
from pytrends.request import TrendReq
from tkinter.filedialog import askopenfilename

pytrends = TrendReq(hl="en-US", tz=360)

st.sidebar.write("""
  ## Public unrest: protests
    """)

acled = pd.read_csv('states_cleaned_final.csv')
cops = acled[['State', 'TotalLawEnforcementEmployees_per1000']]

protests = pd.read_csv('ACLED_final.csv') 



view = st.sidebar.radio('View', ['Heatmap', 'Demographics'])
#violent = protests[protests['violent'] == 'yes']
@st.cache
def find_monday(date):
  """
  finds next monday after specified date

  variable date should be a datetime object in the format of "2020-05-01".
  """
  date = datetime.datetime.strptime(date, "%Y-%m-%d")
  day = date.weekday()

  newdate = date + datetime.timedelta(days=7 - day)

  newdate = newdate.strftime("%Y-%m-%d")
  return newdate

@st.cache
def init_calendar(data):
  """
  returns start date and end date given protests dataset in string format

  data should be a dataframe with "DATE" on the index or column
  """
  start_date = data[['DATE']].min()[0]
  start_date = '2020-05-01'
  start_date = find_monday(start_date)
  end_date = data[['DATE']].max()[0]
  return start_date, end_date

def collect_weeks(weeks, kw_list):
    """
    returns google trends data for input weeks
    caution: function might take a while to run (22 seconds on my machine)
    
    variables
    weeks: (required) list, should contain datetime objects of first day of desired weeks.
    """
    d = {}
    progress = 0.0
    part = 100 / (len(weeks) - 1) / 100
    for i in range(len(weeks)-1):
        #set timeframe
        end = weeks[i].strftime("%Y-%m-%d")
        start = weeks[i+1].strftime("%Y-%m-%d")
        timeframe = end + ' ' + start
        print("Fetching {}...".format(timeframe))
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
        status_text.text('Fetching week {}'.format(start))
        progress += part
        progress_bar.progress(progress)
    #return data in dataframe
    #df = pd.DataFrame.from_dict(d, orient='index')
    return d

def get_trends(end_date, keywords):
    """
    end_date should be the first date in the ACLED data. Sorry.
    keywords should be list of strings. 
    """
    kw_list = keywords
    weeks = gt.get_week_dates(end_date)
    timeframe = gt.create_timeframe(end_date, kw_list)
    print('timeframe: ', timeframe)
    data = collect_weeks(weeks, kw_list)
    trend = gt.collect_trend(end_date, kw_list)
    status_text.text('Calculating weekly frequencies...')
    print('data', data)
    print('trend', trend.head)

    corrected = gt.calculate_weekly(data, trend)
    df = pd.DataFrame.from_dict(corrected, orient='index')
    final_df = pd.DataFrame()

    for week in corrected:
        final_df = final_df.append(corrected[week])

    final_df['corrected'] = final_df['corrected'].apply(lambda x: x/final_df['corrected'].max())
    final_df = final_df[final_df.state != "District of Columbia"]
    col = final_df.columns[0]
    print('Dropping column "{}"'.format(col))
    final_df = final_df.drop(columns=col)

    last_week = str(final_df.index.max())

    filepath = 'google_trends_' + last_week + '.csv'

    status_text.text('Finishing up DataFrame...')
    final_df.to_csv(filepath)

    progress_bar.progress(1.0)
    status_text.text('Done')

    return filepath

@st.cache
def fetch_trends(start_date, keyword):
  print(start_date)
  file = get_trends(start_date, [keyword])
  trends = pd.read_csv(file)
  return trends, keyword

if view == 'Heatmap':
  st.write("""
  ## Weekly view
    """)

  topleft, topright = st.beta_columns(2)

  keyword = topleft.text_input('Define keyword', value = "Protest")
  
  start_date, end_date = init_calendar(protests)

  progress_bar = st.progress(0)
  status_text = st.empty()

  trends = pd.read_csv('google_trends_2021-01-11.csv')
  topright.write("## ")    

  weeks = c.get_week_dates(start_date, end_date)

  data = c.prepare(trends, protests, start_date, end_date)

  keyword_list = pd.read_csv('keywords.csv')

  correlations = c.correlate_trend(data)

  if topright.button("Run keyword"):
    trends, keyword = fetch_trends(start_date, keyword)
    data = c.prepare(trends, protests, start_date, end_date)
    correlations = c.correlate_trend(data)
    keyword_list = keyword_list.append({'keyword':keyword, 'correlation':correlations.mean()[0]}, ignore_index=True)

    keyword_list.to_csv('keywords.csv', index=False)

  st.write("Average correlation ({}): {}".format(keyword, correlations['correlation'].mean()))

  st.write('Previous searches')
  st.write(keyword_list.tail(5))

  midleft, midright = st.beta_columns(2)
  
  transform = midleft.radio('Transform protest data:', ['None', 'Log2'])
  degrees = midright.radio('Polynomial regression degree:', [1, 2, 3])

  if transform == 'Log2':
    data['log2_protests'] = data['protests'].apply(lambda x: 0 if x in (0, 1) else np.log2(x)) 
    regressions = c.regression(data, 'corrected', 'log2_protests', degrees=degrees)
    plotcol = 'log2_protests'
  else: 
    regressions = c.regression(data, 'corrected', 'protests', degrees=degrees)
    plotcol = 'protests'

  left_col, right_col = st.beta_columns(2)

  button = left_col.radio('Choose view', ['Protests per 100k', 'Number of protests', 'Cops per protest'])

  date = right_col.selectbox("Select week: ", weeks)

  trend_data = trends[trends['date'] == date]
  predictions = c.predict(regressions, trend_data)

  pops = acled[['State', 'Pop2020']]
  pops = pops.rename(columns={'State':'state'})

  df = pd.DataFrame()
  df['state'] = predictions.index
  df['locations'] = df['state'].apply(lambda x: abbreviations[x])
  x = list(predictions['protests'])
  df['protests'] = x

  actual = list(data['protests'][data.index == date])
  df['actual_protests'] = actual
  df['error'] = df['actual_protests'] - df['protests']

  legend_text = 'Protests'

  title_text = 'Estimated number of protests per state for week of {}'.format(date)
  if button == 'Protests per 100k':
    df['protests'] = df['protests'] / pops['Pop2020'] * 100000
    title_text = 'Estimated protests for week of {}, per 100k inhabitants'.format(date)
    legend_text = 'Protests'
  elif button == 'Cops per protest':
    legend_text = 'Cops'
    title_text = 'Law enforcement employees per estimated protest for week of {}'.format(date)
    df['protests'] = df['protests'] / pops['Pop2020'] * 1000
    df['protests'] = cops['TotalLawEnforcementEmployees_per1000'] / df['protests'] 

  fig = px.choropleth(df,  # Input Pandas DataFrame
                      locations="locations",  # DataFrame column with locations
                      color="protests",  # DataFrame column with color values
                      hover_name="state", # DataFrame column hover info
                      color_continuous_scale = "Reds", 
                      locationmode = 'USA-states', # Set to plot as US States
                      hover_data = {'state':False,
                                    'protests':True,
                                    'error':True
                                    },
                      labels={'protests':legend_text}
                      )
  fig.update_layout(
      title_text = title_text, # Create a Title
      geo_scope='usa',  # Plot only the USA instead of globe
      hoverlabel=dict(
        bgcolor="white",
        font_size=16,
        font_family="consolas"
        )
  )

  fig

  st.write(""" ### Explore state correlations """)
  state = st.selectbox("Select state: ", list(abbreviations))

  state_data = data[data['state'] == state]

  state_pop = pops['Pop2020'][pops['state'] == state].values[0]
  print(state_pop)
  state_data['protests_per_capita'] = state_data['protests'] / state_pop * 100000
  print(state_data['protests_per_capita'])

  trendplot = go.Figure(layout = {'template': 'plotly_white'})

  trendplot.add_trace(go.Scatter(x=state_data.index, y=state_data['corrected'], mode='lines', name='Google Trend'))

  trendplot.add_trace(go.Scatter(x=state_data.index, y=state_data['protests_per_capita'], mode='lines', name='Protests'))

  trendplot.update_layout(title = "Google trends data ('{}') and protests against time".format(keyword),
                   
                   yaxis_title = "Keyword ({})/protest frequency".format(keyword),
                   legend_title = "Legend")

  st.write(trendplot)

  top = state_data['corrected'].max()
  model = regressions[state][1]
  line = np.linspace(0, top, 100)
  state_pred = predictions[predictions.index == state]
  point = state_data[state_data.index == date]

  #transformation = 'None'
  #if transformation == 'Log2':


  pl = go.Figure(layout = {'template': 'plotly_white'})

  pl.add_trace(go.Scatter(x=state_data['corrected'], y=state_data[plotcol], mode='markers', name="Datapoint"))
  pl.add_trace(go.Scatter(x=line, y=model(line), mode='lines', name="Regression"))
  pl.add_trace(go.Scatter(x=point['corrected'], y=model(point['corrected']), mode='markers', name=date))

  pl.update_layout(title = "Visualized regression of Google trends data vs. protest frequency",
                   xaxis_title = "Relative keyword frequency",
                   yaxis_title = "Protest count ({})".format(transform),
                   legend_title = "Legend")

  st.write(pl)

else: 
  st.write("""
  ## Yearly view
    """)
  acled, cols = se.prep(acled)

  cols = st.multiselect('Choose factors to correlate with yearly protests', cols)

  corrs = se.calc_corr(acled, cols)
  corrs