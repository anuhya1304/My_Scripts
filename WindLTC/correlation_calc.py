import pandas as pd
import duckdb


def calculate_correlations(short_table_name, long_table_name, con, shift_range=(-720, 721, 10)):
    """
    Calculates the correlation for a range of time shifts using DuckDB tables.
     Correlation is calculated iteratively for each time shift to find the best alignment of long_data and short_data
    Args:
        short_table_name (str): Name of the DuckDB table containing short-term data
        long_table_name (str): Name of the DuckDB table containing long-term data
        con (duckdb.DuckDBPyConnection): DuckDB connection
        shift_range (tuple): Range of shifts to test (start, end, step)

    Returns:
        tuple: (max_shift, max_correlation, correlation_df)
    """
    results = []
    # con = duckdb.connect(database=':memory:')
    # Loop over the specified range of shifts
    for shift in range(*shift_range):
        # Shift the 'Timestamp' of long data by the specified number of minutes
        con.execute(f"""
                CREATE OR REPLACE TABLE shifted_long_data AS 
                SELECT *, Timestamp + INTERVAL '{shift} minutes' AS shifted_timestamp 
                FROM {long_table_name}
            """)

        # Use DuckDB to join tables on the shifted timestamp
        merged_data = con.execute(f"""
            SELECT short.speed AS speed_short, shifted.speed AS speed_long
            FROM {short_table_name} AS short
            INNER JOIN shifted_long_data AS shifted
            ON short.Timestamp = shifted.shifted_timestamp
        """).df()

        # Drop NaN values and calculate correlation if data is available
        merged_data = merged_data.dropna()
        if not merged_data.empty:
            correlation = merged_data['speed_short'].corr(
                merged_data['speed_long'])
            results.append((shift, correlation))
        else:
            results.append((shift, None))

    # Clean up temporary table
    con.execute("DROP TABLE IF EXISTS shifted_long_data")

    # Convert results to DataFrame
    correlation_df = pd.DataFrame(
        results, columns=['Shift (minutes)', 'Correlation'])

    # Find the maximum correlation and its corresponding shift
    valid_correlations = correlation_df.dropna()
    if not valid_correlations.empty:
        max_correlation_row = valid_correlations.loc[valid_correlations['Correlation'].idxmax(
        )]
        max_shift = max_correlation_row['Shift (minutes)']
        max_correlation = max_correlation_row['Correlation']
    else:
        max_shift = 0
        max_correlation = None

    return max_shift, max_correlation, correlation_df

# import pandas as pd
# import duckdb


# def calculate_correlations(short_data, long_data, shift_range=(-720, 721, 10)):
#     """
#     Calculates the correlation for a range of time shifts.

#     Args:
#         short_data (pd.DataFrame): DataFrame containing short-term data
#         long_data (pd.DataFrame): DataFrame containing long-term data
#         shift_range (tuple): Range of shifts to test (start, end, step)

#     Returns:
#         tuple: (max_shift, max_correlation, correlation_df)
#     """
#     results = []

#     # Create a DuckDB connection
#     con = duckdb.connect(database=':memory:')

#     # Loop over the specified range of shifts
#     for shift in range(*shift_range):
#         # Shift the 'Timestamp' of long data by the specified number of minutes
#         shifted_long_data = long_data.copy()

#         shifted_long_data['Timestamp'] = shifted_long_data['Timestamp'] + \
#             pd.Timedelta(minutes=shift)

#         # Register DataFrames with DuckDB
#         con.register('short_data', short_data)
#         con.register('shifted_long_data', shifted_long_data)

#         # Use DuckDB to merge and calculate correlation
#         merged_data = con.execute("""
#             SELECT short_data.speed AS speed_short, shifted_long_data.speed AS speed_long
#             FROM short_data
#             INNER JOIN shifted_long_data
#             ON short_data.Timestamp = shifted_long_data.Timestamp
#         """).df()

#         # Unregister DataFrames to free up memory
#         con.unregister('short_data')
#         con.unregister('shifted_long_data')

#         # Drop any NaN values
#         merged_data = merged_data.dropna()

#         # Calculate correlation if there are sufficient data points
#         if not merged_data.empty:
#             correlation = merged_data['speed_short'].corr(
#                 merged_data['speed_long'])
#             results.append((shift, correlation))
#         else:
#             results.append((shift, None))

#     # Close DuckDB connection
#     con.close()

#     # Convert results to DataFrame
#     correlation_df = pd.DataFrame(
#         results, columns=['Shift (minutes)', 'Correlation'])

#     # Find the maximum correlation and its corresponding shift
#     valid_correlations = correlation_df.dropna()
#     if not valid_correlations.empty:
#         max_correlation_row = valid_correlations.loc[valid_correlations['Correlation'].idxmax(
#         )]
#         max_shift = max_correlation_row['Shift (minutes)']
#         max_correlation = max_correlation_row['Correlation']
#     else:
#         max_shift = 0
#         max_correlation = None

#     return max_shift, max_correlation, correlation_df
# %%
# import pandas as pd
# import duckdb


# def calculate_correlations(short_data, long_data, shift_range=(-720, 721, 10)):
#     """
#     Calculates the correlation for a range of time shifts.
#     """
#     results = []

#     # Loop over the specified range of shifts
#     for shift in range(*shift_range):
#         # Shift the 'Timestamp' of long data by the specified number of minutes
#         shifted_long_data = long_data.copy()
#         shifted_long_data['Timestamp'] = shifted_long_data['Timestamp'] + \
#             pd.Timedelta(minutes=shift)

#         # Use DuckDB to merge and calculate correlation
#         merged_data = duckdb.query("""
#             SELECT short_data.speed AS speed_short, long_data.speed AS speed_long
#             FROM short_data
#             INNER JOIN shifted_long_data
#             ON short_data.Timestamp = shifted_long_data.Timestamp
#         """).to_df()

#         # Drop any NaN values
#         merged_data = merged_data.dropna()

#         # Calculate correlation if there are sufficient data points
#         if not merged_data.empty:
#             correlation = merged_data['speed_short'].corr(
#                 merged_data['speed_long'])
#             results.append((shift, correlation))
#         else:
#             results.append((shift, None))

#     # Convert results to DataFrame
#     correlation_df = pd.DataFrame(
#         results, columns=['Shift (minutes)', 'Correlation'])

#     # Find the maximum correlation and its corresponding shift
#     max_correlation_row = correlation_df.loc[correlation_df['Correlation'].idxmax(
#     )]
#     max_shift = max_correlation_row['Shift (minutes)']
#     max_correlation = max_correlation_row['Correlation']

#     return max_shift, max_correlation, correlation_df
