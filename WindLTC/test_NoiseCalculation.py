import pandas as pd
import numpy as np
from scipy.stats import circmean
from sklearn.linear_model import LinearRegression

#Calculating noise and without nosie
class NoiseCalculation:
    def __init__(self):
        # Define correct sector boundaries and labels
        self.sector_boundaries = [15, 45, 75, 105,
                                  135, 165, 195, 225, 255, 285, 315, 345]
        self.sector_labels = [30, 60, 90, 120,
                              150, 180, 210, 240, 270, 300, 330, 0]
        np.random.seed(45)  # Seed for reproducibility

    def assign_sector(self, direction):
        for i in range(len(self.sector_boundaries)):
            if i == len(self.sector_boundaries) - 1:
                if direction >= self.sector_boundaries[i] or direction < self.sector_boundaries[0]:
                    return self.sector_labels[i]
            elif self.sector_boundaries[i] <= direction < self.sector_boundaries[i + 1]:
                return self.sector_labels[i]
        return None

    def circular_mean(self, angles):
        angles_rad = np.deg2rad(angles)
        mean_angle_rad = circmean(angles_rad, high=np.pi, low=-np.pi)
        return np.rad2deg(mean_angle_rad)

    def with_noise(self, merged_data_filtered):
        # Create sector columns for both long and short directions
        merged_data_filtered['sector_long'] = merged_data_filtered['direction_1'].apply(
            lambda x: self.assign_sector(x))
        merged_data_filtered['sector_short'] = merged_data_filtered['direction'].apply(
            lambda x: self.assign_sector(x))

        # Calculate WD Delta
        merged_data_filtered['WD_Delta'] = merged_data_filtered['direction'] - \
            merged_data_filtered['direction_1']

        # Group by sector_long and calculate circular mean for WD_Delta
        wd_sec_delta_metrics = []
        grouped_wd = merged_data_filtered.groupby('sector_long')
        for sector, group in grouped_wd:
            WD_SecDelta = self.circular_mean(group['WD_Delta'])
            wd_sec_delta_metrics.append(
                {'Sector': sector, 'WD SecDelta': WD_SecDelta})

        wd_sec_delta_df = pd.DataFrame(wd_sec_delta_metrics)

        # Group by sector_long for linear model
        grouped = merged_data_filtered.groupby('sector_long')
        models = {}
        errors = {}

        for sector, group in grouped:
            x_data = group['speed_1'].values
            y_data = group['speed'].values
            try:
                coeffs = np.polyfit(x_data, y_data, 1)
                models[sector] = coeffs
                predicted_y = np.polyval(coeffs, x_data)
                residuals = y_data - predicted_y
                sigma = np.std(residuals)
                errors[sector] = sigma
            except Exception as e:
                print(f"Could not fit linear model for sector {sector}: {e}")

        def predict_corrected_speed(sector, speed_long):
            if sector in models:
                m, b = models[sector]
                predicted_speed = m * speed_long + b
                if sector in errors:
                    noise = np.random.normal(0, errors[sector])
                    corrected_speed = predicted_speed + noise
                    return max(0, corrected_speed)
                else:
                    return max(0, predicted_speed)
            else:
                return None

        merged_data_filtered['corrected_speed'] = merged_data_filtered.apply(
            lambda row: predict_corrected_speed(
                row['sector_long'], row['speed_1']),
            axis=1
        )
        # crt_data = merged_data_filtered.copy()
        # crt_data['speed'] = crt_data['corrected_speed'].round(2)
        # ltc_data = crt_data[['Timestamp', 'speed']]

        merged_data_filtered = merged_data_filtered.merge(
            wd_sec_delta_df, left_on='sector_long', right_on='Sector', how='left'
        )

        return merged_data_filtered[['Timestamp', 'corrected_speed', 'WD SecDelta']]

    def without_noise(self, merged_data_filtered, merged_data, long_data, short_data):
        data1 = pd.DataFrame({
            'Timestamp': merged_data_filtered['Timestamp'],
            'direction_long': merged_data_filtered['direction_1'],
            'direction_short': merged_data_filtered['direction'],
            'speed_long': merged_data_filtered['speed_1'],
            'speed_short': merged_data_filtered['speed']
        })

        data1['sector_long'] = data1['direction_long'].apply(
            lambda x: self.assign_sector(x))
        data1['sector_short'] = data1['direction_short'].apply(
            lambda x: self.assign_sector(x))

        models = {}
        grouped = data1.groupby('sector_long')
        for sector, group in grouped:
            X = group[['speed_long']].values.reshape(-1, 1)
            y = group['speed_short'].values
            model = LinearRegression()
            model.fit(X, y)
            models[sector] = model

        def predict_corrected_speed(sector, speed_long):
            if sector in models:
                model = models[sector]
                return model.predict([[speed_long]])[0]
            else:
                return None

        long_data['sector_Long'] = long_data['direction'].apply(
            lambda x: self.assign_sector(x))
        long_data['corrected_speed'] = long_data.apply(
            lambda row: predict_corrected_speed(
                row['sector_Long'], row['speed']),
            axis=1
        )

        spd_data = pd.DataFrame()
        spd_data['Timestamp'] = long_data['Timestamp']
        spd_data['speed'] = long_data['corrected_speed'].round(2)

        final_data = pd.merge(merged_data, long_data[[
                              'Timestamp', 'corrected_speed']], on='Timestamp', how='inner')
        m_data = pd.merge(short_data, spd_data, on='Timestamp',
                          how='inner', suffixes=('_short', '_long'))

        return final_data, m_data, spd_data
