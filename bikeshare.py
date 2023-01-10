# LIBRARIES
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dtm
import calendar as cal

def list_select(qstn, lst):
    # Asks the user to select an option from a given list of valid value
    # Args:
    #     (qstn) - A text string representing the question the user will see
    #     (lst) - A list of strings representing the options available to the user
    # Returns:
    #     A string selected from those provided in (lst)
    valid_optns = {**{str(enum): val for enum, val in enumerate(lst,1)},
                   **{val.lower(): val for val in lst}}

    optn_txt = '\n'.join([f'{key}: {val}' for key, val in enumerate(lst,1)])
    qstn_txt = qstn + '\n' + optn_txt + '\n>'

    ask = str()
    while ask.lower() not in valid_optns.keys():
        ask = input(qstn_txt)
        if ask.lower() not in valid_optns.keys():
            print('"' + ask + '" is not a valid input.')
        else:
            print('Selected: ' + valid_optns.get(ask))
            return valid_optns.get(ask)

def time_string(sec):
    # Returns a detailed, human readable time string based on a numeric value representing number of seconds
    # Args:
    #   (sec) - a numeric value representing a number of seconds
    factrs = {'years': 365*24*60*60, 'days': 24*60*60,'hrs': 60*60, 'mins': 60}
    x = round(sec,0)
    strt = False
    out = {}
    for i in factrs:
        y, x = divmod(x, factrs.get(i))
        if (y == 0 and strt == True) or y!=0:
            out[i] = int(y)
            strt = True
    out['secs'] = int(x)
    str = ', '.join('{} {}'.format(val, key) for key, val in out.items())
    return str

def series_mode_summary(series, txt):
    # Prints text summarising the mode of the values from a provided series accompanied with descriptive text
    # Args:
    #   (series) - A pandas series
    #   (txt) - Descriptive text of the mode being printed
    conv = lambda x: int(round(x,0)) if type(x) == float else x
    modes = [str(conv(i)) for i in series.mode(dropna=True)]
    mode_str = ' (AND) '.join(modes)
    multi = '' if len(modes) == 1 else '*'+str(len(modes))
    mode_vals = series.value_counts().sort_values(ascending=False)
    print('{}{}, n={:,}{}'.format(txt, mode_str,mode_vals.iloc[0],multi))


# MAIN INPUT
redo = 'Yes'
while redo == 'Yes':
    # USER INPUT: Ask user to select city dataset to analyse
    city = list_select('\nWhich dataset would you like to select?',
                       ['washington','chicago','new_york_city'])

    # USER INPUT: Ask user if they want to filter data by month
    if list_select('\nWould you like to filter by month?', ['Yes','No']) == 'Yes':
        month = list_select('\nWhich month?',
                            [cal.month_name[i] for i in np.arange(1,7)])
    else:
        month = False

    # USER INPUT: Ask user if they want to filter data by type of day
    if list_select('\nWould you like to filter the data by type of day?', ['Yes','No'])=='Yes':
        daytype = list_select('\nWhich day type?', ['weekend','weekday'])
    else:
        daytype = False

    # Check with user if they are happy with their selection
    print(
         '\nYou selected:\n    Dataset: ' + city +
         '\n    Month filter: ' + str(month) +
         '\n    Day type filter: ' + str(daytype)
          )
    redo = list_select("Would you like to re-do your selection?", ['Yes','No'])



# MANIPULATE DATA
print("\nReading csv into dataframe...")
global df
df = pd.read_csv('{}.csv'.format(city))

# REDUNDANT
print("Creating new column 'ROUTE'...")
x = df[['Start Station','End Station']].to_numpy()
x.sort(axis=1)
df['ROUTE'] = ["<==>".join(i) for i in x.tolist()]

# REDUNDANT
print("Creating new column 'DIRECTION'...")
dir_cats =  {
    'LOOP': (df['Start Station'] == df['End Station']),
    'TO<==>FROM': (df['Start Station'] > df['End Station']),
    'FROM<==>TO': (df['Start Station'] < df['End Station'])
    }
df['DIRECTION'] = np.select(dir_cats.values(), dir_cats.keys())

# Create Start Month Column. Filter if necessary
print("Creating new column 'Start Month'...")
df['Start Month'] = pd.to_datetime(df['Start Time']).dt.month_name()
df['Start Month'] = pd.Categorical(df['Start Month'],
                                   categories = list(cal.month_name[1:]),
                                   ordered = True)
if month:
    print("Filtering by 'Start Month' == '" + month + "'...")
    df = df[(df['Start Month']==month)]

# Create Start Day columns
print("Creating new column 'Start Day Number'...")
df['Start Day Number'] = pd.to_datetime(df['Start Time']).dt.dayofweek
print("Creating new column 'Start Day'...")
df['Start Day'] = pd.to_datetime(df['Start Time']).dt.day_name()
df['Start Day'] = pd.Categorical(df['Start Day'],
                                 categories = list(cal.day_name),
                                 ordered = True)

# Create Start Hour columns
print("Creating new column 'Start Hour'...")
df['Start Hour'] = pd.to_datetime(df['Start Time']).dt.strftime('%H')
df['Start Hour (12H)'] = pd.to_datetime(df['Start Time']).dt.strftime('%I%p')

# Fillna the 'Gender' column if present
if 'Gender' in df.columns:
    df['Gender'].fillna('Unknown', inplace=True)

print("Creating new column 'Trip Duration (minutes)'...")
df['Trip Dur(mins)'] = df['Trip Duration']/60

# Create 'Start Day Type' column, filter if necessary
print("Creating new column 'Start Day Type'...")
day_cats = {
    'weekend': (df['Start Day Number'] > 4),
    'weekday': (df['Start Day Number'] <= 4)
    }
df['Start Day Type'] = np.select(day_cats.values(), day_cats.keys())
if daytype:
    print("Filtering by 'Start Day Type' == '" + daytype + "'...")
    df = df[(df['Start Day Type']==daytype)]

# Create generation column
if 'Birth Year' in df.columns:
    print("Creating new column 'Generation'...")
    gnrtn_cats = {
        "Unknown": (np.isnan(df['Birth Year'])),
        "Pre-boomer(-'45)": (df['Birth Year'] < 1946),
        "Boomer('46-'64)": (df['Birth Year'].between(1946 ,1965, 'left')),
        "Gen-X('65-'80)": (df['Birth Year'].between(1965, 1981, 'left')),
        "Gen-Y('80-'96)": (df['Birth Year'].between(1981, 1997, 'left')),
        "Gen-Z('97-)": (df['Birth Year'] >= 1997)
        }
    df['Generation'] = np.select(gnrtn_cats.values(), gnrtn_cats.keys())
    df['Generation'] = pd.Categorical(df['Generation'],
                                      categories = gnrtn_cats.keys(),
                                      ordered = True)

# Create 'Duration Catoegory' column
print("Creating new column 'Duration Category'...")
dur_cats = {
    '00<=mins<05': (df['Trip Dur(mins)'] < 5),
    '05<=mins<10': (df['Trip Dur(mins)'].between(5, 10, 'left')),
    '10=<mins<15': (df['Trip Dur(mins)'].between(10, 15, 'left')),
    '15=<mins<20': (df['Trip Dur(mins)'].between(15, 20, 'left')),
    '20=<mins<25': (df['Trip Dur(mins)'].between(20, 25, 'left')),
    '25=<mins<30': (df['Trip Dur(mins)'].between(25, 30, 'left')),
    '30=<mins<..': (df['Trip Dur(mins)'] >= 30)
    }
df['Duration Category'] = np.select(dur_cats.values(), dur_cats.keys())

# Print raw data
if list_select('\nWould you like to see 5 lines of the dataset you selected?', ['Yes','No']) == 'Yes':
    again = 'Yes'
    x = 0
    while again == 'Yes':
        print(df.iloc[x:x+5])
        again = list_select('\nPrint another 5 lines?', ['Yes','No'])
        x += 5


# CREATE MAIN STATS
print('\nTOPIC 1: POPULAR TIMES OF TRAVEL\n')

# -most common month
if month == False:
    series_mode_summary(df['Start Month'],'Most popular month:\n    ')

# -most common day of week
day_counts = df['Start Day'].value_counts().sort_values(ascending = False)
if daytype == False:
    txt = ''
elif daytype == 'weekend':
    txt = 'weekend '
elif daytype == 'weekday':
    txt = 'week'
series_mode_summary(df['Start Day'],
                    'Most popular {}day:\n    '.format(txt))

# -most common hour of day
series_mode_summary(df['Start Hour (12H)'],
                    'Most popular starting hour:\n    ')

# 2 Popular stations and trip
print('\nTOPIC 2: POPULAR STATIONS AND ROUTES\n')
# -most common start station
series_mode_summary(df['Start Station'],
                    'Most popular starting station:\n    ')
# -most common end station
series_mode_summary(df['End Station'],
                    'Most popular ending station:\n    ')
# -most common trip from start to end
route_counts = df[['Start Station','End Station']].value_counts()
max = route_counts.max()
modes = route_counts[route_counts == max]
print('Most popular route:')
routes =list()
for i, j in modes.index:
    routes.append('    {} <TO> {}, n={:,}'.format(i,j,max))
print('\n    &\n'.join(routes))

# 3 Trip Duration
print('\nTOPIC 3: TRIP DURATIONS\n')
# -total travel time
tot_time = time_string(df['Trip Duration'].sum())
print('Total user time spent in transit:\n    ' + tot_time)
# -average travel time
ave_time = time_string(df['Trip Duration'].mean())
print('Average trip duration:\n    ' + ave_time)

# 4 User info
print('\nTOPIC 4: USER INFO')
# -counts of each user type
print('\nTrip counts by user type:')
n_utype = df['User Type'].value_counts().sort_values(ascending = False)
for i in n_utype.index:
    print('    {}: {:,}'.format(i.upper(), n_utype.loc[i]))


# user stats for Chicago and New York datasets
if city in ['chicago', 'new_york']:
    # -count of each gender (dataset specific)
    print('\nTrip counts by user gender:')
    n_gender = df['Gender'].value_counts()
    for i in n_gender.index:
        print('    {}: {:,}'.format(i.upper(), n_gender.loc[i]))

    # -earliest, most recent, most common year of birth
    print('\nYear of birth stats:')
    print('    EARLIEST: {:.0f}'.format(df['Birth Year'].dropna().min()))
    print('    LATEST: {:.0f}'.format(df['Birth Year'].dropna().max()))
    series_mode_summary(df['Birth Year'], '    MOST COMMON: ')


# BAR CHART
if list_select('\nWould you like to create a bar chart of the trip data?', ['Yes','No']) == 'Yes':
    again = None
    while again != 'No':

        category_list = ['Gender', 'User Type', 'Generation', 'Duration Category',
                         'Start Hour','Start Month','Start Day Type', 'Start Day']
        category_list = [i for i in category_list if i in df.columns]

        # Select x-axis category
        xaxis = list_select('\nSelect a category to represent along the x-axis.',
                            category_list)
        category_list.remove(xaxis)

        # Select bar grouping category
        groups = list_select('\nSelect a category to group the bars by.',
                             category_list)

        # Prepare dataframe for chart
        df2 = df.groupby([groups, xaxis])
        df2 = df2.agg(transit_time=('Trip Duration',np.sum),
                      trips=('Trip Duration', 'size'))
        df2 = df2.reset_index()
        df3 = df2.pivot(index=xaxis, columns=groups, values='trips')
        df3.sort_index(axis=1, inplace=True)

        # create and format plot
        plt.ion()
        ax = df3.plot.bar(stacked=True, backend='matplotlib')
        plt.xticks(rotation=45)
        ax.set_yticks(ax.get_yticks())
        ax.set_yticklabels(['{:,}'.format(int(x)) for x in ax.get_yticks().tolist()])
        plt.title('Number of Trips by {}, grouped by {}'.format(xaxis, groups))
        plt.ylabel('Number of Trips')
        plt.tight_layout()
        again = list_select('\nWould you like to create another bar chart?', ['Yes','No'])
