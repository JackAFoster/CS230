import streamlit as st
import pydeck as pdk
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import altair as alt
path = "/Users/jacka/Desktop/CS 230/Map/"


df = pd.read_csv(path + "Meteorite_Landings.csv")
df = df.dropna()
#Map data must contain a column named "latitude" or "lat"
st.write(df)
continent_ranges = {
    'North America': {'lat_range': (5, 83), 'lon_range': (-175, -45)},
    'South America': {'lat_range': (-60, 15), 'lon_range': (-90, -30)},
    'Europe': {'lat_range': (36, 71), 'lon_range': (-10, 60)},
    'Africa': {'lat_range': (-35, 37), 'lon_range': (-20, 55)},
    'Asia': {'lat_range': (9, 77), 'lon_range': (25, 180)},
    'Australia': {'lat_range': (-45, -7), 'lon_range': (110, 155)}
}
selected_map = st.sidebar.radio("Please select the map", ["Home Page", "Continents", "Largest",])
# Split GeoLocation column into latitude and longitude columns
df[["lat", "lon"]] = df["GeoLocation"].str.split(",", expand=True)
df = df.rename(columns={"Mass (g)": "grams"})
# Convert latitude and longitude columns to float type
df['lat'] = df['lat'].str.replace('(', '').astype(float)
df['lon'] = df['lon'].str.replace(')', '').astype(float)

df['year'] = pd.to_datetime(df['year']).dt.year
min_year = None
max_year = None
min_year = int(df['year'].min())-1
max_year = int(df['year'].max())+1



trim = pd.DataFrame(columns=['lat', 'lon', 'continent'])
year_range = st.slider("Select a range of years", min_value=min_year, max_value=max_year, value=(min_year, max_year))
filtered_df = df
filtered_df = df[(df['year'] >= year_range[0]) & (df['year'] <= year_range[1])]




# Add a new column to the DataFrame to identify the continent for each meteorite landing
df['continent'] = None
for index, row in df.iterrows():
    lat = row["reclat"]
    lon = row["reclong"]
    for continent in continent_ranges:
        lat_range = continent_ranges[continent]["lat_range"]
        lon_range = continent_ranges[continent]["lon_range"]
        if lat_range[0] <= lat <= lat_range[1] and lon_range[0] <= lon <= lon_range[1]:
            df.at[index, "continent"] = continent
            break
continent_counts = df.groupby("continent").size().reset_index(name="Counts")
chart = alt.Chart(continent_counts).mark_bar().encode(
    x=alt.X("continent:N", sort=list(continent_ranges.keys())),
    y="Counts",
    tooltip=["continent", "Counts"]
).properties(width=600, height=600)
st.altair_chart(chart)
grouped_df = df.groupby('continent').size().reset_index(name='counts')




def create_pie_chart(df):
    mass_bins = [0, 100, 1000, 10000, 100000, 1000000, 10000000, 100000000, 1000000000]
    labels = [f"{mass_bins[i]:,d} - {mass_bins[i+1]:,d}" for i in range(len(mass_bins)-1)]
    values = [df[(df["mass (g)"] >= mass_bins[i]) & (df["mass (g)"] < mass_bins[i+1])]["name"].count() for i in range(len(mass_bins)-1)]
    chart_data = pd.DataFrame({"Weight in grams": labels, "values": values})
    chart_data = chart_data.sort_values("values")
    chart = alt.Chart(chart_data).mark_arc().encode(
        theta="values",
        color="Weight in grams",
        tooltip=["Weight in grams", "values"]
    ).properties(width=600, height=600)
    return chart

if selected_map == "Continents":
    st.title('Continents')
    labels = list(df.index)
    values = list(df['name'])
    continent_ranges = dict(continent_ranges)
    continent_filter = st.sidebar.multiselect('Select Continents', continent_ranges.keys())
    if continent_filter:

        for index, row in filtered_df.iterrows():
            lat = row['lat']
            lon = row['lon']
            for continent in continent_filter:
                lat_range = continent_ranges[continent]['lat_range']
                lon_range = continent_ranges[continent]['lon_range']
                if lat_range[0] <= lat <= lat_range[1] and lon_range[0] <= lon <= lon_range[1]:
                    trim.loc[len(trim)] = row

            # place marker on map at latitude and longitude of meteorite
    else:
        filtered_df = df


    filtered_df = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]
    filtered_df["marker_size"] = filtered_df["mass (g)"] / 500
    # The most basic map, st.map(df)

    view_state = pdk.ViewState(
        latitude=filtered_df["lat"].mean(),  # The latitude of the view center
        longitude=filtered_df["lon"].mean(),  # The longitude of the view center
        zoom=2,  # View zoom level
        pitch=0)  # Tilt level

    # Create a map layer with the given coordinates
    layer1 = pdk.Layer(
        type='ScatterplotLayer',  # layer type
        data=filtered_df,  # data source
        get_position='[lon, lat]',  # coordinates
        get_radius='marker_size',  # scatter radius
        get_color=[0, 0, 255],  # scatter color
        pickable=True  # work with tooltip
    )

    # Stylish tool tip: https://pydeck.gl/tooltip.html?highlight=tooltip
    tool_tip = {"html": "Name:<br/> <b>{name}</b> <br/> <b>{mass (g)}<b>",
                "style": {"backgroundColor": "orange",
                          "color": "white"}
                }

    st.map(trim)


elif selected_map == "Largest":

    st.title("Biggest By Mass")
    df.sort_values("mass (g)", ascending=False, inplace=True)
    bigboys = df.head(5)

    view_state = pdk.ViewState(
        latitude=bigboys["lat"].mean(),  # The latitude of the view center
        longitude=bigboys["lon"].mean(),  # The longitude of the view center
        zoom=2,  # View zoom level
        pitch=0)  # Tilt level

    # Create a map layer with the given coordinates
    layer1 = pdk.Layer(type = 'ScatterplotLayer', # layer type
                      data=bigboys, # data source
                      get_position='[lon, lat]', # coordinates
                      get_radius=100000, # scatter radius
                      get_color=[0,0,255],   # scatter color
                      pickable=True # work with tooltip
                      )

   # stylish tool tip: https://pydeck.gl/tooltip.html?highlight=tooltip
    tool_tip = {"html": "Name:<br/> <b>{name}</b> <br/> <b>{mass (g)}<b>",
                "style": { "backgroundColor": "orange",
                            "color": "white"}
              }

    # Create a map based on the view, layers, and tool tip
    map = pdk.Deck(
        map_style='mapbox://styles/mapbox/outdoors-v11', # Go to https://docs.mapbox.com/api/maps/styles/ for more map styles
        initial_view_state=view_state,
        layers=[layer1], # The following layer would be on top of the previous layers
        tooltip= tool_tip
    )

    st.pydeck_chart(map) # Show the map in your app

st.altair_chart(create_pie_chart(df))

