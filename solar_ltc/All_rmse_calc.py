# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 16:40:26 2024

@author: SaiAnuhyaKurra
"""
import pandas as pd
import numpy as np


class AllRMSECalc:
    def __init__(self, common_df, mea_cols):
        self.common_df = common_df
        # Dictionary to hold measurement columns for each data type, e.g., {'GHI': 'measured_ghi_col', 'DNI': 'measured_dni_col'}
        self.mea_cols = mea_cols

    def calculate_rmse(self, actual, predicted):
        return np.sqrt(((actual - predicted) ** 2).mean())

    def calculate_nrmse_percent(self, actual, predicted):
        rmse = self.calculate_rmse(actual, predicted)
        mean_actual = actual.mean()
        return rmse * 100 / mean_actual if mean_actual != 0 else np.nan

    def calc_rmse(self, selected_data_types=['GHI', 'DNI', 'Temp']):
        # Overall RMSE Calculation
        rmse_results_overall = []

        for data_type in selected_data_types:
            if data_type in self.mea_cols:
                mea_col = self.mea_cols[data_type]
                rmse_result = {
                    f'RMSE_{data_type}': self.calculate_rmse(self.common_df[mea_col], self.common_df[data_type]),
                    f'RMSE_{data_type}_Adapted': self.calculate_rmse(self.common_df[mea_col], self.common_df[f'{data_type.lower()}_adapted_1']),
                    f'RMSE_{data_type}_Adapted_2': self.calculate_rmse(self.common_df[mea_col], self.common_df[f'{data_type.lower()}_adapted_2'])
                }
                rmse_results_overall.append(rmse_result)

        # Convert the list of dictionaries to a DataFrame for overall RMSE results
        self.rmse_results_overall = pd.DataFrame(rmse_results_overall)

        # Hourly RMSE Calculation
        self.rmse_results_hourly = self.calculate_hourly_rmse(
            selected_data_types)
        self.rmse_results_hourly.loc['avg'] = self.rmse_results_hourly.mean()

        # Monthly RMSE Calculation
        self.rmse_results_monthly = self.calculate_monthly_rmse(
            selected_data_types)
        self.rmse_results_monthly.loc['avg'] = self.rmse_results_monthly.mean()

        # Overall RMSE Percentage Calculation
        self.rmse_results_overall_per = self.calculate_rmse_percentages(
            selected_data_types, overall=True)

        # Hourly RMSE Percentage Calculation
        self.rmse_results_hourly_per = self.calculate_rmse_percentages(
            selected_data_types, hourly=True)

        # Monthly RMSE Percentage Calculation
        self.rmse_results_monthly_per = self.calculate_rmse_percentages(
            selected_data_types, monthly=True)

        return self.rmse_results_overall, self.rmse_results_hourly, self.rmse_results_monthly, \
            self.rmse_results_overall_per, self.rmse_results_hourly_per, self.rmse_results_monthly_per

    def calculate_hourly_rmse(self, selected_data_types):
        grouped_by_hour = self.common_df.groupby(self.common_df.index.hour)
        rmse_results_hourly = []

        for hour, group in grouped_by_hour:
            result = {'Hour': hour}
            for data_type in selected_data_types:
                if data_type in self.mea_cols:
                    mea_col = self.mea_cols[data_type]
                    result.update({
                        f'RMSE_{data_type}': self.calculate_rmse(group[mea_col], group[data_type]),
                        f'RMSE_{data_type}_Adapted': self.calculate_rmse(group[mea_col], group[f'{data_type.lower()}_adapted_1']),
                        f'RMSE_{data_type}_Adapted_2': self.calculate_rmse(group[mea_col], group[f'{data_type.lower()}_adapted_2'])
                    })
            rmse_results_hourly.append(result)

        return pd.DataFrame(rmse_results_hourly)

    def calculate_monthly_rmse(self, selected_data_types):
        grouped_by_month = self.common_df.groupby(self.common_df.index.month)
        rmse_results_monthly = []

        for month, group in grouped_by_month:
            result = {'Month': month}
            for data_type in selected_data_types:
                if data_type in self.mea_cols:
                    mea_col = self.mea_cols[data_type]
                    result.update({
                        f'RMSE_{data_type}': self.calculate_rmse(group[mea_col], group[data_type]),
                        f'RMSE_{data_type}_Adapted': self.calculate_rmse(group[mea_col], group[f'{data_type.lower()}_adapted_1']),
                        f'RMSE_{data_type}_Adapted_2': self.calculate_rmse(group[mea_col], group[f'{data_type.lower()}_adapted_2'])
                    })
            rmse_results_monthly.append(result)

        return pd.DataFrame(rmse_results_monthly)

    def calculate_rmse_percentages(self, selected_data_types, overall=False, hourly=False, monthly=False):
        if overall:
            rmse_percent_results = []

            for data_type in selected_data_types:
                if data_type in self.mea_cols:
                    mea_col = self.mea_cols[data_type]
                    rmse_percent_result = {
                        f'RMSE_{data_type}%': self.calculate_nrmse_percent(self.common_df[mea_col], self.common_df[data_type]),
                        f'RMSE_{data_type}_Adapted%': self.calculate_nrmse_percent(self.common_df[mea_col], self.common_df[f'{data_type.lower()}_adapted_1']),
                        f'RMSE_{data_type}_Adapted_2%': self.calculate_nrmse_percent(self.common_df[mea_col], self.common_df[f'{data_type.lower()}_adapted_2'])
                    }
                    rmse_percent_results.append(rmse_percent_result)

            return pd.DataFrame(rmse_percent_results)

        elif hourly:
            grouped_by_hour = self.common_df.groupby(self.common_df.index.hour)
            rmse_percent_results_hourly = []

            for hour, group in grouped_by_hour:
                result = {'Hour': hour}
                for data_type in selected_data_types:
                    if data_type in self.mea_cols:
                        mea_col = self.mea_cols[data_type]
                        result.update({
                            f'RMSE_{data_type}%': self.calculate_nrmse_percent(group[mea_col], group[data_type]),
                            f'RMSE_{data_type}_Adapted%': self.calculate_nrmse_percent(group[mea_col], group[f'{data_type.lower()}_adapted_1']),
                            f'RMSE_{data_type}_Adapted_2%': self.calculate_nrmse_percent(group[mea_col], group[f'{data_type.lower()}_adapted_2'])
                        })
                rmse_percent_results_hourly.append(result)

            return pd.DataFrame(rmse_percent_results_hourly)

        elif monthly:
            grouped_by_month = self.common_df.groupby(
                self.common_df.index.month)
            rmse_percent_results_monthly = []

            for month, group in grouped_by_month:
                result = {'Month': month}
                for data_type in selected_data_types:
                    if data_type in self.mea_cols:
                        mea_col = self.mea_cols[data_type]
                        result.update({
                            f'RMSE_{data_type}%': self.calculate_nrmse_percent(group[mea_col], group[data_type]),
                            f'RMSE_{data_type}_Adapted%': self.calculate_nrmse_percent(group[mea_col], group[f'{data_type.lower()}_adapted_1']),
                            f'RMSE_{data_type}_Adapted_2%': self.calculate_nrmse_percent(group[mea_col], group[f'{data_type.lower()}_adapted_2'])
                        })
                rmse_percent_results_monthly.append(result)

            return pd.DataFrame(rmse_percent_results_monthly)

# import pandas as pd
# import numpy as np


# class AllRMSECalc():
#     def __init__(self, common_df, mea_ghi_col, mea_dni_col=None):
#         self.common_df = common_df
#         self.mea_ghi_col = mea_ghi_col
#         self.mea_dni_col = mea_dni_col

#     def calculate_rmse(self, actual, predicted):
#         return np.sqrt(((actual - predicted) ** 2).mean())

#     def calculate_nrmse_percent(self, actual, predicted):
#         rmse = self.calculate_rmse(actual, predicted)
#         mean_actual = actual.mean()
#         return rmse*100 / mean_actual

#     def calc_rmse(self, selected_data_types=['GHI', 'DNI']):
#         # =============================================================================
#         #           Overall MBE Calculation
#         # =============================================================================

#         self.rmse_results_overall_list = []

#         if 'GHI' in selected_data_types:
#             rmse_ghi = self.calculate_rmse(
#                 self.common_df[self.mea_ghi_col], self.common_df['GHI'])
#             rmse_ghi_adapted = self.calculate_rmse(
#                 self.common_df[self.mea_ghi_col], self.common_df['ghi_adapted_1'])
#             rmse_ghi_adapted2 = self.calculate_rmse(
#                 self.common_df[self.mea_ghi_col], self.common_df['ghi_adapted_2'])

#             # self.mbe_results_overall_list.append({
#             #     'Overall': 'Overall',
#             #     'MBE_GHI': mbe_ghi,
#             #     'MBE_GHI_Adapted': mbe_ghi_adapted,
#             #     'MBE_GHI_Adapted2': mbe_ghi_adapted2
#             # })

#         if 'DNI' in selected_data_types:
#             rmse_dni = self.calculate_rmse(
#                 self.common_df[self.mea_ghi_col], self.common_df['DNI'])
#             rmse_dni_adapted = self.calculate_rmse(
#                 self.common_df[self.mea_ghi_col], self.common_df['dni_adapted_1'])
#             rmse_dni_adapted2 = self.calculate_rmse(
#                 self.common_df[self.mea_ghi_col], self.common_df['dni_adapted_2'])

#             # self.mbe_results_overall_list.append({
#             #     'Overall': 'Overall',
#             #     'MBE_DNI': mbe_dni,
#             #     'MBE_DNI_Adapted': mbe_dni_adapted,
#             #     'MBE_DNI_Adapted2': mbe_dni_adapted2
#             # })
#         self.rmse_results_overall_list.append({
#             'Overall': 'Overall',
#             'RMSE_GHI': rmse_ghi,
#             'RMSE_GHI_Adapted': rmse_ghi_adapted,
#             'RMSE_GHI_Adapted2': rmse_ghi_adapted2,

#             'RMSE_DNI': rmse_dni,
#             'RMSE_DNI_Adapted': rmse_dni_adapted,
#             'RMSE_DNI_Adapted2': rmse_dni_adapted2
#         })

#         self.rmse_results_overall = pd.DataFrame(
#             self.rmse_results_overall_list)

#         # =============================================================================
#         #           Hourly RMSE Calculation
#         # =============================================================================

#         self.rmse_results_hourly = self.calculate_hourly_rmse(
#             selected_data_types)

#         # =============================================================================
#         #           Monthly RMSE Calculation
#         # =============================================================================

#         self.rmse_results_monthly = self.calculate_monthly_rmse(
#             selected_data_types)

#         # =============================================================================
#         #           Overall RMSE Percentage Calculation
#         # =============================================================================

#         self.rmse_results_overall_per = self.calculate_rmse_percentages(
#             selected_data_types, overall=True)

#         # =============================================================================
#         #           Hourly RMSE Percentage Calculation
#         # =============================================================================

#         self.rmse_results_hourly_per = self.calculate_rmse_percentages(
#             selected_data_types, hourly=True)

#         # =============================================================================
#         #           Monthly RMSE Percentage Calculation
#         # =============================================================================

#         self.rmse_results_monthly_per = self.calculate_rmse_percentages(
#             selected_data_types, monthly=True)

#         return self.rmse_results_overall, self.rmse_results_hourly, self.rmse_results_monthly, \
#             self.rmse_results_overall_per, self.rmse_results_hourly_per, self.rmse_results_monthly_per

#     def calculate_hourly_rmse(self, selected_data_types):
#         grouped_by_hour = self.common_df.groupby(self.common_df.index.hour)
#         mbe_results = []

#         for hour, group in grouped_by_hour:
#             results = {'Hour': hour}
#             if 'GHI' in selected_data_types:
#                 results.update({'RMSE_GHI': self.calculate_rmse(
#                     group[self.mea_ghi_col], group['GHI'])})

#             if 'DNI' in selected_data_types:
#                 results.update({'RMSE_DNI': self.calculate_rmse(
#                     group[self.mea_ghi_col], group['DNI'])})
#             mbe_results.append(results)

#         return pd.DataFrame(mbe_results)

#     def calculate_monthly_rmse(self, selected_data_types):
#         grouped_by_month = self.common_df.groupby(self.common_df.index.month)
#         mbe_results = []

#         for month, group in grouped_by_month:
#             results = {'Month': month}
#             if 'GHI' in selected_data_types:
#                 results.update({'RMSE_GHI': self.calculate_rmse(
#                     group[self.mea_dni_col], group['GHI'])})

#             if 'DNI' in selected_data_types:
#                 results.update({'RMSE_DNI': self.calculate_rmse(
#                     group[self.mea_dni_col], group['DNI'])})
#             mbe_results.append(results)

#         return pd.DataFrame(mbe_results)

#     def calculate_rmse_percentages(self, selected_data_types, overall=False, hourly=False, monthly=False):
#         if overall:
#             rmse_percent_results = []
#             if 'GHI' in selected_data_types:
#                 rmse_ghi_percent = self.calculate_nrmse_percent(
#                     self.common_df[self.mea_ghi_col], self.common_df['GHI'])
#                 rmse_ghi_adapted_percent = self.calculate_nrmse_percent(
#                     self.common_df[self.mea_ghi_col], self.common_df['ghi_adapted_1'])
#                 rmse_ghi_adapted2_percent = self.calculate_nrmse_percent(
#                     self.common_df[self.mea_ghi_col], self.common_df['ghi_adapted_2'])

#                 # mbe_percent_results.append({
#                 #     'Overall': 'Overall',
#                 #     'MBE_GHI%': mbe_ghi_percent,
#                 #     'MBE_GHI_Adapted%': mbe_ghi_adapted_percent,
#                 #     'MBE_GHI_Adapted2%': mbe_ghi_adapted2_percent
#                 # })

#             if 'DNI' in selected_data_types:
#                 rmse_dni_percent = self.calculate_nrmse_percent(
#                     self.common_df[self.mea_dni_col], self.common_df['DNI'])
#                 rmse_dni_adapted_percent = self.calculate_nrmse_percent(
#                     self.common_df[self.mea_dni_col], self.common_df['dni_adapted_1'])
#                 rmse_dni_adapted2_percent = self.calculate_nrmse_percent(
#                     self.common_df[self.mea_dni_col], self.common_df['dni_adapted_2'])

#                 # mbe_percent_results.append({
#                 #     'Overall': 'Overall',
#                 #     'MBE_DNI%': mbe_dni_percent,
#                 #     'MBE_DNI_Adapted%': mbe_dni_adapted_percent,
#                 #     'MBE_DNI_Adapted2%': mbe_dni_adapted2_percent
#                 # })
#             rmse_percent_results.append({
#                 'Overall': 'Overall',
#                 'RMSE_GHI%': rmse_ghi_percent,
#                 'RMSE_GHI_Adapted%': rmse_ghi_adapted_percent,
#                 'RMSE_GHI_Adapted2%': rmse_ghi_adapted2_percent,

#                 'RMSE_DNI %': rmse_dni_percent,
#                 'RMSE_DNI_Adapted%': rmse_dni_adapted_percent,
#                 'RMSE_DNI_Adapted2%': rmse_dni_adapted2_percent
#             })

#             return pd.DataFrame(rmse_percent_results)

#         elif hourly:
#             grouped_by_hour = self.common_df.groupby(self.common_df.index.hour)
#             rmse_percent_results = []

#             for hour, group in grouped_by_hour:
#                 result = {'Hour': hour}
#                 if 'GHI' in selected_data_types:
#                     mbe_temp_percent = self.calculate_nrmse_percent(
#                         group[self.mea_ghi_col], group['GHI'])
#                     result.update({
#                         'RMSE_GHI%': mbe_temp_percent
#                     })
#                 if 'DNI' in selected_data_types:
#                     mbe_temp_percent = self.calculate_nrmse_percent(
#                         group[self.mea_dni_col], group['DNI'])
#                     result.update({
#                         'RMSE_DNI%': mbe_temp_percent
#                     })
#                 rmse_percent_results.append(result)

#             return pd.DataFrame(rmse_percent_results)

#         elif monthly:
#             grouped_by_month = self.common_df.groupby(
#                 self.common_df.index.month)
#             rmse_percent_results = []

#             for month, group in grouped_by_month:
#                 result = {'Month': month}
#                 if 'GHI' in selected_data_types:
#                     mbe_temp_percent = self.calculate_nrmse_percent(
#                         group[self.mea_ghi_col], group['GHI'])
#                     result.update({
#                         'RMSE_GHI%': mbe_temp_percent
#                     })
#                 if 'DNI' in selected_data_types:
#                     mbe_temp_percent = self.calculate_nrmse_percent(
#                         group[self.mea_dni_col], group['DNI'])
#                     result.update({
#                         'RMSE_DNI%': mbe_temp_percent
#                     })
#                 rmse_percent_results.append(result)

#             return pd.DataFrame(rmse_percent_results)
