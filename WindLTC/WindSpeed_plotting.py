import numpy as np

from scipy.stats import gaussian_kde

#plotting windspeed data
def compute_graph_data(merged_data, m_data):
    # KDE for measured and predicted
    measured_speeds = merged_data['speed_short']
    predicted_speeds = merged_data['speed_long']
    predicted_speeds_without = m_data['speed_long']

    kde_measured = gaussian_kde(measured_speeds)
    kde_predicted = gaussian_kde(predicted_speeds)
    kde_predicted_without = gaussian_kde(predicted_speeds_without)

    wind_speed_range = np.linspace(
        0, max(measured_speeds.max(), predicted_speeds.max()), 100)
    wind_speed_range_without = np.linspace(
        0, max(measured_speeds.max(), predicted_speeds_without.max()), 100)

    measured_density = kde_measured(wind_speed_range)
    predicted_density = kde_predicted(wind_speed_range)
    predicted_density_without = kde_predicted_without(wind_speed_range_without)

    # Sector boundaries and labels
    sector_boundaries = [15, 45, 75, 105, 135,
                         165, 195, 225, 255, 285, 315, 345, 15]
    sector_labels = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 0]

    def assign_sector(direction):
        for i in range(len(sector_boundaries) - 1):
            if sector_boundaries[i] <= direction < sector_boundaries[i + 1]:
                return sector_labels[i]
        return sector_labels[-1]

    merged_data['sector_long'] = merged_data['direction_long'].apply(
        assign_sector)
    merged_data['sector_short'] = merged_data['direction_short'].apply(
        assign_sector)

    sector_pct_long = merged_data['sector_long'].value_counts(
        normalize=True) * 100
    sector_pct_short = merged_data['sector_short'].value_counts(
        normalize=True) * 100

    # Grouping for hourly and monthly analysis
    hourly_data = merged_data.groupby(merged_data['Timestamp'].dt.hour).mean()
    monthly_data = merged_data.groupby(
        merged_data['Timestamp'].dt.month).mean()

    return {
        "hourly_data": hourly_data,
        "monthly_data": monthly_data,
        "wind_speed_range": wind_speed_range,
        "measured_density": measured_density,
        "predicted_density": predicted_density,
        "wind_speed_range_without": wind_speed_range_without,
        "predicted_density_without": predicted_density_without,
        "sector_pct_long": sector_pct_long,
        "sector_pct_short": sector_pct_short,
    }
