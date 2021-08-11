import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score
from sklearn import linear_model
from sklearn.ensemble import RandomForestRegressor
from tqdm.notebook import tqdm
import scipy.stats

rename_cols = {
'giniCoefficient': 'Gini Coefficient',
'PopDensity':'Population Density',
'WhitePerc':'Percentage of White Population',
'BlackPerc':'Percentage of Black Population',
'NativePerc': 'Percentage of Native Population', 
'AsianPerc': 'Percentage of Asian Population',
'IslanderPerc': 'Percentage of Islander Population',
'OtherRacePerc': 'Percentage of Other Race Population',
'TwoOrMoreRacesPerc': 'Percentage of Mixed Race Population',
'MedianAge': 'Median Age',
'AvgHouseholdIncome': 'Average Household Income',
'incomeTax': 'Income Tax Percentage',
'costRank': 'Ranking of Living Costs',
'groceryCost': 'Ranking of Grocery Costs',
'housingCost': 'Ranking of Housing Costs',
'utilitiesCost': 'Ranking of Utilities Costs',
'transportationCost': 'Ranking of Transportation Costs',
'miscCost': 'Ranking of Miscellaneous Costs',
'UnemploymentRate': 'Unemployment Rate', 
'UnemploymentRank': 'Unemployment Rate Rank', 
'votesTrump_percent2020': 'Percentage of Votes for Trump',
'votesBiden_percent':'Percentage of Votes for Biden',
'VEP Turnout Rate (Total Ballots Counted)': 'Voter Turnout 2020', 
'HomicideRate2017(per100k)': 'Homicide Rates Per 100k', 
'TotalHomicides2017': 'Total Homicides 2017',
'TrumpApproval_perc': 'Trump Approval Rate', 
'TrumpDisapproval_perc':'Trump Disapproval Rate',
'TrumpnetChangeSinceOffice_perc': 'Trump Approval Rate netChange',
'BachelorsDegreeHolders2018_perc': 'Percentage of Bachelors DegreeHolders 2018',
'Age0-18_perc': 'Percentage of Population Age 0-18',
'Age19-25_perc': 'Percentage of Population Age 19-25',
'Age26-34_perc': 'Percentage of Population Age 26-34',
'Age35-54_perc': 'Percentage of Population Age 35-54',
'Age55-64_perc': 'Percentage of Population Age 55-64',
'Age65+_perc': 'Percentage of Population Age 65+',
'NrLawEnforcementAgencies': 'Nr of Law Enforcement Agencies',
'TotalLawEnforcementEmployees_per1000': 'Total Law Enforcement Employees Per 1000',
'HealthInsuranceCoverageByEmployer': '% of Population with Health Insurance covered by Employer',
'HealthInsuranceCoverageByMedicaid': '% of Population with Health Insurance covered by Medicaid',
'Uninsured': 'Percentage of Uninsured', 
'LifeExpectancyAtBirth_years': 'Life Expectancy At Birth',
'HealthSpendingperCapita': 'Health Spending per Capita'}

def prep(data):
  states = data
  states['protests_per_capita'] = states['ACLEDProtestCount'] / states['Pop2020'] * 100000
  states = states.drop(columns='ACLEDViolentProtestCount')

  states = states.drop(columns=['PopGrowthfrom2018', 'RealGDP2019'])
  states = states.rename(columns = rename_cols)
  cols = list(states.columns[2:])
  return states, cols

def calc_corr(data, cols):
    d = {}
    for factor in cols:
        y = data['protests_per_capita']
        X = data[factor]
        score, p = scipy.stats.pearsonr(X, y)
        d[factor] = score, p
    
    df = pd.DataFrame.from_dict(d, orient = 'index')
    df = df.rename(columns={0: 'Correlation', 1: 'P-value'})

    return df
        
#correlations = calc_corr(states)
#cols = correlations.sort_values(by=0).index


#y = states['protests_per_capita']
#X = states[['AverageTemperature', 'VEP Turnout Rate (Total Ballots Counted)', 'votesBiden_percent', 'BlackPerc', 'WhitePerc', 'groceryCost', 'TrumpnetChangeSinceOffice_perc', 'OtherRacePerc', 'TrumpApproval_perc']]
#regression = RandomForestRegressor(max_depth=5, random_state=0)
#regression.fit(X, y)
#r2_score(y, regression.predict(X))

def construct_model(data):
    r2 = 0
    factors = []
    regression = RandomForestRegressor(max_depth = 5, random_state = 0)
    #regression = linear_model.LinearRegression()
    for i, factor in tqdm(enumerate(cols)):
        best = None
        tempr2 = 0
        for factor in cols:
            test = factors.copy()
            test.append(factor)
            y = data['protests_per_capita']
            X = data[test]
            regression.fit(X, y)
            score = r2_score(y, regression.predict(X))
            if score > tempr2:
                tempr2 = score
                #factors.append(factor)
                best = factor
                factors.append(best)
                r2 = score
    
    return r2, factors


