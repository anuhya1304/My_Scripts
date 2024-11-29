import streamlit as st

import duckdb  # Import DuckDB
from data_processing import ReadData, process_data
from correlation_calc import calculate_correlations
# from without_noise_calc import calculate_without_noise
import warnings
# from sector_based_correction import apply_sector_model
# from test_noise_calc import apply_sector_model
from test_NoiseCalculation import NoiseCalculation
from varaiability_calc import uncertainity_calc
from correlation_plot import plot_correlation
from WindSpeed_plotting import compute_graph_data

warnings.filterwarnings("ignore")

# Streamlit page configuration
st.set_page_config(
    page_title="Wind Site Adaption",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

# Initialize DuckDB connection
conn = duckdb.connect(database=':memory:')  # In-memory database

# Streamlit Tabs
datasettab, adaptiontab, mergertab = st.tabs(
    ["📝 Dataset", '📊 AdaptionTab', "🔗 MergerTab"])

# Initialize session state for data
if 'long_data_tables' not in st.session_state:
    st.session_state.long_data_tables = []
if 'short_data_tables' not in st.session_state:
    st.session_state.short_data_tables = []
if 'correlation_results' not in st.session_state:
    st.session_state.correlation_results = []
if 'ltc_data' not in st.session_state:
    st.session_state.ltc_data = []
if 'final_data' not in st.session_state:
    st.session_state.final_data = []

with datasettab:
    # File uploader for long and short data files
    long_files = st.file_uploader("Upload Long Data CSV Files", type=[
                                  'csv', 'txt', 'xlsx'], accept_multiple_files=True)
    short_files = st.file_uploader("Upload Short Data CSV Files", type=[
                                   'csv', 'txt', 'xlsx'], accept_multiple_files=True)

    if long_files and short_files:
        if len(long_files) != len(short_files):
            st.error("Please upload an equal number of long and short data files.")
        else:
            for index, (long_file, short_file) in enumerate(zip(long_files, short_files)):
                st.write(f"Processing Pair {index + 1}")

                # Read files
                long_data = ReadData(long_file)
                short_data = ReadData(short_file)

                # Load data into DuckDB tables
                long_table_name = f'long_data_{index}'
                short_table_name = f'short_data_{index}'

                conn.execute(
                    f"CREATE OR REPLACE TABLE {long_table_name} AS SELECT * FROM long_data")
                conn.execute(
                    f"CREATE OR REPLACE TABLE {short_table_name} AS SELECT * FROM short_data")

                # Save table names in session state for later access
                st.session_state.long_data_tables.append(long_table_name)
                st.session_state.short_data_tables.append(short_table_name)

                # Display data previews
                st.write("Long Data Preview:", long_data.head())
                st.write("Short Data Preview:", short_data.head())
with adaptiontab:
    if st.session_state.short_data_tables and st.session_state.long_data_tables:
        # Create nested tabs inside AdaptionTab
        with_noise_tab, without_noise_tab, graph_tab = st.tabs(
            ['With Noise', 'Without Noise', '📈Cor_Graphs'])

        # Tab for "With Noise" data
        with with_noise_tab:
            for index, (short_table, long_table) in enumerate(zip(st.session_state.short_data_tables,
                                                                  st.session_state.long_data_tables)):
                # Calculate correlations and shifted long data
                max_shift, max_correlation, correlation_df = calculate_correlations(
                    short_table, long_table, conn)
                max_shift = int(max_shift)

                # Shift long data for max correlation shift
                conn.execute(f"""
                    SELECT *, date_add(Timestamp, INTERVAL {max_shift} MINUTE) AS Adjusted_Timestamp
                    FROM {long_table}
                """)
                shifted_long_data = conn.fetchdf()
                st.session_state.correlation_results.append(correlation_df)

                # Filter and merge data for "With Noise"
                merge_query = f"""
                    SELECT s.*, l.*
                    FROM {short_table} AS s
                    INNER JOIN {long_table} AS l
                    ON s.Timestamp = l.Timestamp
                """
                conn.execute(merge_query)
                merged_data = conn.fetchdf().dropna()

                # Adjust column names to distinguish between short and long data
                merged_data.columns = [
                    col + '_short' if 's.' in col else col for col in merged_data.columns]
                merged_data.columns = [
                    col + '_long' if 'l.' in col else col for col in merged_data.columns]

                # Filtered merged query
                long_filtered_query = f"SELECT * FROM {long_table} WHERE speed >= 3.99"
                conn.execute(long_filtered_query)
                long_data_filtered = conn.fetchdf()

                # Filtered merged query with long data conditions
                filtered_merge_query = f"""
                    SELECT s.*, l.*
                    FROM {short_table} AS s
                    INNER JOIN ({long_filtered_query}) AS l
                    ON s.Timestamp = l.Timestamp
                """
                conn.execute(filtered_merge_query)
                merged_data_filtered = conn.fetchdf().dropna()

                # Adjust column names for filtered merged data
                merged_data_filtered.columns = [
                    col + '_short' if 's.' in col else col for col in merged_data_filtered.columns]
                merged_data_filtered.columns = [
                    col + '_long' if 'l.' in col else col for col in merged_data_filtered.columns]
                st.write(merged_data_filtered.columns)
                # Calculate with noise (using apply_sector_model for noise calculation)
                noise_calculator = NoiseCalculation()
                output_df = noise_calculator.with_noise(
                    merged_data_filtered)
                # output_df = apply_sector_model(
                #     merged_data_filtered)  # "With Noise" model
                ltc_data = process_data(
                    long_data,  merged_data_filtered)
                st.session_state.ltc_data.append(ltc_data)

                # Display merged data with corrected speed
            # st.write('Merged Data with Corrected Speed:', output_df.head())

            # Download button for "With Noise" data
            st.download_button(
                label=f"Download With Noise Data for Pair {index + 1}",
                data=output_df.to_csv(index=False),
                file_name=f'with_noise_data_pair_{index + 1}.csv',
                mime='text/csv'
            )

        with without_noise_tab:
            st.title("Wind Data Uncertainty and KS Statistic Analysis")
            with st.sidebar:
                st.header("User Inputs")
                bin_sizes_input = st.text_input(
                    "Enter bin sizes (comma-separated, e.g., 0.25,0.5,1):", "0.25,0.5,1")
                bin_sizes = [float(b) for b in bin_sizes_input.split(",")]

            for index, (short_table, long_table) in enumerate(zip(st.session_state.short_data_tables, st.session_state.long_data_tables)):
                # Filtering and merging data
                long_filtered_query = f"SELECT * FROM {long_table} WHERE speed >= 3.99"
                conn.execute(long_filtered_query)
                long_data_filtered = conn.fetchdf()

                merge_query = f"""
                    SELECT s.*, l.*
                    FROM {short_table} AS s
                    INNER JOIN {long_table} AS l
                    ON s.Timestamp = l.Timestamp
                """
                conn.execute(merge_query)
                merged_data = conn.fetchdf().dropna()

                # Adjust column names to distinguish between short and long data
                merged_data.columns = [
                    col + '_short' if 's.' in col else col for col in merged_data.columns]
                merged_data.columns = [
                    col + '_long' if 'l.' in col else col for col in merged_data.columns]

                # Filtered merged query
                filtered_merge_query = f"""
                    SELECT s.*, l.*
                    FROM {short_table} AS s
                    INNER JOIN ({long_filtered_query}) AS l
                    ON s.Timestamp = l.Timestamp
                """
                conn.execute(filtered_merge_query)
                merged_data_filtered = conn.fetchdf().dropna()

                # Adjust column names for filtered merged data
                merged_data_filtered.columns = [
                    col + '_short' if 's.' in col else col for col in merged_data_filtered.columns]
                merged_data_filtered.columns = [
                    col + '_long' if 'l.' in col else col for col in merged_data_filtered.columns]

                # Calculate without noise
                final_data, m_data, spd_data = noise_calculator.without_noise(
                    merged_data_filtered, merged_data, long_data, short_data
                )
                # final_data, merged_result, spd_data = calculate_without_noise(
                #     merged_data_filtered, merged_data, long_data_filtered, short_data)

                var_sum_data = uncertainity_calc(
                    merged_data_filtered, short_data, long_data, ltc_data, final_data)
                summary_var_data, ks_statistics_df = uncertainity_calc(
                    merged_data_filtered=merged_data_filtered,
                    short_data=short_data,
                    long_data=long_data,
                    ltc_data=ltc_data,
                    final_data=final_data,
                    bin_sizes=bin_sizes
                )
            st.write(ks_statistics_df)

            st.download_button(
                label=f"Download Without Noise Data for Pair {index + 1}",
                data=final_data.to_csv(index=False),
                file_name=f'without_noise_data_pair_{index + 1}.csv',
                mime='text/csv'
            )

            st.write(var_sum_data)
        with graph_tab:
            st.title("Correlation Graphs")
            for index, (short_table, long_table) in enumerate(zip(st.session_state.short_data_tables, st.session_state.long_data_tables)):
                # Filtering and merging data for plotting
                merge_query = f"""
                    SELECT s.*, l.*
                    FROM {short_table} AS s
                    INNER JOIN {long_table} AS l
                    ON s.Timestamp = l.Timestamp
                """
                conn.execute(merge_query)
                merged_data = conn.fetchdf().dropna()

                # Adjust column names for clarity
                merged_data.rename(columns={
                    'speed': 'speed_short',
                    'speed_1': 'speed_long',
                    'direction': 'direction_short',
                    'direction_1': 'direction_long'
                }, inplace=True)

                # Resample data for daily, weekly, and monthly correlations
                daily_data = merged_data.resample(
                    'D', on='Timestamp').mean().dropna()
                weekly_data = merged_data.resample(
                    'W', on='Timestamp').mean().dropna()
                monthly_data = merged_data.resample(
                    'M', on='Timestamp').mean().dropna()

                # Collect graphs in a list
                correlation_graphs = []
                # Display correlation plots

                for data, period in zip(
                    [daily_data, weekly_data, monthly_data],
                    ["Daily", "Weekly", "Monthly"]
                ):
                    # Generate the graphs and add them to the list
                    speed_graph = plot_correlation(
                        data,
                        'speed_short', 'speed_long',
                        f"{period} Wind Speed Correlation",
                        "Speed Short (Measured)", "Speed Long (Corrected)"
                    )
                    direction_graph = plot_correlation(
                        data,
                        'direction_short', 'direction_long',
                        f"{period} Wind Direction Correlation",
                        "Direction Short (Measured)", "Direction Long (Corrected)"
                    )
                    correlation_graphs.append((speed_graph, direction_graph))

                # Display the graphs in two rows (speed and direction correlations)
            cols = st.columns(3)  # Create three columns

            # First row: Wind Speed Correlations
            for i, (speed_graph, _) in enumerate(correlation_graphs):
                with cols[i]:  # Place each graph in a column
                    st.altair_chart(speed_graph, use_container_width=True)

            # Second row: Wind Direction Correlations
            cols = st.columns(3)  # Create three columns again
            for i, (_, direction_graph) in enumerate(correlation_graphs):
                with cols[i]:  # Place each graph in a column
                    st.altair_chart(direction_graph,
                                    use_container_width=True)



            # Compute graph data for additional plots
            graph_data = compute_graph_data(merged_data, m_data)

            # Extract computed data
            hourly_data = graph_data["hourly_data"]
            monthly_data = graph_data["monthly_data"]
            wind_speed_range = graph_data["wind_speed_range"]
            measured_density = graph_data["measured_density"]
            predicted_density = graph_data["predicted_density"]
            wind_speed_range_without = graph_data["wind_speed_range_without"]
            predicted_density_without = graph_data["predicted_density_without"]
            sector_pct_long = graph_data["sector_pct_long"]
            sector_pct_short = graph_data["sector_pct_short"]

            # Additional Graphs
            st.subheader("Diurnal Wind Speed")
            st.line_chart(
                hourly_data[['speed_short', 'speed_long']], height=300)

            st.subheader("Monthly Average Wind Speed")
            st.line_chart(
                monthly_data[['speed_short', 'speed_long']], height=300)

            st.subheader("Wind Speed Frequency - Residuals")
            st.line_chart(
                {
                    "Measured": measured_density * 100,
                    "Predicted": predicted_density * 100,
                },
                height=300
            )

            st.subheader("Wind Speed Frequency - No Residuals")
            st.line_chart(
                {
                    "Measured": measured_density * 100,
                    "Predicted Without Residuals": predicted_density_without * 100,
                },
                height=300
            )

            st.subheader("Wind Direction Frequency")
            st.bar_chart(
                {
                    "Long": sector_pct_long,
                    "Short": sector_pct_short,
                },
                height=300
            )


                # for data, period in zip(
                #     [daily_data, weekly_data, monthly_data],
                #     ["Daily", "Weekly", "Monthly"]
                # ):
                #     print('the garphs are:')

                #     st.altair_chart(
                #         plot_correlation(
                #             data,
                #             'speed_short', 'speed_long',
                #             f"{period} Wind Speed Correlation",
                #             "Speed Short (Measured)", "Speed Long (Corrected)"
                #         ),
                #         use_container_width=True
                #     )

                #     st.altair_chart(
                #         plot_correlation(
                #             data,
                #             'direction_short', 'direction_long',
                #             f"{period} Wind Direction Correlation",
                #             "Direction Short (Measured)", "Direction Long (Corrected)"
                #         ),
                #         use_container_width=True
                #     )
                # for speed_graph, direction_graph in correlation_graphs:
                #     st.altair_chart(speed_graph, use_container_width=True)
                #     st.altair_chart(direction_graph, use_container_width=True)