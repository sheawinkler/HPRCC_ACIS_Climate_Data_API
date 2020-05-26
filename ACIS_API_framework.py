'''
--Author: Shea Winkler
--Date: 05/25/2020
--Purpose: Framework to access ACIS climate data API

current Python: 3.7.4 (should be compatible with anything 3.7+ or earlier)
--current packages:
----requests version: 2.22.0
----pandas version: 0.25.1
----numpy version: 1.17.2
'''
import io
import re
import requests
import pandas as pd
import numpy as np

### print out your package versions to see if you need to update ###
# import sys
# print(sys.version)
# print('python executable: {}'.format(sys.executable))
# print('requests version: {}'.format(requests.__version__))
# print('pandas version: {}'.format(pd.__version__))
# print('numpy version: {}'.format(np.__version__))


## stn = station_number
## sdate = start date
## edate = end date
stn = '254795'
sdate = '2018-01-01'
edate = '2018-12-31'

# for further explanation: http://www.rcc-acis.org/docs_webservices.html
api_params = {'sID': stn,
              'sdate':sdate,
              'edate':edate,
              'meta':'valid_daterange,ll',
              # 1 = maxT, 2 = minT, 4 = precip, 10 = snowfall, 11 = snow_depth,
              'elems':'1,2,4,10,11',#format may change if api calls become more complex
              }
base_url = 'http://data.rcc-acis.org/'
method = 'StnData'

# get the api data w/ StnData method from documentation
req = requests.get(base_url+method,api_params)

# read the data returned from API into pandas dataframe
df = pd.read_csv(io.StringIO(req.text))

## retrieve lattitude and longitude
latitude = re.sub('[^\d]','',df.columns[1])
longitude = re.sub('[^-\d]','',df.columns[0])

# get rid of T/F columns for whether data exists - could use these as QC in the future
# TODO: process any missing data here
df = df.drop(axis=1, columns=df.columns[[6,7,8,9,10,11,12]])

# reset column names
df.columns = ['Date','MaxTemp','MinTemp','Precip','Snowfall','Snow_Depth']

# Replace letters in precip column according to HPRCC script (w/o tracking 'M')
precip = []
for i in range(len(df['Precip'])):
    if df.iloc[i,3] == 'T' or df.iloc[i,3] == 'S':
        precip.append(0.0)
    elif df.iloc[i,3] == 'A': #not sure about this one but it copies HPRCC method
        precip.append(float(df.iloc[i,:-1]))
    else:
        precip.append(df.iloc[i,3])
df['Precip'] = precip

# Replace T with 0.0 in Snowfall
df['Snowfall'] = [0.0 if 'T' else i for i in df['Snowfall']]

# remove non-numerical chars from snow_depth
# Snow_depth may not be necessary
df['Snow_Depth'] = [re.sub('[^\d]','',i) for i in df['Snow_Depth']]

# reformat date to match expected input for BuildWEA: yyyy-mm-dd
df.Date = pd.date_range(sdate,edate).tolist()

# print weather station data to csv for BuildWEA
df.to_csv('acis_test.csv',index=False)
