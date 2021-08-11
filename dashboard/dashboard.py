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
from states import states, abbreviations, fullnames
import plotly.graph_objects as go
from pytrends.request import TrendReq
from tkinter.filedialog import askopenfilename
from rename_columns import rename_cols
from sklearn import linear_model
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import data_integration as di
import belarus as b

#st.set_page_config(layout="wide")

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

def collect_weeks(weeks, kw_list, country):
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
        timeframe = end + " " + start
        print("Fetching {}...".format(timeframe))
        #initialise pytrends API request
        pytrends.build_payload(kw_list, 
                               cat=0, 
                               timeframe=timeframe, 
                               geo=country,
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

def get_trends(end_date, keywords, country):
    """
    end_date should be the first date in the ACLED data. Sorry.
    keywords should be list of strings. 
    """
    kw_list = keywords
    weeks = gt.get_week_dates(end_date)
    timeframe = gt.create_timeframe(end_date, kw_list, country)
    print('timeframe: ', timeframe)
    data = collect_weeks(weeks, kw_list, country)
    trend = gt.collect_trend(end_date, kw_list, country)
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

    filepath = 'google_trends_' + last_week + country + '.csv'

    status_text.text('Finishing up DataFrame...')
    final_df.to_csv(filepath)

    progress_bar.progress(1.0)
    status_text.text('Done')

    return filepath

@st.cache
def fetch_trends(start_date, keyword, country):
  print(start_date)
  file = get_trends(start_date, [keyword], country)
  trends = pd.read_csv(file)
  return trends, keyword

pytrends = TrendReq(hl="en-US", tz=360)

downloadbox = st.sidebar.beta_expander("Update protest data")
downloadbox.write("Pressing this button allows for grabbing up to date protest data from ACLED. Might take a while.")
download = downloadbox.button("Update data")

if download:
  protests = di.integrate_acled_data('https://acleddata.com/download/22846/')
  belarus = di.integrate_belarus_data('https://data.humdata.org/dataset/96267a9e-c628-4a54-8aa5-e17d022c2573/resource/185fae7c-ce67-4b11-ab80-8e31d8760de3/download/conflict_data_blr.csv')
  print('Downloading new protest data')
  belarus.to_csv('belarus.csv')
  protests.to_csv('ACLED_final.csv')

#df_police = integrate_police_data('https://mappingpoliceviolence.org/s/MPVDatasetDownload.xlsx')

acled = pd.read_csv('states_cleaned_final.csv')
protests = pd.read_csv('ACLED_final.csv')
start_date, end_date = init_calendar(protests)

uploadbox = st.sidebar.beta_expander("Upload file")
uploadbox.write("Select a csv file to attach it to the existing dataset. Uploaded file should contain a column 'State' with all 50 states and their full names.")
uploaded = uploadbox.file_uploader("Choose a csv file")

if uploaded is not None:
  new_df = pd.read_csv(uploaded)
  acled = acled.merge(new_df, how='left', on='State')

peaceful = protests[protests.SUB_EVENT_TYPE == 'Peaceful protest']
violent = protests[protests.SUB_EVENT_TYPE != 'Peaceful protest']

#trends = pd.read_csv('google_trends_2021-01-18.csv')


#violent_prep = c.prepare( trends, violent, start_date, end_date)
#violent_prep = violent_prep.rename(columns={'protests':'violent'})
#violent_protests = list(violent_prep['violent'])
#peaceful_prep = c.prepare( trends, peaceful,start_date, end_date)
#peaceful_prep['violent'] = violent_protests
#peaceful_prep['total'] = peaceful_prep['protests'] + peaceful_prep['violent']
#peaceful_prep['%violent'] = peaceful_prep['violent'] / peaceful_prep['total']
#peaceful_prep = peaceful_prep.fillna(0)

#violentperc = peaceful_prep[['state', '%violent', 'corrected']]
#violentperc = violentperc.rename(columns={'%violent':'protests'})
#st.write(violentperc.head())

#cors = c.correlate_trend(violentperc)
#st.write(cors)

pops = acled[['State', 'Pop2020']]
pops = pops.rename(columns={'State':'state'})

cops = acled[['State', 'TotalLawEnforcementEmployees_per1000']] 
st.markdown("""
    <style>
    .maintitle {
        font: 60px Consolas, monaco, monospace;
        text-transform: uppercase;
        color: #000099;
        background-color:  white;
        line-height: 90%;
        margin: .2em 0 .4em 0;
        letter-spacing: 2px;
        text-align: center;
        padding: 20px;
        box-shadow: 5px 5px 5px 5px #888888;
        
    }
    .info {
        
        letter-spacing: 1px;
        color: #000080;
        font-size: 15px;
        font-family: "Lucida Grande", Verdana, Helvetica, Arial, sans-serif;
        font-weight: 100;
        
    }    
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
    .section {
        color: black; 
        font: 60px Consolas, monaco, monospace;
        letter-spacing: 1px;
        font-size: 45px; 
        font-weight: 400;
        border-bottom: 3px solid #cc0000;
        text-align: center;
        text-transform: uppercase;
        padding: 10px;
        '
       }
     .text {
         color: #111
         font-family: "Consolas";
         font-size: 22px; 
         line-height: 24px; 
         margin: 0 0 24px; 
         text-align: justify; 
         text-justify: inter-word;
     }  
     </style>
           """, unsafe_allow_html=True)

st.markdown('<p class="maintitle">US Protest Dashboard</p>', unsafe_allow_html=True) 

#sidebar
st.sidebar.title('Navigator')
view = st.sidebar.radio('Select to view page:', ['Google Trends factor estimation', 'State factors comparison', 'Combined factors estimation', 'Belarus Google Trends'])

st.sidebar.write("""## About  """)
about_google = st.sidebar.beta_expander('Google Trends factor estimation')
with about_google:
    st.write("Search keyword terms related to public unrest to show how volume of searches historically indicates public unrest.")

about_cond = st.sidebar.beta_expander('State factor comparison')
with about_cond:
    st.write("Compare, analyse and discover the societal conditions underlying states, and the number of protests they hosted in the year.")

about_estimate = st.sidebar.beta_expander('Combined factors estimation')
with about_estimate:
    st.write("Run our protest model with your own featured variables to estimate the number of protests in a state.")    



if view == 'Belarus Google Trends':
    st.markdown('<p class="section">Belarus Google Trends Validation</p>', unsafe_allow_html=True)    
    keyword = st.text_input("Define Keyword Term", value="протест")
    belarus = pd.read_csv('belarus.csv')
    
    belarus = belarus.sort_values(by='date')
    progress_bar = st.progress(0)
    status_text = st.empty()
    belarus = belarus[belarus["date"] >= start_date]
    belarus.loc[belarus['state'] == 'Grodno', 'state'] = 'Hrodna'
    belarus['state'] = belarus['state'].apply(lambda x: x + ' Region')

    belarus = belarus.rename(columns={'date':'DATE', 'state':'STATE'})

    trends, keyword = fetch_trends(start_date, keyword, "BY")

    #temp['state'] = temp['state'].apply(lambda x: x.split(" ")[0])
    data = b.prepare(trends, belarus, start_date, end_date)

    correlations = b.correlate_trend(data)
    correlations
#state conditions page
if view == 'State factors comparison':
    st.markdown('<p class="section">State factors comparison</p>', unsafe_allow_html=True)

    #show actual historical protests on the map and tooltip to include count of protests for year or selected week
    col_1, col_2, col_3 = st.beta_columns([1,3,1])
    #map

    #for options to display values on map - absolute = raw, relative = ranked 1-50
    #protest_values = st.radio("Select Values:" ['Absolute', 'Relative'])

    # #type of event - can move to sidebar or elsewhere    
    # col_3.subheader('Select Type of Events to Include:')  
    # only_peace = col_3.checkbox('Only Peaceful Protests')    
    # only_violent = col_3.checkbox('Only Violent Protests')    
    # #if == all_events: all events selected
    # #if == only_peace:just peaceful selected
    # #if == only_violent:just violent selected
    # if only_peace:
    #   protests = peaceful
    # if only_violent:
    #   protests = violent


    #run demographic correlations here
    st.markdown('<p class="info">Select variables to find correlations between underlying conditions and protests per capita in specific states. The displayed correlations are between the individual listed factor and protests per capita.</p>', unsafe_allow_html=True)    
    acled, cols = se.prep(acled)
    #cols = st.multiselect('Select feature variables:', cols)

    df = pd.DataFrame()
    social_cols = ['Unemployment Rate', 'Unemployment Rate Rank', 'Homicide Rates Per 100k', 'Percentage of Bachelors DegreeHolders 2018', 'Nr of Law Enforcement Agencies', 'Total Law Enforcement Employees Per 1000', '% of Population with Health Insurance covered by Employer', '% of Population with Health Insurance covered by Medicaid', 'Percentage of Uninsured', 'Life Expectancy At Birth']
    demographic_cols = ['Population Density', 'Percentage of White Population', 'Percentage of Black Population', 'Percentage of Native Population', 'Percentage of Asian Population', 'Percentage of Islander Population', 
    'Percentage of Other Race Population', 'Percentage of Mixed Race Population', 'Median Age', 'Percentage of Population Age 0-18', 'Percentage of Population Age 19-25', 'Percentage of Population Age 26-34', 
    'Percentage of Population Age 35-54', 'Percentage of Population Age 55-64', 'Percentage of Population Age 65+']
    economic_cols = ['giniCoefficient', 'Average Household Income', 'Income Tax Percentage', 'Ranking of Living Costs', 'Ranking of Grocery Costs', 
    'Ranking of Housing Costs', 'Ranking of Utilities Costs', 'Ranking of Transportation Costs', 'Ranking of Miscellaneous Costs', 'Health Spending per Capita']
    political_cols = ['Percentage of Votes for Trump', 'Percentage of Votes for Biden', 'Voter Turnout 2020', 'Trump Approval Rate', 'Trump Disapproval Rate', 
    'Trump Approval Rate netChange']
    drop1, drop2 = st.beta_columns(2)
    drop3, drop4 = st.beta_columns(2)
    
    social = drop1.multiselect('Social:', social_cols)
    economic = drop2.multiselect('Economic:', economic_cols)
    demographic = drop3.multiselect('Demographic:', demographic_cols)
    political = drop4.multiselect('Political:', political_cols)

    cols2 = []
    cols2.extend(social)
    cols2.extend(economic)
    cols2.extend(demographic)
    cols2.extend(political)

    #cols2 = [rename_cols[col] for col in cols2]
    corrs = se.calc_corr(acled, cols2)

    st.write(corrs)

    st.markdown('<p class="info">Pick two variables to plot against each other to visualize the correlation.</p>', unsafe_allow_html=True)
    #plots to visualise selected correlations? 
    #or to compare two states?
    varcol1, varcol2 = st.beta_columns(2)
    var1 = varcol1.selectbox("Choose first variable: ", cols)
    var2 = varcol2.selectbox("Choose second variable: ", cols)

    pl = go.Figure(layout = {'template': 'plotly_white'})

    pl.add_trace(go.Scatter(x=acled[var1], y=acled[var2], text=acled["State"] ,mode='markers', name="Datapoint"))

    pl.update_layout(title = "Scatterplot of {} vs. {}".format(var1, var2),
                       xaxis_title = var1,
                       yaxis_title = var2, 
                       legend_title = "Legend")

    st.write(pl)
    
    info = pd.DataFrame()

    st.markdown('<p class="info">Display a variable on a choropleth map to visualize how factors are distributed across the country.</p>', unsafe_allow_html=True)
    displayvar = st.selectbox("Display variable: ", cols)
    info[displayvar] = acled[displayvar]
    info["state"] = acled['State']
    info["locations"] = info['state'].apply(lambda x: abbreviations[x])  

    fig2 = px.choropleth(info,  # Input Pandas DataFrame
                          locations="locations",  # DataFrame column with locations
                          color=displayvar,  # DataFrame column with color values
                          hover_name="state", # DataFrame column hover info
                          color_continuous_scale = "Reds", 
                          locationmode = 'USA-states', # Set to plot as US States
                          )
    fig2.update_layout(
          title_text = "{} for 2020".format(displayvar), # Create a Title
          geo_scope='usa',  # Plot only the USA instead of globe
          hoverlabel=dict(
            bgcolor="white",
            font_size=16,
            font_family="consolas"
            )
      )


    st.write(fig2)

#google trends page

if view == 'Google Trends factor estimation':
    #page title
    st.markdown('<p class="section">Google Trends factor estimation</p>', unsafe_allow_html=True)
    st.markdown('<p class="info">Search and explore different keyword terms to see how they correlate with the number of public unrest events.</p>', unsafe_allow_html=True)    

    #building page layout
    verytop = st.beta_container()
    topcontainer = st.beta_container()
    col1, col2 = topcontainer.beta_columns([1, 1])
    lefttop, righttop = topcontainer.beta_columns([1, 1])
    exp = col2.beta_expander("Filter protest type")
    only_violent = exp.checkbox('Only Violent Protests')  
    mapbox = topcontainer.beta_container()
    col4, col5 = topcontainer.beta_columns([1, 1])
    st.markdown('<p class="info">Below you can view the regression and correlation for a specific state by selecting it from the dropdown menu.</p>', unsafe_allow_html=True)    
    mapbox.markdown('<p class="info">The map below displays the estimated amounts of protests given the filters specified. The details of the regression can be viewed in the section below.</p>', unsafe_allow_html=True)
    topleft, sidecol = st.beta_columns([1,1])
    keyword = col1.text_input('Define Keyword Term', value = "Protest")
    progress_bar = mapbox.progress(0)
    status_text = mapbox.empty()
    plots = st.beta_container()
    midleft, midright = st.beta_columns(2)
    fexpander = col2.beta_expander("Regression Options")
    transform = fexpander.radio('Transform protest data:', ['None', 'Log2'], key="radio")
    degrees = fexpander.radio('Polynomial regression degree:', [1, 2, 3], key="radio1")
    leftplot, rightplot = st.beta_columns(2)
    macro = verytop.multiselect("Choose region: ", ["North East", "South", "Mid West", "West"], default = ["North East", "South", "Mid West", "West"])
    colexp = col2.beta_expander("View options")
    button = colexp.radio("Choose view", ['Protests per 100k inhabitants', 'Number of protests', 'Law Enforcement Employees per protest','Law Enforcement Employees per 100k inhabitants'])

    #violent checkbox if statement
    if only_violent:
      protests = violent

    #fix calendar and get trends data
    start_date, end_date = init_calendar(protests)     

    trends1 = pd.read_csv('google_trends_2021-01-18US.csv')
    #build week slider and write it to dashboard
    weeks = c.get_week_dates(start_date, end_date)
    weeks = [datetime.datetime.strptime(date, "%Y-%m-%d").date() for date in weeks]
    date = mapbox.slider("Select week: ", weeks[0], weeks[-1], step = datetime.timedelta(7))
    
    #date_start, date_end = st.slider("Select Week: ", weeks, value=(weeks[0], weeks[1]))    
    data = c.prepare(trends1, protests, start_date, end_date)

    #change date format from string to (pd) datetime
    data['date'] = data.index
    data['date'] = pd.to_datetime(data['date'])    
    #date_start = pd.to_datetime(date_start)
    #date_end = pd.to_datetime(date_end)

    #get historical keywords
    keyword_list = pd.read_csv('keywords.csv')

    #if statement for regression options
    if transform == 'Log2':
        data['log2_protests'] = data['protests'].apply(lambda x: 0 if x in (0, 1) else np.log2(x)) 
        regressions = c.regression(data, 'corrected', 'log2_protests', degrees=degrees)
        plotcol = 'log2_protests'
    else: 
        regressions = c.regression(data, 'corrected', 'protests', degrees=degrees)
        plotcol = 'protests'

    #macro areas (hardcoded)
    northeast = ["ME", "NH", "CT", "RI", "VT", "NY", "MA", "NJ", "PA"]
    midwest = ["IL", "IN", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"]
    south = ["DE", "FL", "GA", "MD", "NC", "SC", "VA", "WV", "AL", "KY", "MS", "TN", "AR", "LA", "OK", "TX"]
    west = ["AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY", "AK", "CA", "HI", "OR", "WA"]

    #if statements for macro area selector
    selected_states = []
    if "North East" in macro:
      selected_states.extend(northeast)
    if "South" in macro:
      selected_states.extend(south)
    if "Mid West" in macro:
      selected_states.extend(midwest)
    if "West" in macro:
      selected_states.extend(west)

    #calulate correlations to google trends
    correlations = c.correlate_trend(data)

    #"run" button functionality
    if col1.button("Run Analysis"):
        trends1, keyword = fetch_trends(start_date, keyword, "US")
        data = c.prepare(trends1, protests, start_date, end_date)
        data['locations'] = data['state'].apply(lambda x: abbreviations[x])
        data = data[data.locations.isin(selected_states)]   
        data['date'] = data.index
        data['date'] = pd.to_datetime(data['date'])      
        correlations = c.correlate_trend(data)
        keyword_list = keyword_list.append({'keyword':keyword, 'correlation':correlations.mean()[0]}, ignore_index=True)
        keyword_list.to_csv('keywords.csv', index=False)

    #reducing the choropleth map dataframe to exclusively selected states
    data['locations'] = data['state'].apply(lambda x: abbreviations[x])
    data = data[data.locations.isin(selected_states)]

    #selecting the trend_data based on specified period and making predictions
    trends1['date'] = pd.to_datetime(trends1['date'], format="%Y-%m-%d")
    date = pd.to_datetime(date)
    trend_data = trends1[trends1['date'] == date]
    predictions = c.predict(regressions, trend_data)

    #building the choropleth map dataframe
    df = pd.DataFrame()
    df['state'] = predictions.index
    df['locations'] = df['state'].apply(lambda x: abbreviations[x])
    x = list(predictions['protests'])
    df['protests'] = x
    df = df[df['locations'].isin(selected_states)]

    #if statement for choose view radio selector
    legend_text = button
    title_text = 'Estimated number of protests per state for week of {}'.format(date.date())
    if button == 'Protests per 100k inhabitants':
      df['protests'] = df['protests'] / pops['Pop2020'] * 100000
      title_text = 'Estimated protests for week of {}, per 100k inhabitants'.format(date.date())
      legend_text = 'Protests'
    elif button == 'Law Enforcement Employees per protest':
      legend_text = 'Law Enforcement'
      title_text = 'Law enforcement employees per estimated protest for week of {}'.format(date.date())
      df['protests'] = df['protests'] / pops['Pop2020'] * 1000
      df['protests'] = cops['TotalLawEnforcementEmployees_per1000'] / df['protests']
    elif button ==  'Law Enforcement Employees per 100k inhabitants':
      legend_text = 'Law Enforcement'
      title_text = 'Law enforcement employees per 100k inhabitants for week of {}'.format(date.date())
      df['protests'] = cops['TotalLawEnforcementEmployees_per1000'] * 100
    
    #build and plot choropleth map
    fig = px.choropleth(df,  # Input Pandas DataFrame
                          locations="locations",  # DataFrame column with locations
                          color="protests",  # DataFrame column with color values
                          hover_name="state", # DataFrame column hover info
                          color_continuous_scale = "Reds", 
                          locationmode = 'USA-states', # Set to plot as US States
                          hover_data = {'state':False,
                                        'protests':True,
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
            ),
          autosize = True
      )

    mapbox.write(fig)    

    #write previous search results
    with col4:
        st.write('Previous Search Results:')
        st.write(keyword_list.tail(5))

    #write correlation to dashboard
    col5.write("##")
    exp2 = col5.beta_expander("Average correlation ({}): {}".format(keyword, round(correlations['correlation'].mean(), 4)))
    exp2.write("Average correlation between number of protests and search activity for term '({})' for all selected states: {}".format(keyword, round(correlations['correlation'].mean(), 4)))
    #making the selected state dataframe
    selected_full = [fullnames[state] for state in selected_states]
    state = plots.selectbox("Select State: ", selected_full, key='dlafsdlj')
    state_data = data[data['state'] == state]
    state_pop = pops['Pop2020'][pops['state'] == state].values[0]
    state_data['protests_per_capita'] = state_data['protests'] / state_pop * 100000

    #build and plot trendplot
    with plots:
        trendplot = go.Figure(layout = {'template': 'plotly_white'})
        trendplot.add_trace(go.Scatter(x=state_data.index, y=state_data['corrected'], mode='lines', name='Google Trend'))
        trendplot.add_trace(go.Scatter(x=state_data.index, y=state_data['protests_per_capita'], mode='lines', name='Protests'))
        trendplot.update_layout(title = "Google trends data ('{}') and protests against time".format(keyword),
                                yaxis_title = "Keyword ({})/protest frequency".format(keyword),
                                legend_title = "Legend")

        st.write(trendplot)

    #build regression line
    top = state_data['corrected'].max()
    model = regressions[state][1]
    line = np.linspace(0, top, 100)
    state_pred = predictions[predictions.index == state]

    #get selected datapoint (for selected week)
    point = state_data[state_data.date == date]

    #build and plot scatterplot with regression line
    with plots:
        pl = go.Figure(layout = {'template': 'plotly_white'})
        pl.add_trace(go.Scatter(x=state_data['corrected'], y=state_data[plotcol], mode='markers', name="Datapoint"))
        pl.add_trace(go.Scatter(x=line, y=model(line), mode='lines', name="Regression"))
        pl.add_trace(go.Scatter(x=point['corrected'], y=model(point['corrected']), mode='markers', name=datetime.datetime.strftime(date, "%Y-%m-%d")))
        pl.update_layout(title = "Visualized regression of Google trends data vs. protest frequency",
                         xaxis_title = "Relative keyword frequency",
                         yaxis_title = "Protest count ({})".format(transform),
                         legend_title = "Legend")

        st.write(pl)

    #belarus = belarus[belarus['date'] <= ]

if view == 'Combined factors estimation':
    st.markdown('<p class="section">Combined factors estimation</p>', unsafe_allow_html=True)
    st.markdown('<p class="info">Explore feature variables and highly correlated google trends to estimate the number of protests in a state. </p>', unsafe_allow_html=True)
    start_date, end_date = init_calendar(protests)
    topleft, topright = st.beta_columns(2)
    keyword = topleft.text_input("Define keyword: ", value = "Protest")
    boxy = st.beta_container()
    progress_bar = st.progress(0)
    status_text = st.empty()
    acled, cols = se.prep(acled)
    trends2, keyword = fetch_trends(start_date, keyword, "US")
    only_violent = boxy.checkbox('Only Violent Protests') 
    if only_violent:
        protests = violent
    data = c.prepare(trends2, protests, start_date, end_date)

    data = data.rename(columns={'state':'State'})
    data['date'] = data.index

    @st.cache
    def merge(data):
      data = data.merge(acled, how='left', on='State')
      data['protests_per_capita'] = data['protests'] / data['Pop2020'] * 100000
      return data

    data = merge(data)

    social_cols = ['Unemployment Rate', 'Unemployment Rate Rank', 'Homicide Rates Per 100k', 'Percentage of Bachelors DegreeHolders 2018', 'Nr of Law Enforcement Agencies', 'Total Law Enforcement Employees Per 1000', '% of Population with Health Insurance covered by Employer', '% of Population with Health Insurance covered by Medicaid', 'Percentage of Uninsured', 'Life Expectancy At Birth']
    demographic_cols = ['Population Density', 'Percentage of White Population', 'Percentage of Black Population', 'Percentage of Native Population', 'Percentage of Asian Population', 'Percentage of Islander Population', 
    'Percentage of Other Race Population', 'Percentage of Mixed Race Population', 'Median Age', 'Percentage of Population Age 0-18', 'Percentage of Population Age 19-25', 'Percentage of Population Age 26-34', 
    'Percentage of Population Age 35-54', 'Percentage of Population Age 55-64', 'Percentage of Population Age 65+']
    economic_cols = ['giniCoefficient', 'Average Household Income', 'Income Tax Percentage', 'Ranking of Living Costs', 'Ranking of Grocery Costs', 
    'Ranking of Housing Costs', 'Ranking of Utilities Costs', 'Ranking of Transportation Costs', 'Ranking of Miscellaneous Costs', 'Health Spending per Capita']
    political_cols = ['Percentage of Votes for Trump', 'Percentage of Votes for Biden', 'Voter Turnout 2020', 'Trump Approval Rate', 'Trump Disapproval Rate', 
    'Trump Approval Rate netChange']

    exp = boxy.beta_expander("Select factors")

    drop1, drop2 = exp.beta_columns(2)
    drop3, drop4 = exp.beta_columns(2)
    
    social = drop1.multiselect('Social:', social_cols)
    economic = drop2.multiselect('Economic:', economic_cols)
    demographic = drop3.multiselect('Demographic:', demographic_cols)
    political = drop4.multiselect('Political:', political_cols)

    cols2 = []
    cols2.extend(social)
    cols2.extend(economic)
    cols2.extend(demographic)
    cols2.extend(political)

    cols2.append('corrected')

    exp2 = boxy.beta_expander("Change model output")
    button = exp2.radio('Show model output as:', ['Protests per 100k inhabitants', 'Number of protests'])
    
    if button == 'Protests per 100k inhabitants':
      y = 'protests_per_capita'
    else:
      y = 'protests'
    X = cols2

    select = [col for col in cols2 if col != 'corrected']
    select.append("State")
    export_data = acled[select]

    exportbox1, exportbox2 = exp.beta_columns(2)
    exportbox2.write("##")
    export = exportbox2.button("Export factors to csv")
    filename = exportbox1.text_input("Enter filename: ")
    if export:
      export_data.to_csv(filename)

    X_data = np.array(data[X])
    y_data = np.array(data[y])

    X_train, X_test, y_train, y_test = train_test_split(X_data, y_data, test_size=0.2, random_state=0)
    data = data.rename(columns={'State':'state'})
    correlations = c.correlate_trend(data)

    exp3 = st.beta_expander("Average keyword correlation ({}): {}".format(keyword, round(correlations['correlation'].mean(), 4)))
    exp3.write("Average keyword correlation between number of protests and search activity for term '({})' for all selected states: {}".format(keyword, round(correlations['correlation'].mean(), 4)))


    regressor = topright.selectbox("Choose regression: ", ["Linear", "Random Forest"])
    if regressor == "Linear":
      regression = linear_model.LinearRegression()
    elif regressor == "Random Forest":
      regression = RandomForestRegressor()

    regression.fit(X_train, y_train)
    exp.write(cols2)  
    predictions = regression.predict(X_test)
    r2 = r2_score(y_test, predictions)
    st.write("#")
    st.markdown('<p class="text">Combined model R-squared: {}</p>'.format(round(r2, 4)), unsafe_allow_html=True)


    weeks = c.get_week_dates(start_date, end_date)

    weeks = [datetime.datetime.strptime(date, "%Y-%m-%d").date() for date in weeks]
    st.markdown('<p class="info">Visualize estimations for protests in a week in the choropleth map below. Values displayed are outputs of the regression constructed above.</p>'.format(round(r2, 4)), unsafe_allow_html=True)    
    date_start, date_end = st.select_slider("Select Week: ", weeks, value=(weeks[0], weeks[1]))
    data['date'] = pd.to_datetime(data['date'])

    date_start = pd.to_datetime(date_start)
    date_end = pd.to_datetime(date_end)

    date_data = data[data.date >= date_start]
    date_data = date_data[date_data.date <= date_end]

    x_test = date_data[X]

    northeast = ["ME", "NH", "CT", "RI", "VT", "NY", "MA", "NJ", "PA"]
    midwest = ["IL", "IN", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"]
    south = ["DE", "FL", "GA", "MD", "NC", "SC", "VA", "WV", "AL", "KY", "MS", "TN", "AR", "LA", "OK", "TX"]
    west = ["AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY", "AK", "CA", "HI", "OR", "WA"]

    macro = st.multiselect("Choose macro area: ", ["North East", "South", "Mid West", "West"], default = ["North East", "South", "Mid West", "West"])

    selected_states = []
    if "North East" in macro:
      selected_states.extend(northeast)
    if "South" in macro:
      selected_states.extend(south)
    if "Mid West" in macro:
      selected_states.extend(midwest)
    if "West" in macro:
      selected_states.extend(west)

    #df = df[df.locations.isin(selected_states)]
    #data['locations'] = data['state'].apply(lambda x: abbreviations[x])
    #data = data[data.locations.isin(selected_states)]

    df = pd.DataFrame()
    df[button] = regression.predict(x_test)
    statelist = list(date_data['state'])
    df['state'] = statelist
    df['locations'] = df['state'].apply(lambda x: abbreviations[x])
    df = df[df['locations'].isin(selected_states)]

    title_text = 'Estimated number of protests for week {} to week {}'.format(date_start.date(), date_end.date())

    fig = px.choropleth(df,  # Input Pandas DataFrame
                          locations="locations",  # DataFrame column with locations
                          color=button,  # DataFrame column with color values
                          hover_name="state", # DataFrame column hover info
                          color_continuous_scale = "Reds", 
                          locationmode = 'USA-states', # Set to plot as US States
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

    st.write(fig)