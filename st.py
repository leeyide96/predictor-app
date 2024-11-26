import streamlit as st
import folium
from streamlit_folium import folium_static, st_folium
from typing import Tuple
import os
import requests
from io import BytesIO
import joblib
import pandas as pd
from utils import count_nearby
from datetime import datetime

PUBLIC_BUCKET = os.getenv('PUBLIC_BUCKET')
CF_LINK = os.getenv('CF_LINK')

@st.cache_resource
def load_encoder_from_public_gcs(gcs_url):
    """
    Load a joblib encoder from a public Google Cloud Storage bucket.

    Parameters:
    gcs_url (str): The public URL to the encoder.joblib file
        Example: 'https://storage.googleapis.com/your-bucket-name/encoder.joblib'

    Returns:
    object: The loaded encoder object
    """

    # Make a GET request to download the file
    response = requests.get(gcs_url)

    # Load the encoder from the downloaded bytes
    encoder = joblib.load(BytesIO(response.content))
    return encoder


@st.cache_data
def retrieve_csv(url):
    data = pd.read_csv(url)
    return data

def get_tilejson_config():
    """Fetch the TileJSON configuration from OneMap."""
    url = "https://www.onemap.gov.sg/maps/json/raster/tilejson/2.2.0/Default.json"
    response = requests.get(url)
    return response.json()


def create_singapore_map(config: dict, center: Tuple[float, float] = (1.3521, 103.8198)) -> folium.Map:
    """
    Create a Folium map using OneMap's TileJSON configuration.
    """
    # Extract configuration from TileJSON
    min_zoom = config.get('minzoom', 11)
    max_zoom = config.get('maxzoom', 19)
    bounds = bounds = config.get('bounds', [103.6, 1.15, 104.0, 1.45])  # [west, south, east, north]

    # Create the map centered on Singapore
    singapore_map = folium.Map(
        location=center,
        zoom_start=min_zoom + 1,  # Start at one zoom level above minimum
        tiles=config['tiles'][0],  # Use the first tile URL from the config
        attr="OneMap",
        min_zoom=min_zoom,
        max_zoom=max_zoom,
        control_scale=True
    )

    # Set map bounds
    singapore_map.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    return singapore_map

@st.fragment
def display_coordinates_map(config):
    col1, col2 = st.columns([3,1])
    with col1:
        st.write("Click anywhere on the map to get coordinates")
        # Create the map using TileJSON config
        m = create_singapore_map(config)
        # Add click event handling
        m.add_child(folium.LatLngPopup())
        map_data = st_folium(m, width=None, height=400)

    with col2:
        if map_data['last_clicked']:
            lat = map_data['last_clicked']['lat']
            lng = map_data['last_clicked']['lng']
            # Show current clicked coordinates
            st.write("Currently selected coordinates:")
            st.write(f"Latitude: {lat:.6f}")
            st.write(f"Longitude: {lng:.6f}")
            st.session_state.clicked_coords = (lat, lng)

def return_main():
    st.session_state.page = "main"

def generate_list_items(items):
    return (' ').join([f'  '
                      f'- {item}' for item in items])

def display_price_page():
    today = datetime.now()
    with st.status("", expanded=True):
        st.write("Parsing data")
        yearquarter = f"{today.year}Q{(today.month - 1) // 3 + 1}"
        room = int(st.session_state.flat_type[0])
        remaining_lease = int(st.session_state.years_left)
        level = st.session_state.floor // 3
        info = []
        facilities_nearby = {}
        for name_col, df in st.session_state.data.items():
            if name_col == "index":
                index = df[df.quarter == yearquarter]["index"].iloc[0]
                info.append(index)
            elif name_col == 'town':
                _, _, town = count_nearby(st.session_state.clicked_coords, df, 0.5, name_col)
                town_df = pd.DataFrame({name_col: town})
                town_enc = st.session_state.encoder.transform(town_df).iloc[0]
                info.append(int(town_enc))
            elif name_col == 'school_name':
                pri_sch = df[df.mainlevel_code == "PRIMARY"]
                count, nearest_dist, pri_facilities = count_nearby(st.session_state.clicked_coords, pri_sch, 1, name_col)
                info.extend([count, nearest_dist])
                facilities_nearby[name_col + "_pri"] = pri_facilities
                sec_sch = df[df.mainlevel_code == "SECONDARY"]
                count, nearest_dist, sec_facilities = count_nearby(st.session_state.clicked_coords, sec_sch, 1, name_col)
                info.extend([count, nearest_dist])
                facilities_nearby[name_col+"_sec"] = sec_facilities
            else:
                count, nearest_dist, facilities = count_nearby(st.session_state.clicked_coords, df, 1, name_col)
                info.extend([count, nearest_dist])
                facilities_nearby[name_col] = facilities
        info.extend([room, remaining_lease, level])
        st.write("Data Processed")
        st.write("Predicting Price")
        response = requests.post(CF_LINK, json={"instances": [info]})
        predicted_price = response.json()[0]
        st.write("Price Predicted")

    st.markdown("#### Property Details: ")

    # Basic Information
    st.markdown("##### Basic Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Flat Type", st.session_state.flat_type)
    with col2:
        st.metric("Lease Years Remaining", f"{st.session_state.years_left} years")
    with col3:
        st.metric("Predicted Price", f"{int(predicted_price)}K SGD")

    # Transportation
    st.divider()
    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown("##### Transportation")
        st.markdown("###### Nearby MRT Stations")
        for station in facilities_nearby["mrt_station_english"]:
            st.write(f"• {station}")

    # Amenities
    with col5:
        st.markdown("##### Amenities")
        st.markdown("###### Hawker Centers & Food Markets")
        for hawker in facilities_nearby["name"]:
            st.write(f"• {hawker}")

    # Education
    with col6:
        st.markdown("##### Education")
        st.markdown("###### Primary Schools in Vicinity")
        for school in facilities_nearby["school_name_pri"]:
            st.write(f"• {school}")
        st.markdown("###### Secondary Schools in Vicinity")
        for school in facilities_nearby["school_name_sec"]:
            st.markdown(f"• {school}")

    st.button("Return to main page", on_click=return_main)


@st.cache_data
def get_map_json():
    try:
        config = get_tilejson_config()
    except Exception as e:
        st.error("Failed to load map configuration. Please try again later.")
        st.stop()
    return config

def main_page():
    st.title("HDB Price Predictor")

    hawker_markets = retrieve_csv(f"{PUBLIC_BUCKET}/hawker_markets.csv")
    resale_index = retrieve_csv(f"{PUBLIC_BUCKET}/resale_index.csv")
    schools = retrieve_csv(f"{PUBLIC_BUCKET}/schools.csv")
    street_blocks = retrieve_csv(f"{PUBLIC_BUCKET}/street_blocks.csv")
    train_stations = retrieve_csv(f"{PUBLIC_BUCKET}/train_stations.csv")
    st.session_state.data = {"school_name": schools, "name": hawker_markets, "mrt_station_english": train_stations, "town": street_blocks, "index": resale_index}
    st.session_state.encoder = load_encoder_from_public_gcs(f"{PUBLIC_BUCKET}/meanencoder.joblib")
    # Fetch TileJSON configuration
    config = get_map_json()

    display_coordinates_map(config)
    with st.form("Form", border=False):
        option = st.selectbox(
            "Which type of HDB flat you want?",
            ("1-room", "2-room", "3-room", "4-room", "5-room"),
        )
        years = st.slider("Lease Years Left", 20, 95, step=5)
        floor = st.slider("Floor Level", 1, 50, step=1)
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state.flat_type = option
            st.session_state.years_left = years
            st.session_state.floor = floor
    _, _, town = count_nearby(st.session_state.clicked_coords, street_blocks, 0.5, "town")
    if submitted and town and st.session_state.clicked_coords:
        st.session_state.page = "display_price"
        st.rerun()
    elif submitted and not town:
        st.error("Please select your coordinates from urban area within Singapore", icon="🚨")

def main():

    # Initialize session state for clicked coordinates
    if all([var not in st.session_state for var in ['page', 'clicked_coords', 'flat_type', 'years_left', 'floor']]):
        st.session_state.clicked_coords = []
        st.session_state.flat_type = None
        st.session_state.years_left = None
        st.session_state.floor = None
        st.session_state.encoder = None
        st.session_state.data = {}
        st.session_state.page = "main"


    # Page routing
    page_functions = {"main": main_page, "display_price": display_price_page}
    to_run = page_functions[st.session_state.page]
    to_run()


if __name__ == "__main__":
    main()