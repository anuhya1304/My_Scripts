import pandas as pd
import numpy as np
from scipy.stats import circmean


def ReadData(uploaded_file):
    """
    Reads and prepares data by selecting necessary columns
    and converting the Timestamp to datetime format.
    """
    # Read the uploaded CSV file
    data = pd.read_csv(uploaded_file)

    # Select only the 'Timestamp', 'speed', and 'direction' columns
    data = data[['Timestamp', 'speed', 'direction']]

    # Convert 'Timestamp' to datetime format
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], dayfirst=True)

    return data


def circular_mean(angles):
    angles_rad = np.deg2rad(angles)
    mean_angle_rad = circmean(angles_rad, high=np.pi, low=-np.pi)
    mean_angle_deg = np.rad2deg(mean_angle_rad)
    return mean_angle_deg

# Function to process data and store results in session state


def process_data(long_data,  merged_data_filtered):
    """
    Processes data to calculate corrected wind speed and adjusted directions.
    Stores the results in session state for further use.
    """
    # Define sector boundaries and labels
    sector_boundaries = [15, 45, 75, 105, 135,
                         165, 195, 225, 255, 285, 315, 345]
    sector_labels = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 0]

    # Helper function to assign sector based on direction
    def assign_sector(direction):
        for i in range(len(sector_boundaries)):
            if i == len(sector_boundaries) - 1:
                if direction >= sector_boundaries[i] or direction < sector_boundaries[0]:
                    return sector_labels[i]
            elif sector_boundaries[i] <= direction < sector_boundaries[i + 1]:
                return sector_labels[i]
        return None

    # Fit linear models for each sector
    grouped = merged_data_filtered.groupby(
        merged_data_filtered['direction_1'].apply(assign_sector))
    models = {}
    errors = {}

    for sector, group in grouped:
        x_data = group['speed_1'].values
        y_data = group['speed'].values

        try:
            coeffs = np.polyfit(x_data, y_data, 1)
            models[sector] = coeffs
            residuals = y_data - np.polyval(coeffs, x_data)
            errors[sector] = np.std(residuals)
        except Exception as e:
            print(f"Could not fit linear model for sector {sector}: {e}")

    # Predict corrected speeds
    def predict_corrected_speed(sector, speed_long):
        if sector in models:
            m, b = models[sector]
            predicted_speed = m * speed_long + b
            if sector in errors:
                noise = np.random.normal(0, errors[sector])
                return max(0, predicted_speed + noise)
            return max(0, predicted_speed)
        return None

    crt_data = long_data.copy()
    crt_data['sector_Long'] = crt_data['direction'].apply(assign_sector)
    crt_data['corrected_speed'] = crt_data.apply(
        lambda row: predict_corrected_speed(row['sector_Long'], row['speed']), axis=1
    )
    crt_data['speed'] = crt_data['corrected_speed'].round(2)

    # Calculate WD Delta and adjust new directions
    merged_data_filtered['WD_Delta'] = merged_data_filtered['direction'] - \
        merged_data_filtered['direction_1']
    merged_data_filtered['sector_long'] = merged_data_filtered['direction_1'].apply(
        assign_sector)

    wd_sec_delta = merged_data_filtered.groupby('sector_long')['WD_Delta'].apply(
        circular_mean).reset_index(name='WD SecDelta')
    crt_data = crt_data.merge(
        wd_sec_delta, left_on='sector_Long', right_on='sector_long', how='left')

    circular_mean_0 = wd_sec_delta[wd_sec_delta['sector_long']
                                   == 0]['WD SecDelta'].iloc[0]

    def adjust_new_direction(row):
        if row['sector_Long'] == 0.2:
            return (row['direction'] + circular_mean_0 + 360) % 360
        elif row['sector_Long'] == 0.1:
            return (row['direction'] + circular_mean_0) % 360
        else:
            return (row['direction'] + row['WD SecDelta']) % 360

    crt_data['new_direction'] = crt_data.apply(adjust_new_direction, axis=1)

    ltc_data = crt_data[['Timestamp', 'speed', 'new_direction']].round(2)

    return ltc_data
