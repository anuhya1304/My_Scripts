# -*- coding: utf-8 -*-
"""
Created on Fri Oct  4 11:44:05 2024

@author: SaiAnuhyaKurra
"""
from sklearn.linear_model import LinearRegression
import pandas as pd


class AdaptionMain:
    def __init__(self, satellit_df_adap, resample_measured_df_hourly, common_df, mea_adap_col, sat_adap_col, data_type):
        self.satellit_df_adap = satellit_df_adap
        self.resample_measured_df_hourly = resample_measured_df_hourly
        self.common_df = common_df
        self.mea_adap_col = mea_adap_col
        self.sat_adap_col = sat_adap_col
        self.data_type = data_type  # Store the data type (e.g., 'GHI', 'DNI')

    def applyadaption_met1(self):
        grouped = self.common_df.groupby(self.common_df.index.month)

        # Initialize an empty list to store regression results
        regression_results = []

        if self.data_type == "Temp":
            intervals = [(x, x+3) for x in range(0, 50, 3)]
        else:
            # Define the intervals
            intervals = [(x, x + 50) for x in range(0, 1300, 50)]

        # Loop through each month and interval
        for month, data in grouped:
            for interval in intervals:
                # Perform linear regression for each interval
                X = data[data[self.sat_adap_col].between(
                    *interval)][[self.sat_adap_col]]
                y = data.loc[X.index, self.mea_adap_col]

                # Check if X is not empty
                if not X.empty:
                    intercept = False
                    if interval == (0, 50):
                        intercept = False

                    model = LinearRegression(fit_intercept=intercept)
                    model.fit(X, y)

                    # Get coefficient and intercept
                    coefficient = model.coef_[0]
                    intercept = model.intercept_

                    # Calculate R-squared value
                    r_squared = model.score(X, y)
                    # Append results to list
                    regression_results.append({
                        'Month': month,
                        'Interval_Start': interval[0],
                        'Interval_End': interval[1],
                        f'{self.data_type}_Coefficient': coefficient,
                        f'{self.data_type}_Intercept': intercept,
                        f'{self.data_type}_R2': r_squared
                    })

        regression_results_df = pd.DataFrame(regression_results)

        # Dynamically set the adapted column name
        adapted_col = f'{self.data_type.lower()}_adapted_1'
        self.satellit_df_adap[adapted_col] = self.satellit_df_adap[self.sat_adap_col]

        # Apply the regression results to adapt the data
        for month, data in grouped:
            for interval in intervals:
                coeff_intercept = regression_results_df[
                    (regression_results_df['Month'] == month) &
                    (regression_results_df['Interval_Start'] == interval[0]) &
                    (regression_results_df['Interval_End'] == interval[1])
                ]
                if not coeff_intercept.empty:
                    coefficient = coeff_intercept[f'{self.data_type}_Coefficient'].values[0]
                    intercept = coeff_intercept[f'{self.data_type}_Intercept'].values[0]

                    cond = (self.satellit_df_adap.index.month == month) & \
                           (interval[0] <= self.satellit_df_adap[self.sat_adap_col]) & \
                           (self.satellit_df_adap[self.sat_adap_col]
                            < interval[1])
                    self.satellit_df_adap.loc[cond,
                                              adapted_col] = self.satellit_df_adap[cond][self.sat_adap_col] * coefficient + intercept

        return regression_results_df, self.satellit_df_adap

    def applyadaption_met2(self):
        grouped = self.common_df.groupby(
            [self.common_df.index.month, self.common_df.index.hour])

        # Initialize an empty list to store regression results
        regression_results = []

        # Loop through each month and interval
        for (month, hour), data in grouped:
            # Perform linear regression for each interval
            X = data[[self.sat_adap_col]]
            y = data[[self.mea_adap_col]]

            # Check if X is not empty
            if not X.empty:
                model = LinearRegression(fit_intercept=False)
                model.fit(X, y)

                # Get coefficient and intercept
                coefficient = model.coef_[0]
                intercept = model.intercept_

                # Calculate R-squared value
                r_squared = model.score(X, y)

                # Append results to list
                regression_results.append({
                    'Month': month,
                    'Hour': hour,
                    f'{self.data_type}_Coefficient': coefficient,
                    f'{self.data_type}_Intercept': intercept,
                    f'{self.data_type}_R2': r_squared
                })

        regression_results_df = pd.DataFrame(regression_results)

        # Dynamically set the adapted column name
        adapted_col = f'{self.data_type.lower()}_adapted_2'
        self.satellit_df_adap[adapted_col] = self.satellit_df_adap[self.sat_adap_col]

        for (month, hour), data in grouped:
            coeff_intercept = regression_results_df[
                (regression_results_df['Month'] == month) &
                (regression_results_df['Hour'] == hour)
            ]
            if not coeff_intercept.empty:
                coefficient = coeff_intercept[f'{self.data_type}_Coefficient'].values[0]
                intercept = coeff_intercept[f'{self.data_type}_Intercept'].values[0]

                cond = (self.satellit_df_adap.index.month == month) & \
                       (self.satellit_df_adap.index.hour == hour)
                self.satellit_df_adap.loc[cond,
                                          adapted_col] = self.satellit_df_adap[cond][self.sat_adap_col] * coefficient + intercept

        return regression_results_df, self.satellit_df_adap
