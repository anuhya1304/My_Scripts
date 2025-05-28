# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 13:57:23 2025

@author: SaiAnuhyaKurra
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from ReadData import readdata

mast_file = r""
lidar_file = r""


def extract_height(s):
    """Extract height from column name (e.g., WS_100_45_Mean -> 100)."""
    return float(s.split("_")[1])


def extract_orientation(column_name):
    """Extract wind direction sensor orientation from column name (Assumption: orientation is numeric)."""
    return int(column_name.split("_")[2])  # Assuming orientation is at the end

def find_nearest_match(list1, list2):
    """Find nearest numerical match for each element in list1 from list2."""
    list2_numbers = {extract_height(s): s for s in list2}
    matches = {}

    for item in list1:
        num = extract_height(item)
        nearest_num = min(list2_numbers.keys(), key=lambda x: abs(x - num))
        matches[item] = list2_numbers[nearest_num]
    return matches


mast_data = readdata(mast_file)
lidar_data = readdata(lidar_file)

# sep_lidar_data = mast_data[lidar_data['Timestamp'] == '2024-09-01 00:00:00']
# sep_lidar_data.to_csv('sep_1stmonth_lidar.csv')
# Filtering Wind Speed and Wind Direction Columns
ws_mast_mean_cols = [
    x for x in mast_data.columns if "Mean" in x  and "cmb" not in x and "flags" not in x and  x.startswith("WS")]
wd_mast_mean_cols = [
    x for x in mast_data.columns if "Mean" in x  and "cmb" not in x and "flags" not in x and x.startswith("WD")]
ws_lidar_mean_cols = [
    x for x in lidar_data.columns if "Mean" in x and "flags" not in x and x.startswith("WS")]
wd_lidar_mean_cols = [
    x for x in lidar_data.columns if "Mean" in x and "flags" not in x and x.startswith("WD")]

# Find nearest matches
ws_matching_cols = find_nearest_match(ws_mast_mean_cols, ws_lidar_mean_cols)
m_ws_wd_matching_cols = find_nearest_match(
    ws_mast_mean_cols, wd_mast_mean_cols)
wd_matching_cols = find_nearest_match(wd_mast_mean_cols, wd_lidar_mean_cols)
l_ws_wd_matching_cols = find_nearest_match(
    ws_lidar_mean_cols, wd_lidar_mean_cols)


def apply_linear_regression(filtered_data, mast_col, lidar_col, mast_wd_col, ws_key):
    """Apply Linear Regression and calculate absolute differences & exceedance based on wind speed range keys."""

    if filtered_data.empty:
        print(f"No data available in the specified wind speed range ({ws_key}).")
        return None

    # Perform Linear Regression
    ws_mast_array = np.array(filtered_data[mast_col]).reshape(-1,1)
    ws_lidar_array =np.array( filtered_data[lidar_col])
    model = LinearRegression(fit_intercept=False) 
    model.fit(ws_mast_array, ws_lidar_array)
    slope = model.coef_[0]  # Should be close to 2
    intercept = model.intercept_  # Should be 0
    # Predict and compute R² score
    y_pred = model.predict(ws_mast_array)
    # Compute R² manually (Excel's approach)
    ss_total = np.sum(ws_lidar_array ** 2)  # Sum of squares total (Excel uses y instead of mean(y))
    ss_residual = np.sum((ws_lidar_array - y_pred) ** 2)  # Residual sum of squares
    r2 = 1 - (ss_residual / ss_total)
    # r2 = r2_score(ws_lidar_array, y_pred)
    # slope, intercept, r, p, std_err = stats.linregress(ws_mast_array, ws_lidar_array)

    # Calculate mean, differences, and exceedance percentage
    mean_ws_rsd = round(ws_lidar_array.mean(),3)
    mean_ws_mast = round(ws_mast_array.mean(),3)
    mean_difference = round(mean_ws_rsd - mean_ws_mast,3)
    rel_mean_diff = round((mean_difference / mean_ws_mast) * 100,3)

    height = extract_height(mast_col)
    abs_diff_col = f"Abs.diff_{height}"
    exceed_col = f"Exceeds_{height}"

    temp_df = pd.DataFrame({
        "Timestamp": filtered_data["Timestamp"],
        abs_diff_col: abs(filtered_data[mast_col] - filtered_data[lidar_col]),
        exceed_col: (abs(filtered_data[mast_col] - filtered_data[lidar_col]) > 0.5).astype(int),
    })

    exceedance_percentage = temp_df[exceed_col].mean() * 100

    return {
        "slope": slope, "intercept": intercept, "r_squared": r2,  
        "data_points": len(filtered_data), "mean_ws_rsd": mean_ws_rsd, "mean_ws_mast": mean_ws_mast,
        "mean_difference": mean_difference, "rel_mean_diff": rel_mean_diff, "abs_diff_df": temp_df,
        "exceedance_percentage": exceedance_percentage
    }

# Initialize variables
ws_key = ">=3"
data_points_list = []
summary_data_list = []
processed_availability_list = []
abs_diff_df = pd.DataFrame()
exceedence_data_list = []
data_points_dict = {"WS Range": ws_key}

# Define wind speed ranges
ws_ranges = {
    ">=3": (3, float('inf')),
    "3.75-16.25": (3.75, 16.25)
}
min_ws, max_ws = ws_ranges[ws_key]

# Loop through mast and lidar column pairs
for mast_col, lidar_col in ws_matching_cols.items():
    mast_wd_col = m_ws_wd_matching_cols[mast_col]
    lidar_wd_col = l_ws_wd_matching_cols[lidar_col]

    # Filter non-null values from mast and lidar data
    mast_data_filtered = mast_data[mast_data[mast_col].notna()][['Timestamp', mast_col, mast_wd_col]]
    lidar_data_filtered = lidar_data[lidar_data[lidar_col].notna()][['Timestamp', lidar_col, lidar_wd_col]]

    # Merge mast and lidar data
    combined_data = mast_data_filtered.merge(
        lidar_data_filtered, on="Timestamp", how="inner", suffixes=("_mast", "_lidar"))

    # Extract orientation details
    orientation = extract_orientation(mast_col)
    red_sen_orientation = (orientation - 180) % 360
    wd_min = (red_sen_orientation - 45) % 360
    wd_max = (red_sen_orientation + 45) % 360

    # Apply **single filtering** for both wind direction and wind speed
    filtered_combined_data = combined_data[
        ((combined_data[mast_wd_col] < wd_min) | (combined_data[mast_wd_col] > wd_max)) &  
        ((combined_data[mast_col] >= min_ws) & (combined_data[mast_col] <= max_ws))
    ]

    # Calculate processed availability
    processed_availability = lidar_data[lidar_data[lidar_col].notna()][lidar_col].count() / len(lidar_data[lidar_col]) * 100
    processed_availability_list.append(
        {"Measurement Level (m)": extract_height(mast_col), "PDA (%)": processed_availability})

    # Pass already filtered data to function
    results = apply_linear_regression(
        filtered_combined_data, mast_col, lidar_col, mast_wd_col, ws_key)

    if results:
        height = extract_height(mast_col)
        data_points_dict[height] = results["data_points"]
        summary_data_list.append({
            "WS Range": ws_key, "Height (m)": height,
            "Concurrent Data Points": results["data_points"], "Slope (Y)": results["slope"],
            "Corr. Coefficient (R²)": results["r_squared"], "Mean WS_RSD": results["mean_ws_rsd"],
            "Mean WS_Mast": results["mean_ws_mast"], "Mean Difference": results["mean_difference"],
            "Rel. Mean Difference (%)": results["rel_mean_diff"]
        })

summary_df = pd.DataFrame(summary_data_list)


mean_cols = [col for col in lidar_data.columns if "Mean" in col]
total_rows = len(lidar_data)
fully_null_rows = lidar_data[mean_cols].isnull().all(axis=1).sum()
system_availability = ((total_rows - fully_null_rows) / total_rows) * 100

system_availability_df = pd.DataFrame({
    "Start Date": [lidar_data["Timestamp"].min()],
    "End Date": [lidar_data["Timestamp"].max()],
    "Months": [(lidar_data["Timestamp"].max() - lidar_data["Timestamp"].min()).days / 30.0],
    "System Availability (%)": [system_availability]
})
