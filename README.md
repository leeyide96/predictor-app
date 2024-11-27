# HDB Resale Price Predictor

A Streamlit web application that predicts HDB (Housing & Development Board) resale prices in Singapore based on location, flat type, and nearby amenities.

Data are constantly updated via MLOps pipeline that leverages on Airflow and GCP. The code for the pipeline can be found in https://github.com/leeyide96/mlops_resale_price

## Features

- Interactive map selection for property location
- Price prediction based on:
  - Flat type (1-room to 5-room)
  - Remaining lease years
  - Floor level
  - Location-based factors
- Detailed analysis of nearby amenities including:
  - MRT stations
  - Hawker centers and food markets
  - Primary and secondary schools
  - Property market indices

## How to Use


1. **Select Location**
   - Open the app and you'll see a map of Singapore
   - Click anywhere on the map to select your desired location
   - The coordinates will be displayed on the right side of the map

2. **Enter Property Details**
   - Choose your flat type from the dropdown menu (1-room to 5-room)
   - Use the slider to select remaining lease years (20-95 years)
   - Use the slider to select the floor level (1-50)
   - Click "Submit" to generate the prediction

3. **View Results**
   - The app will display the predicted resale price in SGD
   - You'll see a comprehensive breakdown of nearby amenities:
     - List of nearby MRT stations
     - Nearby hawker centers and food markets
     - Primary and secondary schools in the vicinity
   - Click "Return to main page" to make another prediction

*Sometimes, you might see a huge gap between the map and the dropdown. Refresh the page if you do.*

## Technical Details

The application uses several data sources and components:

- OneMap API for Singapore map visualization
- Distance-based calculations for nearby amenities
- Machine learning model for price predictions

## Notes

- Predictions are based on historical data and market trends
- The application takes into account various factors including proximity to amenities and property characteristics
- All distances are calculated using geodesic distance 
