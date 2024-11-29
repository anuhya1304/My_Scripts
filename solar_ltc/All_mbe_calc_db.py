import pandas as pd
import numpy as np


class AllMBECalc:
    def __init__(self, common_df, data_type_columns):
        self.common_df = common_df
        # Dictionary with keys: 'GHI', 'DNI', 'Temp'
        self.data_type_columns = data_type_columns

    def calculate_mbe(self, actual, predicted):
        return (actual - predicted).mean()

    def calculate_mbe_percent(self, actual, predicted):
        mbe = self.calculate_mbe(actual, predicted)
        mean_actual = actual.mean()
        return mbe * 100 / mean_actual

    def calc_mbe(self, selected_data_types=['GHI', 'DNI', 'Temp']):
        # Initialize MBE results
        self.mbe_results_overall_list = []
        results = {'Overall': 'Overall'}

        # Loop through each selected data type and calculate MBE independently
        for data_type in selected_data_types:
            if data_type in self.data_type_columns:
                mea_col, adapted_cols = self.data_type_columns[data_type]
                results.update(self._calc_mbe_for_type(
                    data_type, mea_col, adapted_cols))

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
                if data_type in self.data_type_columns:
                    mea_col, _ = self.data_type_columns[data_type]
                    period_result[f'MBE_{data_type}'] = self.calculate_mbe(
                        subset[mea_col], subset[data_type])
            mbe_results.append(period_result)

        return pd.DataFrame(mbe_results)

    def calculate_mbe_percentages(self, selected_data_types, overall=False, hourly=False, monthly=False):
        # Calculate MBE percentages for different time periods
        results = []
        if overall:
            result = {'Overall': 'Overall'}
            for data_type in selected_data_types:
                if data_type in self.data_type_columns:
                    mea_col, _ = self.data_type_columns[data_type]
                    result.update(self._calc_mbe_percent_for_type(data_type, mea_col, [
                        data_type, f'{data_type.lower()}_adapted_1', f'{data_type.lower()}_adapted_2']))
            results.append(result)

        elif hourly or monthly:
            time_period = 'hour' if hourly else 'month'
            group = self.common_df.groupby(
                getattr(self.common_df.index, time_period))

            for period, subset in group:
                period_result = {time_period.capitalize(): period}
                for data_type in selected_data_types:
                    if data_type in self.data_type_columns:
                        mea_col, _ = self.data_type_columns[data_type]
                        period_result[f'MBE_{data_type}%'] = self.calculate_mbe_percent(
                            subset[mea_col], subset[data_type])
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
# # independed handling_V.0
# import pandas as pd


# class AllMBECalc:
#     def __init__(self, common_df, data_type_mapping):
#         """
#         Initialize with a DataFrame and a data type mapping.

#         Args:
#         - common_df (pd.DataFrame): The common DataFrame containing all data.
#         - data_type_mapping (dict): A mapping of data types to their measured and adapted columns.
#           Example:
#           {
#               'GHI': {'mea_col': 'mea_ghi_col', 'adapted_cols': ['GHI', 'ghi_adapted_1', 'ghi_adapted_2']},
#               'DNI': {'mea_col': 'mea_dni_col', 'adapted_cols': ['DNI', 'dni_adapted_1', 'dni_adapted_2']}
#           }
#         """
#         self.common_df = common_df
#         self.data_type_mapping = data_type_mapping

#     def calculate_mbe(self, actual, predicted):
#         return (actual - predicted).mean()

#     def calculate_mbe_percent(self, actual, predicted):
#         mbe = self.calculate_mbe(actual, predicted)
#         mean_actual = actual.mean()
#         return mbe * 100 / mean_actual

#     def calc_mbe(self, selected_data_types):
#         """
#         Calculate MBE for the selected data types.

#         Args:
#         - selected_data_types (list): List of data types to calculate MBE for.
#         """
#         mbe_results_overall_list = []

#         # Overall MBE Calculation
#         results = {'Overall': 'Overall'}
#         for data_type in selected_data_types:
#             if data_type in self.data_type_mapping:
#                 mapping = self.data_type_mapping[data_type]
#                 mea_col = mapping['mea_col']
#                 adapted_cols = mapping['adapted_cols']
#                 results.update(self._calc_mbe_for_type(
#                     data_type, mea_col, adapted_cols))

#         mbe_results_overall_list.append(results)
#         self.mbe_results_overall = pd.DataFrame(mbe_results_overall_list)

#         # Hourly, Monthly, and Percentage calculations
#         self.mbe_results_hourly = self.calculate_time_based_mbe(
#             selected_data_types, 'hour')
#         self.mbe_results_monthly = self.calculate_time_based_mbe(
#             selected_data_types, 'month')
#         self.mbe_results_overall_per = self.calculate_mbe_percentages(
#             selected_data_types, overall=True)
#         self.mbe_results_hourly_per = self.calculate_mbe_percentages(
#             selected_data_types, hourly=True)
#         self.mbe_results_monthly_per = self.calculate_mbe_percentages(
#             selected_data_types, monthly=True)

#         return (self.mbe_results_overall, self.mbe_results_hourly,
#                 self.mbe_results_monthly, self.mbe_results_overall_per,
#                 self.mbe_results_hourly_per, self.mbe_results_monthly_per)

#     def _calc_mbe_for_type(self, data_type, mea_col, adapted_cols):
#         mbe_dict = {}
#         for i, col in enumerate(adapted_cols):
#             mbe_dict[f'MBE_{data_type}_Adapted{i}' if i > 0 else f'MBE_{data_type}'] = self.calculate_mbe(
#                 self.common_df[mea_col], self.common_df[col]
#             )
#         return mbe_dict

#     def calculate_time_based_mbe(self, selected_data_types, time_period):
#         group = self.common_df.groupby(
#             getattr(self.common_df.index, time_period))
#         mbe_results = []

#         for period, subset in group:
#             period_result = {time_period.capitalize(): period}
#             for data_type in selected_data_types:
#                 if data_type in self.data_type_mapping:
#                     mapping = self.data_type_mapping[data_type]
#                     mea_col = mapping['mea_col']
#                     if mea_col is not None:
#                         period_result[f'MBE_{data_type}'] = self.calculate_mbe(
#                             subset[mea_col], subset[mapping['adapted_cols'][0]]
#                         )
#             mbe_results.append(period_result)

#         return pd.DataFrame(mbe_results)

#     def calculate_mbe_percentages(self, selected_data_types, overall=False, hourly=False, monthly=False):
#         results = []
#         time_period = 'hour' if hourly else 'month'

#         if overall:
#             result = {'Overall': 'Overall'}
#             for data_type in selected_data_types:
#                 if data_type in self.data_type_mapping:
#                     mapping = self.data_type_mapping[data_type]
#                     mea_col = mapping['mea_col']
#                     result.update(self._calc_mbe_percent_for_type(
#                         data_type, mea_col, mapping['adapted_cols']))
#             results.append(result)

#         elif hourly or monthly:
#             group = self.common_df.groupby(
#                 getattr(self.common_df.index, time_period))
#             for period, subset in group:
#                 period_result = {time_period.capitalize(): period}
#                 for data_type in selected_data_types:
#                     if data_type in self.data_type_mapping:
#                         mapping = self.data_type_mapping[data_type]
#                         mea_col = mapping['mea_col']
#                         period_result[f'MBE_{data_type}%'] = self.calculate_mbe_percent(
#                             subset[mea_col], subset[mapping['adapted_cols'][0]]
#                         )
#                 results.append(period_result)

#         return pd.DataFrame(results)

#     def _calc_mbe_percent_for_type(self, data_type, mea_col, adapted_cols):
#         mbe_dict = {}
#         for i, col in enumerate(adapted_cols):
#             mbe_dict[f'MBE_{data_type}_Adapted{i}%' if i > 0 else f'MBE_{data_type}%'] = self.calculate_mbe_percent(
#                 self.common_df[mea_col], self.common_df[col]
#             )
#         return mbe_dict
