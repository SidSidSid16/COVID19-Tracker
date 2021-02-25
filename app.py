import threading
from flask import Flask, render_template, Response
from covid import Covid
import folium
from geopy.geocoders import Nominatim
from datetime import datetime

import time

app = Flask(__name__)

covid = None

is_initialising = False
country_data_table = {}

def initialise():
    print("[INFO] starting initialisation...")
    global data_table
    global covid
    covid = Covid(source="worldometers")
    countries = covid.list_countries()
    countries = [x for x in countries if x]
    # active, deaths, recovered, total_tests, new_cases, new_deaths, critical_cases
    country_data = []
    continent_data = []
    continents = ["north america","south america","europe","asia","oceania","africa"]
    print("[INFO] variables initialised!")
    for country in countries:
        country_data = []
        continent_data = []

        this_region = str(country)
        if this_region.lower() in continents:
            # this_continent = covid.get_status_by_country_name(this_region)

            # continent_data.append(this_continent["active"])
            # continent_data.append(this_continent["deaths"])
            # continent_data.append(this_continent["recovered"])
            # continent_data.append(this_continent["total_tests"])
            # continent_data.append((this_continent["new_cases"]))
            # continent_data.append((this_continent["new_deaths"]))
            # continent_data.append((this_continent["critical"]))
            
            # #data_table[str(this_country["country"])] = continent_data
            # continent_data = []
            # this_continent = None
            pass
        elif this_region.lower() == "world":
            pass
        else:
            this_country = covid.get_status_by_country_name(this_region)

            country_data.append(this_country["active"])
            country_data.append(this_country["deaths"])
            country_data.append(this_country["recovered"])
            country_data.append(this_country["total_tests"])
            country_data.append((this_country["new_cases"]))
            country_data.append((this_country["new_deaths"]))
            country_data.append((this_country["critical"]))
            
            country_data_table[str(this_country["country"])] = country_data
            country_data = []
            this_country = None
    createWorldMap()
    print("[INFO] initialisation done!")
    is_initialising = False
    threading.Timer(10800, initialise).start()
    print("[INFO] Initialisation thread job started")
    
def get_country_data_table():
    return country_data_table

worldMap = None
worldMapComputePercent = 0
def createWorldMap():
    print("[INFO] Map initialisation started")
    global worldMap
    global worldMapComputePercent
    map = folium.Map(zoom_start = 7, max_bounds=True)
    geolocator = Nominatim(user_agent="http")
    totalCountries = 0
    totalCountries = len(country_data_table)
    countriesProcessed = 0
    for country in country_data_table:
        data_list = country_data_table[country]
        try:
            loc = geolocator.geocode(country)
            latitude = loc.latitude
            longitude = loc.longitude
        except:
            pass
        country_name = country
        total_cases = str(data_list[0])
        deaths = str(data_list[1])
        recovered = str(data_list[2])
        tooltip = country_name
        popUp = "<i><b>"+country_name+"</b>"+"\n\n\n"+"Total Cases: \n"+total_cases+"\n\n"+"Deaths: \n"+deaths+"\n\n"+"Recovered: \n"+recovered+"</i>"
        folium.CircleMarker(location=[latitude, longitude], popup=popUp, tooltip=tooltip, radius=2).add_to(map)
        countriesProcessed += 1
        worldMapComputePercent = round((countriesProcessed/totalCountries)*100)
        # print("[INFO] Map " + str(worldMapComputePercent) + "'%' initialised")
    worldMap = map
<<<<<<< Updated upstream
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
    diff = int(diff)
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
=======
    print("[INFO] Map initialised")
    
def returnWorldMap():
    if worldMap == None:
        # return str("Map " + str(worldMapComputePercent) + "% initialised with updated data. Please allow some time before refreshing the page.")
        return '''
        <div class="progress"><div id="worldMapLoadStatus" class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" aria-valuenow="" aria-valuemin="0" aria-valuemax="100"></div></div>
        
        <div class="card border-left-primary shadow h-100 w-100 py-2">
            <div class="card-body">
                <div class="row h-100 w-100">
                    <div class="row no-gutters align-items-center">
                        <div class="col mr-2 h-100">
                            <div class="text-s font-weight-bold text-primary text-uppercase mb-1">
                                Updating World Map Data: </div>
                            <div class="h5 mb-0 font-weight-bold text-gray-800">Please wait while the world map is being updated with new data.<br> This only happens when the COVID-19 dataset updates.</div>
                        </div>
                        <div class="col-auto">
                            <i class="fas fa-virus-slash fa-2x text-gray-300"></i>
                        </div>
                    </div> 
                </div>
            </div>
        </div>

        <script>

            var source = new EventSource("/progress/worldmap");

            function refresh()
            {
                $('#worldMap').load(document.URL +  ' #worldMap');
            }
            source.onmessage = function(event) {
                $('.progress-bar').css('width', event.data+'%').attr('aria-valuenow', event.data);
                $('.progress-bar-label').text(event.data+'%');

                if(event.data == 100){
                    source.close()
                    refresh()
                }
            }

        </script>
        
        '''
>>>>>>> Stashed changes
    else:
        return worldMap._repr_html_()

@app.route('/')
def index():
    return render_template(
        '/parts/home.html', 
        total_cases_active=covid.get_total_active_cases(),
        total_deaths=covid.get_total_deaths(),
        total_recovered=covid.get_total_recovered(),
        country_data_table=get_country_data_table(),
        worldMap=returnWorldMap(),
    )

@app.route('/progress/worldmap')
def progressWorldMap():
    def checkProgress():
        while worldMapComputePercent <= 100:
            yield "data:" + str(worldMapComputePercent) + "\n\n"
    return Response(checkProgress(), mimetype= 'text/event-stream')
    

if __name__ == "__main__":
    t = threading.Thread(target=initialise)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', debug = True, threaded=True,)