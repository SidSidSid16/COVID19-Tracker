from flask import Flask, render_template, json, redirect, url_for, abort, Markup, request
import time
import threading
from threading import Thread, Event
import pandas
import csv
import urllib
import calendar
from calendar import monthrange
from datetime import datetime, timedelta
import folium
from folium.features import DivIcon
import numpy
from difflib import get_close_matches
from titlecase import titlecase

app = Flask(__name__)

dataset_path = "https://raw.githubusercontent.com/microsoft/Bing-COVID-19-Data/master/data/Bing-COVID19-Data.csv"

is_initialising = False
df_entireDataset = None
df_entireDatasetSorted = None
arr_allCountries = None
arr_allRegions = None
arr_allRegions2 = None

def initialise():
    global df_entireDataset
    global df_entireDatasetSorted
    global arr_allCountries
    global arr_allRegions
    global arr_allRegions2
    global is_initialising
    is_initialising = True
    dataset_csv = urllib.request.urlopen(dataset_path)
    df_entireDataset = pandas.read_csv(dataset_csv)
    df_entireDataset.fillna(0, inplace=True)
    df_entireDataset['Updated'] = pandas.to_datetime(df_entireDataset.Updated)
    df_entireDataset['Deaths'] = pandas.to_numeric(df_entireDataset.Deaths, downcast='integer')
    df_entireDataset['Recovered'] = pandas.to_numeric(df_entireDataset.Recovered, downcast='integer')
    df_entireDatasetSorted = df_entireDataset.copy()
    df_entireDatasetSorted.sort_values(by=['Updated'], inplace=True, ascending=False)
    arr_allCountries = df_entireDataset["Country_Region"].unique()
    arr_allRegions = df_entireDataset["AdminRegion1"].unique()
    arr_allRegions2  = df_entireDataset["AdminRegion2"].unique()
    getLatestdate()
    getTotalCases()
    getTotalDeaths()
    getTotalRecovered()
    getWorstHitCountry()
    createWorldMap()
    createLatestUpdatesTable()
    createWorldCasesChart()
    allCountriesTableCreate()
    print("Dataset Loaded!")
    is_initialising = False
    threading.Timer(10800, initialise).start()

latestDatasetDate = None
latestDatasetDateText = None
def getLatestdate():
    global latestDatasetDate
    global latestDatasetDateText
    date = df_entireDatasetSorted.iloc[0]['Updated']
    df = df_entireDatasetSorted.query('Updated == @date')
    countries = df["Country_Region"].unique()
    latestDatasetDate = date
    latestDatasetDateText = date.strftime('%d/%m/%Y') + ", the statistics for " + str(countries.size) + " countries were updated."

totalCasesWorldwide = None 
def getTotalCases(country = "Worldwide"):
    global totalCasesWorldwide
    totalCasesWorldwide = df_entireDatasetSorted[df_entireDatasetSorted.Country_Region == country].iloc[0]['Confirmed']
    totalCasesWorldwide = "{:,}".format(totalCasesWorldwide)
    return totalCasesWorldwide

totalDeathsWorldwide = None
def getTotalDeaths(country = "Worldwide"):
    global totalDeathsWorldwide
    totalDeathsWorldwide = df_entireDatasetSorted[df_entireDatasetSorted.Country_Region == country].iloc[0]['Deaths']
    totalDeathsWorldwide = "{:,}".format(totalDeathsWorldwide)
    return totalDeathsWorldwide

totalRecoveredWorldwide = None
def getTotalRecovered(country = "Worldwide"):
    global totalRecoveredWorldwide
    totalRecoveredWorldwide = df_entireDatasetSorted[df_entireDatasetSorted.Country_Region == country].iloc[0]['Recovered']
    totalRecoveredWorldwide = "{:,}".format(totalRecoveredWorldwide)
    return totalRecoveredWorldwide

worstHitCountry = None  
def getWorstHitCountry():
    global worstHitCountry
    df_entireDatasetSortedDeaths = df_entireDataset.copy()
    df_entireDatasetSortedDeaths.sort_values(by=['Deaths'], inplace=True, ascending=False)
    # The following line removes "Worldwide" from the results. "Worldwide" isn't a country/region
    df_entireDatasetSortedDeaths = df_entireDatasetSortedDeaths.query("Country_Region != 'Worldwide'")
    worstHitCountry = df_entireDatasetSortedDeaths.iloc[0]['Country_Region']
    return worstHitCountry

latestUpdatesTable = None
def createLatestUpdatesTable():
    global latestUpdatesTable
    date = df_entireDatasetSorted.iloc[0]['Updated']
    df = df_entireDatasetSorted.query('Updated == @date')
    df.drop(columns=['ID', 'Updated', 'ConfirmedChange', 'DeathsChange', 'RecoveredChange', 'Latitude', 'Longitude', 'ISO2', 'ISO3'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.rename(columns={"Country_Region": "Country", "AdminRegion1": "Outer Region", "AdminRegion2": "Inner Region"}, inplace=True)
    df["Outer Region"].replace({0: "---"}, inplace=True)
    df["Inner Region"].replace({0: "---"}, inplace=True)
    df.index.name = '#'
    df.columns.name = df.index.name
    df.index.name = None
    df = df[['Country', 'Outer Region', 'Inner Region', 'Confirmed', 'Deaths', 'Recovered']]
    df[u'Country'] = df[u'Country'].apply(lambda x: make_hyperlink(x))
    df[u'Outer Region'] = df[u'Outer Region'].apply(lambda x: make_hyperlink(x) if x != "---" else "---")
    df[u'Inner Region'] = df[u'Inner Region'].apply(lambda x: make_hyperlink(x) if x != "---" else "---")
    latestUpdatesTable = [df.to_html(classes=['data', 'table', 'table-striped', 'table-borderless'], header="true", justify='left', render_links=True, escape=False)]
    return latestUpdatesTable

worldMap = None
def createWorldMap():
    global worldMap
    map = folium.Map(zoom_start = 9, max_bounds=True)  
    countries = arr_allCountries[arr_allCountries != "Worldwide"]
    countries = countries[countries != "China"]
    for country in countries:
        df = df_entireDatasetSorted.query('Country_Region == @country & AdminRegion1 == 0 & AdminRegion2 == 0')
        # df.query('Updated == @date', inplace=True)
        latitude = df.iloc[0]['Latitude']
        longitude = df.iloc[0]['Longitude']
        country_name = df.iloc[0]['Country_Region']
        updated = df.iloc[0]['Updated']
        updatedText = updated.strftime('%d/%m/%Y')
        confirmed = str(df.iloc[0]['Confirmed'])
        deaths = str(df.iloc[0]['Deaths'])
        recovered = str(df.iloc[0]['Recovered'])
        tooltip = country_name
        popUp = "<i><b>"+country_name+"</b>"+"\n\n\n"+"Confirmed: \n"+confirmed+"\n\n"+"Deaths: \n"+deaths+"\n\n"+"Recovered: \n"+recovered+"\n\n"+"Last updated: \n"+updatedText+"</i>"
        folium.Marker([latitude, longitude], popup=popUp, tooltip=tooltip).add_to(map)
    worldMap = map
    return worldMap._repr_html_()

legend = None
labels = None
WorldwideCases = None
WorldwideDeaths = None
minimum_value = None
def createWorldCasesChart():
    global legend
    global labels
    global WorldwideCases
    global WorldwideDeaths
    global maximum_value
    legend = 'Cases Worldwide'
    country = "Worldwide"
    df = df_entireDataset.copy()
    df.query('Country_Region == @country', inplace=True)
    df.sort_values(by=['Updated'], inplace=True, ascending=False)
    first = df.iloc[0]['Updated']
    df.sort_values(by=['Updated'], inplace=True, ascending=True)
    last = df.iloc[0]['Updated']
    diff = ((first - last)/numpy.timedelta64(1, 'M'))
    diff = int(diff) + 1
    months = numpy.arange(1, diff+1, 1)
    cases = []
    deaths = []
    df = df_entireDataset.copy()
    for month in months:
        day = monthrange(2020, month)[1]
        date = pandas.Timestamp(year=2020, month=month, day=day)
        this_df = df.query('Updated == @date')
        totalCases = int(this_df.iloc[0]['Confirmed'])
        totalDeaths = int(this_df.iloc[0]['Deaths'])
        cases.append(totalCases)
        deaths.append(totalDeaths)
    newList = []
    for month in months:
        month_name = str(calendar.month_name[month])
        newList.append(month_name)
    months = newList
    df = df_entireDataset.copy()
    df.sort_values(by=['Confirmed'], inplace=True, ascending=False)
    maximum_value = int(this_df.iloc[0]['Confirmed']) + (int(this_df.iloc[0]['Confirmed'])/2)
    legend = legend
    # labels = months.tolist()
    labels = months
    WorldwideCases = cases
    WorldwideDeaths = deaths

def make_hyperlink(value):
    if value != "China":
        url = "/places?place={}"
        # return '=HYPERLINK("%s", "%s")' % (url.format(value), value)
        return u'<a href="%s">%s</a>' % (url.format(value), value)
    else:
        value = "China (mainland)"
        url = "/places?place=China (mainland)"
        # return '=HYPERLINK("%s", "%s")' % (url.format(value), value)
        return u'<a href="%s">China</a>' % (url.format(value))

allCountriesTable = None
def allCountriesTableCreate():
    global allCountriesTable
    countries = arr_allCountries[arr_allCountries != "Worldwide"]
    regions1 = arr_allRegions
    regions2 = df_entireDataset["AdminRegion2"].unique()
    df_countries = pandas.DataFrame()
    df = df_entireDatasetSorted.drop(columns=['ConfirmedChange', 'DeathsChange', 'RecoveredChange', 'Latitude', 'Longitude', 'ISO2', 'ISO3'])
    for country in countries: 
        df_country = df.query('Country_Region == @country & AdminRegion1 == 0 & AdminRegion2 == 0')
        if df_country['ID'].count() != 0:
            df_countries = df_countries.append(df_country.iloc[0])
    for region1 in regions1:
        df_region1 = df.query('AdminRegion1 == @region1 & AdminRegion2 == 0')
        if df_region1['ID'].count() != 0:
            df_countries = df_countries.append(df_region1.iloc[0])
    for region2 in regions2:
        df_region2 = df.query('AdminRegion2 == @region2')
        if df_region2['ID'].count() != 0:
            df_countries = df_countries.append(df_region2.iloc[0])
    df_countries['Updated'] = pandas.to_datetime(df_countries.Updated)
    df_countries['Confirmed'] = pandas.to_numeric(df_countries.Confirmed, downcast='integer')
    df_countries['Deaths'] = pandas.to_numeric(df_countries.Deaths, downcast='integer')
    df_countries['Recovered'] = pandas.to_numeric(df_countries.Recovered, downcast='integer')
    df_countries.index.name = '#'
    df_countries.columns.name = df_countries.index.name
    df_countries.index.name = None
    df_countries.sort_values(by=['Country_Region'], inplace=True, ascending=True)
    df_countries.reset_index(drop=True, inplace=True)
    df_countries.rename(columns={"Country_Region": "Country", "AdminRegion1": "Outer Region", "AdminRegion2": "Inner Region", "Updated": "Last Updated"}, inplace=True)
    df_countries["Outer Region"].replace({0: "---"}, inplace=True)
    df_countries["Inner Region"].replace({0: "---"}, inplace=True)
    df_countries = df_countries.drop(columns=['ID'])
    df_countries = df_countries[['Country', 'Outer Region', 'Inner Region', 'Confirmed', 'Deaths', 'Recovered', 'Last Updated']]
    df_countries[u'Country'] = df_countries[u'Country'].apply(lambda x: make_hyperlink(x))
    df_countries[u'Outer Region'] = df_countries[u'Outer Region'].apply(lambda x: make_hyperlink(x) if x != "---" else "---")
    df_countries[u'Inner Region'] = df_countries[u'Inner Region'].apply(lambda x: make_hyperlink(x) if x != "---" else "---")
    tables=[df_countries.to_html(classes=['data', 'table', 'table-striped', 'table-borderless'], header="true", justify='left', render_links=True, escape=False)]
    allCountriesTable = tables
    return allCountriesTable

def searchCountries(searchTerm):
    closeMatches = get_close_matches(searchTerm, arr_allCountries)
    return closeMatches

def dataUpdater():
    initialise()

@app.route('/')
def homepage():
    return render_template("index.html", latestDate = latestDatasetDateText, totalCases = totalCasesWorldwide, totalDeaths = totalDeathsWorldwide, totalRecovered = totalRecoveredWorldwide, worstHitCountry = worstHitCountry, worldMap = worldMap._repr_html_(), tables = latestUpdatesTable, labels=json.dumps(labels), WorldwideCases=json.dumps(WorldwideCases), WorldwideDeaths=json.dumps(WorldwideDeaths))

@app.route('/places')
def places_overview():
    place = request.args.get('place')
    if place == None:
        return render_template("places_overview.html", totalCases = totalCasesWorldwide, totalDeaths = totalDeathsWorldwide, totalRecovered = totalRecoveredWorldwide, worstHitCountry = worstHitCountry, worldMap = worldMap._repr_html_(), tables = allCountriesTable, labels=json.dumps(labels), WorldwideCases=json.dumps(WorldwideCases), WorldwideDeaths=json.dumps(WorldwideDeaths))
    else:
        return places(place)

def inner_region(inner_region): 
    allInnerRegionData = df_entireDatasetSorted.query('AdminRegion2 == @inner_region')
    dataRegion = allInnerRegionData
    lastupdated = dataRegion.iloc[0]['Updated']
    totalcases = dataRegion.iloc[0]['Confirmed']
    totalDeaths = dataRegion.iloc[0]['Deaths']
    totalRecovered = dataRegion.iloc[0]['Recovered']
    latitude = dataRegion.iloc[0]['Latitude']
    longitude = dataRegion.iloc[0]['Longitude']
    countryName = dataRegion.iloc[0]['Country_Region']
    outerRegionName = dataRegion.iloc[0]['AdminRegion1']
    regionName = inner_region
    regionsFullName = regionName + ", " + outerRegionName + ", " + countryName
    map = folium.Map(location = [latitude, longitude], zoom_start = 5, max_bounds=True) 
    innerRegions = allInnerRegionData["AdminRegion2"]
    innerRegions = innerRegions.unique().tolist()
    if 0 in innerRegions:
        innerRegions.remove(0)
    else:
        pass
    if dataRegion.shape[0] == 0:
        pass
    else:
        latitudeRegion = dataRegion.iloc[0]['Latitude']
        longitudeRegion = dataRegion.iloc[0]['Longitude']
        # country_name = df.iloc[0]['Country_Region']
        updated = dataRegion.iloc[0]['Updated']
        updatedText = updated.strftime('%d/%m/%Y')
        confirmed = str(dataRegion.iloc[0]['Confirmed'])
        deaths = str(dataRegion.iloc[0]['Deaths'])
        recovered = str(dataRegion.iloc[0]['Recovered'])
        tooltip = inner_region
        popUp = "<i><b>"+inner_region+"</b>"+"\n\n\n"+"Confirmed: \n"+confirmed+"\n\n"+"Deaths: \n"+deaths+"\n\n"+"Recovered: \n"+recovered+"\n\n"+"Last updated: \n"+updatedText+"</i>"
        folium.Marker([latitudeRegion, longitudeRegion], popup=popUp, tooltip=tooltip).add_to(map)
    return render_template("place.html", placeNameFull = regionsFullName, placeName = regionName, latestDate = lastupdated.strftime('%d/%m/%Y'), totalCases = "{:,}".format(totalcases), totalDeaths = "{:,}".format(totalDeaths), totalRecovered = "{:,}".format(totalRecovered), placeMap = map._repr_html_())

def outer_region(outer_region): 
    allOuterRegionData = df_entireDatasetSorted.query('AdminRegion1 == @outer_region')
    dataRegion = allOuterRegionData.query('AdminRegion2 == 0')
    lastupdated = dataRegion.iloc[0]['Updated']
    totalcases = dataRegion.iloc[0]['Confirmed']
    totalDeaths = dataRegion.iloc[0]['Deaths']
    totalRecovered = dataRegion.iloc[0]['Recovered']
    latitude = dataRegion.iloc[0]['Latitude']
    longitude = dataRegion.iloc[0]['Longitude']
    countryName = dataRegion.iloc[0]['Country_Region']
    regionName = outer_region
    regionsFullName = countryName + ", " + regionName
    map = folium.Map(location = [latitude, longitude], zoom_start = 5, max_bounds=True) 
    innerRegions = allOuterRegionData["AdminRegion2"]
    innerRegions = innerRegions.unique().tolist()
    innerRegions.remove(0)
    for region in innerRegions:
        df = allOuterRegionData.query('AdminRegion2 == @region')
        if df.shape[0] == 0:
            continue
        else:
            latitudeRegion = df.iloc[0]['Latitude']
            longitudeRegion = df.iloc[0]['Longitude']
            # country_name = df.iloc[0]['Country_Region']
            updated = df.iloc[0]['Updated']
            updatedText = updated.strftime('%d/%m/%Y')
            confirmed = str(df.iloc[0]['Confirmed'])
            deaths = str(df.iloc[0]['Deaths'])
            recovered = str(df.iloc[0]['Recovered'])
            tooltip = region
            popUp = "<i><b>"+region+"</b>"+"\n\n\n"+"Confirmed: \n"+confirmed+"\n\n"+"Deaths: \n"+deaths+"\n\n"+"Recovered: \n"+recovered+"\n\n"+"Last updated: \n"+updatedText+"</i>"
            folium.Marker([latitudeRegion, longitudeRegion], popup=popUp, tooltip=tooltip).add_to(map)
    return render_template("place.html", placeNameFull = regionsFullName, placeName = regionName, latestDate = lastupdated.strftime('%d/%m/%Y'), totalCases = "{:,}".format(totalcases), totalDeaths = "{:,}".format(totalDeaths), totalRecovered = "{:,}".format(totalRecovered), placeMap = map._repr_html_())

def country(country): 
    allCountryData = df_entireDatasetSorted.query('Country_Region == @country')
    dataCountry = allCountryData.query('AdminRegion1 == 0 & AdminRegion2 == 0')
    lastupdated = dataCountry.iloc[0]['Updated']
    totalcases = dataCountry.iloc[0]['Confirmed']
    totalDeaths = dataCountry.iloc[0]['Deaths']
    totalRecovered = dataCountry.iloc[0]['Recovered']
    latitude = dataCountry.iloc[0]['Latitude']
    longitude = dataCountry.iloc[0]['Longitude']
    map = folium.Map(location = [latitude, longitude], zoom_start = 5, max_bounds=True) 
    outerRegions = allCountryData["AdminRegion1"]
    outerRegions = outerRegions.unique().tolist()
    outerRegions.remove(0)
    for region in outerRegions:
        df = allCountryData.query('AdminRegion1 == @region & AdminRegion2 == 0')
        # df.query('Updated == @date', inplace=True)
        if df.shape[0] == 0:
            continue
        else:
            latitudeRegion = df.iloc[0]['Latitude']
            longitudeRegion = df.iloc[0]['Longitude']
            # country_name = df.iloc[0]['Country_Region']
            updated = df.iloc[0]['Updated']
            updatedText = updated.strftime('%d/%m/%Y')
            confirmed = str(df.iloc[0]['Confirmed'])
            deaths = str(df.iloc[0]['Deaths'])
            recovered = str(df.iloc[0]['Recovered'])
            tooltip = region
            popUp = "<i><b>"+region+"</b>"+"\n\n\n"+"Confirmed: \n"+confirmed+"\n\n"+"Deaths: \n"+deaths+"\n\n"+"Recovered: \n"+recovered+"\n\n"+"Last updated: \n"+updatedText+"</i>"
            folium.Marker([latitudeRegion, longitudeRegion], popup=popUp, tooltip=tooltip).add_to(map)
    return render_template("place.html", placeNameFull = country, placeName = country, latestDate = lastupdated.strftime('%d/%m/%Y'), totalCases = "{:,}".format(totalcases), totalDeaths = "{:,}".format(totalDeaths), totalRecovered = "{:,}".format(totalRecovered), placeMap = map._repr_html_())

@app.route("/search")
def search():
    place = request.args['place']
    originalPlace = place
    countries = arr_allCountries.tolist()
    countries = [item.lower() for item in countries]
    regions1 = arr_allRegions.tolist()
    regions1.remove(0)
    regions1 = [item.lower() for item in regions1]
    regions2 = arr_allRegions2.tolist()
    regions2.remove(0)
    regions2 = [item.lower() for item in regions2]
    place = place.lower()
    if place in countries and place != "China":
        return country(titlecase(place))
    elif place in regions1:
        return outer_region(place.title())
    elif place in regions2:
        return inner_region(place.title())
    else:
        closeMatchCountry = get_close_matches(place, countries, n=5, cutoff=0.1)
        closeMatchRegion1 = get_close_matches(place, regions1, n=5, cutoff=0.1)
        closeMatchRegion2 = get_close_matches(place, regions2, n=5, cutoff=0.1)
        df_SuggestedCountries = pandas.DataFrame(closeMatchCountry)
        df_SuggestedRegions1 = pandas.DataFrame(closeMatchRegion1)
        df_SuggestedRegions2 = pandas.DataFrame(closeMatchRegion2)
        if (df_SuggestedCountries.shape[0] == 0 & df_SuggestedRegions1.shape[0] == 0 & df_SuggestedRegions2.shape[0] == 0):
            return render_template('search-empty.html', searchTerm = place)
        else:
            df_SuggestedCountries.index.name = '#'
            df_SuggestedCountries.columns.name = df_SuggestedCountries.index.name
            df_SuggestedCountries.index.name = None
            df_SuggestedRegions1.index.name = '#'
            df_SuggestedRegions1.columns.name = df_SuggestedRegions1.index.name
            df_SuggestedRegions1.index.name = None
            df_SuggestedRegions2.index.name = '#'
            df_SuggestedRegions2.columns.name = df_SuggestedRegions2.index.name
            df_SuggestedRegions2.index.name = None
            df_SuggestedCountries.rename(columns={0: "Country"}, inplace=True)
            df_SuggestedRegions1.rename(columns={0: "Outer Region"}, inplace=True)
            df_SuggestedRegions2.rename(columns={0: "Inner Region"}, inplace=True)
            df_SuggestedCountries[u'Country'] = df_SuggestedCountries[u'Country'].apply(lambda x: make_hyperlink(x))
            df_SuggestedRegions1[u'Outer Region'] = df_SuggestedRegions1[u'Outer Region'].apply(lambda x: make_hyperlink(x))
            df_SuggestedRegions2[u'Inner Region'] = df_SuggestedRegions2[u'Inner Region'].apply(lambda x: make_hyperlink(x))
            df_SuggestedCountriesHTML=[df_SuggestedCountries.to_html(classes=['404-suggestions-data', 'table', 'table-striped', 'table-borderless'], header="true", justify='left', render_links=True, escape=False)]
            df_SuggestedRegions1HTML=[df_SuggestedRegions1.to_html(classes=['404-suggestions-data', 'table', 'table-striped', 'table-borderless'], header="true", justify='left', render_links=True, escape=False)]
            df_SuggestedRegions2HTML=[df_SuggestedRegions2.to_html(classes=['404-suggestions-data', 'table', 'table-striped', 'table-borderless'], header="true", justify='left', render_links=True, escape=False)]
            return render_template('404-suggestions.html', searchTerm = place, tblCountries = df_SuggestedCountriesHTML, tblRegions1 = df_SuggestedRegions1HTML, tblRegions2 = df_SuggestedRegions2HTML)
    return render_template("place.html")

# @app.route("/places/<place>")
def places(place):
    originalPlace = place
    countries = arr_allCountries.tolist()
    countries = [item.lower() for item in countries]
    regions1 = arr_allRegions.tolist()
    regions1.remove(0)
    regions1 = [item.lower() for item in regions1]
    regions2 = arr_allRegions2.tolist()
    regions2.remove(0)
    regions2 = [item.lower() for item in regions2]
    place = place.lower()
    if place in countries and place != "China":
        return country(titlecase(place))
    elif place in regions1:
        return outer_region(place.title())
    elif place in regions2:
        return inner_region(place.title())
    else:
        abort(404)
    return render_template("place.html")

@app.route("/world-map")
def world_map():
    return render_template("world-map.html", worldMap = worldMap._repr_html_())

@app.route("/bug-report")
def bug_report():
    return render_template("bug-report.html")

@app.route("/feature-request")
def feature_request():
    return render_template("feature-request.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/directory")
def directory():
    return render_template("directory.html", tables = allCountriesTable)

@app.errorhandler(500)
def server_error(e):
    if is_initialising == True:
        now = datetime.now()
        timestamp = datetime.now()
        timestampText = timestamp.strftime("%d-%m-%Y (%H:%M:%S)")
        error = str('<p class="lead">Here\'s what Mr. Server has to say:</p>')
        # error2 = str('<samp class="text-left text-wrap">['+str(datetime.fromtimestamp(timestamp))+']' + ' FATAL - ERROR 500' + '<br>['+str(datetime.fromtimestamp(timestamp))+']' + ' ERROR - Variables holding metrics are null!' + '<br>['+str(datetime.fromtimestamp(timestamp))+']' + ' WARN - Dataset is still being loaded' + '<br><br>['+str(datetime.fromtimestamp(timestamp))+']' + ' WARN - Hi human, I\'m still parsing data, I\'ll be done soon! :-)</samp>')
        error2 = str('<samp class="text-left text-wrap">['+str(timestampText)+']' + ' <span class="text-danger font-weight-bold">FATAL</span> - ERROR 500' + '<br>['+str(timestampText)+']' + ' <span class="text-danger">ERROR</span> - Variables holding metrics are null!' + '<br>['+str(timestampText)+']' + ' <span class="text-warning font-weight-bold">WARN</span> - Dataset is still being loaded' + '<br><br>['+str(timestampText)+']' + ' <span class="text-info font-weight-bold">INFO</span> - Hi human, I\'m still parsing data, I\'ll be done soon! :-)</samp><hr>')
        errorText = Markup(error + error2)
        return render_template('500.html', errorMessage = errorText)
    else:
        return render_template('500.html'), 500

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(400)
def not_found(e):
    return render_template('400.html'), 400

def start_initialise():
    initialise()

if __name__ == "__main__":
    t = threading.Thread(target=start_initialise)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', debug = False, threaded=True)

    
