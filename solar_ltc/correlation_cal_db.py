# without_loop
import pandas as pd
import numpy as np


class AllMBECalc:
    def __init__(self, common_df, mea_ghi_col, data_type, mea_dni_col=None):
        self.common_df = common_df
        self.mea_ghi_col = mea_ghi_col
        self.mea_dni_col = mea_dni_col  # Optional, only used if DNI is selected
        self.data_type = data_type

    def calculate_mbe(self, actual, predicted):
        return (actual - predicted).mean()

    def calculate_mbe_percent(self, actual, predicted):
        mbe = self.calculate_mbe(actual, predicted)
        mean_actual = actual.mean()
        return mbe * 100 / mean_actual

    def calc_mbe(self, selected_data_types=['GHI', 'DNI', 'Temp']):
        # Overall MBE Calculation
        self.mbe_results_overall_list = []
        results = {'Overall': 'Overall'}

        # Handling GHI data type
        if 'GHI' in selected_data_types:
            results.update(self._calc_mbe_for_type('GHI', self.mea_ghi_col, [
                           'GHI', 'ghi_adapted_1', 'ghi_adapted_2']))

        # Handling DNI data type
        if 'DNI' in selected_data_types and self.mea_dni_col is not None:
            results.update(self._calc_mbe_for_type('DNI', self.mea_dni_col, [
                           'DNI', 'dni_adapted_1', 'dni_adapted_2']))

        # Handling Temp data type
        if 'Temp' in selected_data_types and self.mea_dni_col is not None:
            results.update(self._calc_mbe_for_type('Temp', self.mea_dni_col, [
                           'Temp', 'temp_adapted_1', 'temp_adapted_2']))

        self.mbe_results_overall_list.append(results)
        self.mbe_results_overall = pd.DataFrame(self.mbe_results_overall_list)

        # Hourly, Monthly, and Percentage calculations
        self.mbe_results_hourly = self.calculate_time_based_mbe(
            selected_data_types, 'hour')
        self.mbe_results_monthly = self.calculate_time_based_mbe(
            selected_data_types, 'month')
        self.mbe_results_overall_per = self.calculate_mbe_percentages(
            selected_data_types, overall=True)
        self.mbe_results_hourly_per = self.calculate_mbe_percentages(
            selected_data_types, hourly=True)
        self.mbe_results_monthly_per = self.calculate_mbe_percentages(
            selected_data_types, monthly=True)

        return (self.mbe_results_overall, self.mbe_results_hourly,
                self.mbe_results_monthly, self.mbe_results_overall_per,
                self.mbe_results_hourly_per, self.mbe_results_monthly_per)

    def _calc_mbe_for_type(self, data_type, mea_col, adapted_cols):
        # Helper function to calculate MBE for a specific data type
        mbe_dict = {f'MBE_{data_type}': self.calculate_mbe(
            self.common_df[mea_col], self.common_df[adapted_cols[0]])}
        mbe_dict[f'MBE_{data_type}_Adapted'] = self.calculate_mbe(
            self.common_df[mea_col], self.common_df[adapted_cols[1]])
        mbe_dict[f'MBE_{data_type}_Adapted2'] = self.calculate_mbe(
            self.common_df[mea_col], self.common_df[adapted_cols[2]])
        return mbe_dict

    def calculate_time_based_mbe(self, selected_data_types, time_period):
        # Calculate MBE based on a time period (hourly or monthly)
        group = self.common_df.groupby(
            getattr(self.common_df.index, time_period))
        mbe_results = []

        for period, subset in group:
            period_result = {time_period.capitalize(): period}
            for data_type in selected_data_types:
                if data_type == 'GHI' and self.mea_ghi_col is not None:
                    period_result[f'MBE_{data_type}'] = self.calculate_mbe(
                        subset[self.mea_ghi_col], subset[data_type])
                elif data_type == 'DNI' and self.mea_dni_col is not None:
                    period_result[f'MBE_{data_type}'] = self.calculate_mbe(
                        subset[self.mea_dni_col], subset[data_type])
                elif data_type == 'Temp' and self.mea_dni_col is not None:
                    period_result[f'MBE_{data_type}'] = self.calculate_mbe(
                        subset[self.mea_dni_col], subset[data_type])
            mbe_results.append(period_result)

        return pd.DataFrame(mbe_results)

    def calculate_mbe_percentages(self, selected_data_types, overall=False, hourly=False, monthly=False):
        # Calculate MBE percentages for different time periods
        results = []
        if overall:
            result = {'Overall': 'Overall'}
            for data_type in selected_data_types:
                if data_type == 'GHI' and self.mea_ghi_col is not None:
                    result.update(self._calc_mbe_percent_for_type(data_type, self.mea_ghi_col, [
                                  data_type, f'{data_type.lower()}_adapted_1', f'{data_type.lower()}_adapted_2']))
                elif data_type == 'DNI' and self.mea_dni_col is not None:
                    result.update(self._calc_mbe_percent_for_type(data_type, self.mea_dni_col, [
                                  data_type, f'{data_type.lower()}_adapted_1', f'{data_type.lower()}_adapted_2']))
                elif data_type == 'Temp' and self.mea_dni_col is not None:
                    result.update(self._calc_mbe_percent_for_type(data_type, self.mea_dni_col, [
                                  data_type, f'{data_type.lower()}_adapted_1', f'{data_type.lower()}_adapted_2']))
            results.append(result)

        elif hourly or monthly:
            time_period = 'hour' if hourly else 'month'
            group = self.common_df.groupby(
                getattr(self.common_df.index, time_period))

            for period, subset in group:
                period_result = {time_period.capitalize(): period}
                for data_type in selected_data_types:
                    if data_type == 'GHI' and self.mea_ghi_col is not None:
                        period_result[f'MBE_{data_type}%'] = self.calculate_mbe_percent(
                            subset[self.mea_ghi_col], subset[data_type])
                    elif data_type == 'DNI' and self.mea_dni_col is not None:
                        period_result[f'MBE_{data_type}%'] = self.calculate_mbe_percent(
                            subset[self.mea_dni_col], subset[data_type])
                    elif data_type == 'Temp' and self.mea_dni_col is not None:
                        period_result[f'MBE_{data_type}%'] = self.calculate_mbe_percent(
                            subset[self.mea_dni_col], subset[data_type])
                results.append(period_result)

        return pd.DataFrame(results)

    def _calc_mbe_percent_for_type(self, data_type, mea_col, adapted_cols):
        # Helper function to calculate MBE percentages for a specific data type
        mbe_dict = {f'MBE_{data_type}%': self.calculate_mbe_percent(
            self.common_df[mea_col], self.common_df[adapted_cols[0]])}
        mbe_dict[f'MBE_{data_type}_Adapted%'] = self.calculate_mbe_percent(
            self.common_df[mea_col], self.common_df[adapted_cols[1]])
        mbe_dict[f'MBE_{data_type}_Adapted2%'] = self.calculate_mbe_percent(
            self.common_df[mea_col], self.common_df[adapted_cols[2]])
        return mbe_dict


# %%
# #with_for_loop
# import pandas as pd
# class CorrelationCalcAll:
#     def __init__(self, common_df, mea_cols):
#         self.common_df = common_df
#         self.mea_cols = mea_cols  # Dictionary of measurement columns

#     def cal_corr(self, selected_data_types):
#         correlation_results = []

#         overall_result = {}
#         for data_type in selected_data_types:
#             # Get the corresponding measured column
#             mea_col = self.mea_cols.get(data_type)
#             if mea_col in self.common_df.columns:
#                 overall_result[f'Correlation_{data_type}'] = self.common_df[mea_col].corr(
#                     self.common_df[data_type])
#                 overall_result[f'Correlation_{data_type}_Adapted_1'] = self.common_df[mea_col].corr(
#                     self.common_df.get(
#                         f'{data_type}_Adapted_1', pd.Series(dtype='float'))
#                 )
#                 overall_result[f'Correlation_{data_type}_Adapted_2'] = self.common_df[mea_col].corr(
#                     self.common_df.get(
#                         f'{data_type}_Adapted_2', pd.Series(dtype='float'))
#                 )
#         correlation_results.append(pd.DataFrame([overall_result]))
#         self.correlation_results_overall = pd.concat(
#             correlation_results, ignore_index=True)

#         # Calculate hourly and monthly correlations
#         self.correlation_results_hourly = self.calculate_hourly_correlations(
#             selected_data_types)
#         self.correlation_results_monthly = self.calculate_monthly_correlations(
#             selected_data_types)

#         return self.correlation_results_overall, self.correlation_results_hourly, self.correlation_results_monthly

#     def calculate_hourly_correlations(self, selected_data_types):
#         grouped_by_hour = self.common_df.groupby(self.common_df.index.hour)
#         correlation_results = []

#         for hour, group in grouped_by_hour:
#             result = {'Hour': hour}
#             for data_type in selected_data_types:
#                 mea_col = self.mea_cols.get(data_type)
#                 if mea_col is not None:
#                     result.update({
#                         f'Correlation_{data_type}': group[mea_col].corr(group.get(data_type, pd.Series(dtype='float'))),
#                         f'Correlation_{data_type}_Adapted_1': group[mea_col].corr(group.get(f'{data_type.lower()}_adapted_1', pd.Series(dtype='float'))),
#                         f'Correlation_{data_type}_Adapted_2': group[mea_col].corr(group.get(f'{data_type.lower()}_adapted_2', pd.Series(dtype='float')))
#                     })
#                 # if mea_col in group.columns:
#                 #     result[f'Correlation_{data_type}'] = group[mea_col].corr(
#                 #         group.get(data_type, pd.Series(dtype='float')))
#                 #     result[f'Correlation_{data_type}_Adapted_1'] = group[mea_col].corr(
#                 #         group.get(f'{data_type}_Adapted_1', pd.Series(dtype='float')))
#                 #     result[f'Correlation_{data_type}_Adapted_2'] = group[mea_col].corr(
#                 #         group.get(f'{data_type}_Adapted_2', pd.Series(dtype='float')))
#             correlation_results.append(result)

#         return pd.DataFrame(correlation_results)

#     def calculate_monthly_correlations(self, selected_data_types):
#         grouped_by_month = self.common_df.groupby(self.common_df.index.month)
#         correlation_results = []

#         for month, group in grouped_by_month:
#             result = {'Month': month}
#             for data_type in selected_data_types:
#                 mea_col = self.mea_cols.get(data_type)
#                 if mea_col is not None:
#                     result.update({
#                         f'Correlation_{data_type}': group[mea_col].corr(group.get(data_type, pd.Series(dtype='float'))),
#                         f'Correlation_{data_type}_Adapted_1': group[mea_col].corr(group.get(f'{data_type.lower()}_adapted_1', pd.Series(dtype='float'))),
#                         f'Correlation_{data_type}_Adapted_2': group[mea_col].corr(group.get(f'{data_type.lower()}_adapted_2', pd.Series(dtype='float')))
#                     })
#                 # if mea_col in group.columns:
#                     # result[f'Correlation_{data_type}'] = group[mea_col].corr(
#                     #     group.get(data_type, pd.Series(dtype='float')))
#                     # result[f'Correlation_{data_type}_Adapted_1'] = group[mea_col].corr(
#                     #     group.get(f'{data_type}_Adapted_1', pd.Series(dtype='float')))
#                     # result[f'Correlation_{data_type}_Adapted_2'] = group[mea_col].corr(
#                     #     group.get(f'{data_type}_Adapted_2', pd.Series(dtype='float')))
#             correlation_results.append(result)

#         return pd.DataFrame(correlation_results)


# Why the for loop is important:
# Handling Multiple Data Types: In your code, the selected_data_types list determines which data types to calculate MBE for. The loop iterates over this list and applies the MBE calculation for each data type (like GHI, DNI, or Temp).

# Ensuring Modular Calculations: Each data type may have different columns (e.g., mea_ghi_col, mea_dni_col), and the logic inside the loop handles each data type’s specific columns correctly. Without a loop, the code would need to handle each data type separately and explicitly, which would lead to repetitive code.

# Dynamic Handling of New Data Types: The for loop makes the code more flexible. If in the future you want to add a new data type (like SolarRad), you would only need to add it to the selected_data_types list without modifying the core logic.
