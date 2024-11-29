import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error


def uncertainity_calc(merged_data_filtered, short_data, long_data, ltc_data, final_data, bin_sizes=None):
    Local_mean = short_data['speed'].mean().round(2)
    Local_mean_con = merged_data_filtered['speed'].mean().round(2)
    Reference_mean = long_data['speed'].mean().round(2)
    Reference_mean_con = merged_data_filtered['speed_1'].mean().round(2)
    Predicted_mean = ltc_data['speed'].mean().round(2)

    correlation_speed = final_data['speed_1'].corr(
        final_data['speed']).round(3)

    # UNCERTAINITY CALCULATION:
    wind_index = ((Reference_mean_con/Reference_mean)*100).round(3)

    long_data['Timestamp'] = pd.to_datetime(
        long_data['Timestamp'], dayfirst=True)
    # Extract the year and month from the timestamp
    long_data['year'] = long_data['Timestamp'].dt.year
    long_data['month'] = long_data['Timestamp'].dt.month

    # Group by year and count the unique months for each year
    months_per_year = long_data.groupby('year')['month'].nunique()

    # Filter for years that have 6 or more unique months
    valid_years = months_per_year[months_per_year >= 6].index

    # Filter the original DataFrame to include only data from valid years
    filtered_data = long_data[long_data['year'].isin(valid_years)]

    data = filtered_data
    # Create a DataFrame
    df = pd.DataFrame(data)
    # Convert the Timestamp column to datetime format
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d-%m-%Y %H:%M')
    # Extract year from the Timestamp
    df['Year'] = df['Timestamp'].dt.year
    # Group by year and calculate the average speed for each year
    yearly_avg_speed = df.groupby('Year')['speed'].mean().reset_index()
    # Calculate the overall mean and standard deviation of the yearly averages
    mean_of_yearly_avg = yearly_avg_speed['speed'].mean()
    std_dev_of_yearly_avg = yearly_avg_speed['speed'].std()
    variability = ((std_dev_of_yearly_avg/mean_of_yearly_avg)*100).round(3)

    merged_data_filter_copy = merged_data_filtered.copy()
    merged_data_filter_copy = merged_data_filter_copy.dropna()
    merged_data_filter_copy.set_index('Timestamp', inplace=True)
    # Resample the merged data to monthly frequency, taking the mean of each month
    monthly_data = merged_data_filter_copy.resample('M').mean()
    monthly_data.reset_index(inplace=True)
    # Extract the relevant columns
    predicted = monthly_data['speed_1']
    actual = monthly_data['speed']
    # errors
    mean_actual = np.mean(actual)
    # 1. Mean Bias Error (MBE)
    mbe = np.mean(predicted - actual)
    mbe_percentage = (mbe / mean_actual) * 100

    # 2. Mean Absolute Error (MAE)
    mae = np.mean(np.abs(predicted - actual))
    mae_percentage = (mae / mean_actual) * 100

    # 3. Root Mean Squared Error (RMSE)
    rmse = np.sqrt(np.mean((predicted - actual) ** 2))
    rmse_percentage = (rmse / mean_actual) * 100

    # 4. Correlation Coefficient (R value)
    correlation = np.corrcoef(actual, predicted)[0, 1]

    metrics = {
        "Metric": [
            "Local_mean[m/s]",
            "Local_mean_con[m/s]",
            "Reference_mean[m/s]",
            "Reference_mean_con[m/s]",
            "Variability(V)",
            "Predicted_mean[m/s]",
            "Correlation (speed), r",
            "Wind_index (WI)%",
            "Mean Bias Error (MBE) %",
            "Mean Absolute Error (MAE) %",
            "Root Mean Squared Error (RMSE) %",
            "Correlation (predicted vs actual), r",
        ],
        "Value": [
            f"{Local_mean:.2f}",
            f"{Local_mean_con:.2f}",
            f"{Reference_mean:.2f}",
            f"{Reference_mean_con:.2f}",
            f"{variability}",
            f"{Predicted_mean:.2f}",
            f"{correlation_speed:.3f}",  # Keep 3 decimals for correlation
            f"{wind_index:.3f}",
            f"{mbe_percentage:.2f}",
            f"{mae_percentage:.2f}",
            f"{rmse_percentage:.2f}",
            f"{correlation:.2f}",
        ],
    }

    summary_var_data = pd.DataFrame(metrics)
    if bin_sizes:
        ks_statistics = []
        for bin_size in bin_sizes:
            bins = np.arange(0, 32 + bin_size, bin_size)
            speed_counts = pd.cut(
                merged_data_filter_copy['speed'], bins=bins, right=False).value_counts().sort_index()
            cumulative_freq_short = speed_counts.cumsum()
            corrected_speed_counts = pd.cut(
                merged_data_filtered['speed_1'], bins=bins, right=False).value_counts().sort_index()
            cumulative_freq_long = corrected_speed_counts.cumsum()

            total_counts = len(merged_data_filtered)
            cumulative_freq_short_percentage = (
                cumulative_freq_short / total_counts) * 100
            cumulative_freq_long_percentage = (
                cumulative_freq_long / total_counts) * 100

            absolute_difference = (
                cumulative_freq_short_percentage - cumulative_freq_long_percentage).abs()
            ks_statistic = absolute_difference.max().round(2)

            ks_statistics.append(
                {"Bin Size": bin_size, "KS Statistic": ks_statistic})

        ks_statistics_df = pd.DataFrame(ks_statistics)
    else:
        ks_statistics_df = pd.DataFrame()

    return summary_var_data, ks_statistics_df
