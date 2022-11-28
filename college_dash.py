# better viewed with Goolge Chrome; Popup won't correctly work with Safari
import streamlit as st
import folium 

st.set_page_config(layout="wide")
import numpy as np
import pandas as pd
import geopandas
from streamlit_folium import st_folium   

input_file = "Data/college_merged_data.csv" # from my other project https://github.com/aleeshen/college-map
rank_file = 'Data/college_rank2023.csv' # from US News

title = "Discover Colleges  🇺🇸 USA" 
st.markdown(f'<p style="text-align:center;background-image:linear-gradient(to right, brown, navy); color:yellow; font-size:24px; border-radius:0%;"> {title}</p>', 
            unsafe_allow_html=True)

st.sidebar.title("Colleges on Map 🎓🏫")

st.sidebar.markdown("I created this dashboard app using python Streamlit to view colleges on map. More info can be added later on, such as application deadlines ...")

st.sidebar.title("Usage")

st.sidebar.markdown("Select State >> College; the selected will be displayed on map as a Star marker while the others as dots. \
                    \n The Ivy League colleges are in green.")
                    
st.sidebar.markdown("Click on the selected college to view more info and hover the mouse for the other colleges.")   
                    
#@st.cache(persist=True) # for large data
def load_data():
    data = pd.read_csv(input_file)
    return data

data = load_data()

ranking = pd.read_csv(rank_file)

data =  data.merge(ranking[['ID', 'Rank']], left_on='ID', right_on='ID', how='left')

geom = geopandas.points_from_xy(data[['LONGITUDE']], 
                                data[['LATITUDE']])
mygeom = geopandas.GeoDataFrame(data, geometry=geom)
mygeom.reset_index(inplace=True) # make sure continuous index

## add ivy info
nms = data['Name'].tolist()
import re
ivies = list(filter(lambda v: re.match('yale|brown|harvard|dartmouth|university of Pennsylvania|Columbia University|Cornell|Princeton', v, re.IGNORECASE), nms))

mygeom['Ivy'] = 0
mygeom.loc[mygeom['Name'].isin(ivies), 'Ivy'] = 1

states = data['STATE'].drop_duplicates()
types = data['Control of institution'].drop_duplicates()

state_sidebar = st.sidebar.selectbox('1 - Select a state:', ['US - all states'] + states.tolist())

if state_sidebar == 'US - all states':
    data_state = data
else:
    data_state = data.query('STATE == @state_sidebar')

colleges = data_state['Name'].drop_duplicates()
college_sidebar = st.sidebar.selectbox('2 - Select a college:', colleges)

data_college = data_state.query('Name == @college_sidebar') 

mymap = folium.Map(location=[50, -100], tiles="OpenStreetMap", zoom_start=6)

## could have multiple results
for myidx, myrow in mygeom.query('Name in @colleges').iterrows():
    mycoord = [myrow['geometry'].xy[1][0], myrow['geometry'].xy[0][0]]                           

    myweb = 'https://' + re.sub('.*www.', '', myrow['INSTURL'].strip('/')) 
    ######must in this format 'https://umich.edu'
        
    # for tooltip
    mytip = f""" <strong>{str(myrow['Name'])}</strong> {myrow['CITY']} {myrow['STATE']} <br>
            {myrow['Control of institution']}; {myrow['Urbanization']} <br> 
            {myrow['CarnegieClass']} <br>
            Acceptance: {str(myrow['Percent admitted - total (DRVADM2021)'])}  <br>
            Yield: {str(myrow['Admissions yield - total (DRVADM2021)'])} <br>
            Student/Faculty: {str(myrow['Student-to-faculty ratio (EF2020D)'])}
            """
            
    # for popup        
    html=f"""
        <h3> {str(myrow['Name'])} </h3>
        <p>Basic info:</p>
        <ul>
            <li> {myrow['Control of institution']}; {myrow['Urbanization']} </li>
            <li> {myrow['CarnegieClass']} </li>
            <li>Acceptance: {str(myrow['Percent admitted - total (DRVADM2021)'])}</li>
            <li>Yield: {str(myrow['Admissions yield - total (DRVADM2021)'])}</li>
            <li>Student/Faculty: {str(myrow['Student-to-faculty ratio (EF2020D)'])}</li>
            
        </ul>
        </p>
        <p>website: <a href="{myweb}"target="_blank">{myweb}</a></p>
        """
    mypopup = folium.IFrame(html=html, width=450, height=250)
    
    if myrow['Ivy'] == 1:
        type_color = "green"
    else:
        type_color = "blue"
    
    if myrow['Name'] == college_sidebar:
        mymap.location=mycoord
        myicon = folium.Icon(icon='star', color=type_color, prefix='fa')
        
        mymap.add_child(
            folium.Marker(
                location=mycoord,
                popup = folium.Popup(mypopup, max_width=1200, parse_html=True),
                tooltip = f""" <strong><font color="brown">{str(myrow['Name'])}</font></strong> {myrow['CITY']} {myrow['STATE']} <br>
                Click to display info""",
                icon=myicon
            )
            )
    else:
        myicon = folium.DivIcon(html = f"""
            <div><svg>
                <circle cx="5" cy="5" r="5" fill={type_color} opacity=".75"/>
            </svg></div>""") 
            
        mymap.add_child(
        folium.Marker(
            location=mycoord,
            tooltip = mytip,
            icon=myicon
            )
        )
    

st_folium(mymap, width=1200, height=600)

st.sidebar.title("US News Ranking 2023: National Colleges 🏅 (top 150 colleges) ")

myrank = data_college['Rank'].tolist()[0]
if np.isnan(myrank):
    myrank = '>137 - rank not included'
else:
    mycnt = (data['Rank']==myrank).sum()
    myrank = int(myrank)
    if mycnt > 1:
        myrank = f'{myrank} - {mycnt} ties'

ranking = f""" <p style="font-family:sans-serif; color:brown; font-size: 36px;"># {myrank}</p>"""
st.sidebar.markdown(ranking, unsafe_allow_html=True)

note = f'<p style="font-family:sans-serif; color:grey; font-size: 14px;"> Only top 150 colleges, with lowest rank of 137 including ties, are available here. </p>'
st.sidebar.markdown(note, unsafe_allow_html=True)

