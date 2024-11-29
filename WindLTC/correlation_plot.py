import altair as alt
import pandas as pd
from scipy.stats import pearsonr

# Function for correlation plotting for daily, weekly, monthly


def plot_correlation(data, x_col, y_col, title, xlabel, ylabel):
    """
    Correlation is calculated for different aggregation levels (daily, weekly, monthly) and 
    displayed on scatter plots to visualize the relationship between the variables.
    """
    # Calculate correlation
    corr_value, _ = pearsonr(data[x_col], data[y_col])

    # Scatter plot with correlation line
    scatter_plot = alt.Chart(data).mark_point(filled=True, color='red').encode(
        x=alt.X(x_col, title=xlabel),
        y=alt.Y(y_col, title=ylabel)
    ).properties(
        title=f"{title} (Correlation: {corr_value:.2f})"
    )

    # Add a line for the correlation
    line = alt.Chart(pd.DataFrame({
        x_col: [data[x_col].min(), data[x_col].max()],
        y_col: [data[y_col].min(), data[y_col].max()]
    })).mark_line(color='blue', strokeDash=[5, 5]).encode(
        x=x_col,
        y=y_col
    )

    return scatter_plot + line

# import pandas as pd
# from sklearn.linear_model import LinearRegression
# import numpy as np
# import seaborn as sns
# from scipy.stats import pearsonr
# import matplotlib.pyplot as plt


# # Function for correlation plotting
# def plot_correlation(merged_data):
#     # Convert 'Timestamp' to datetime if not already done
#     merged_data['Timestamp'] = pd.to_datetime(
#         merged_data['Timestamp'], dayfirst=True)
#     merged_data.set_index('Timestamp', inplace=True)

#     # Set plot style

#     sns.set_theme(style='whitegrid')

#     # Function to calculate and display correlation values on scatter plots
#     def plot_with_correlation(x, y, data, title, ax, xlabel, ylabel):
#         sns.scatterplot(x=x, y=y, data=data, ax=ax,
#                         color='black', marker='*', s=100)  # Star points
#         corr_value, _ = pearsonr(data[x], data[y])
#         ax.set_title(f'{title}\nCorrelation: {corr_value:.2f}',
#                      fontsize=12, ha='center')
#         ax.set_xlabel(xlabel)
#         ax.set_ylabel(ylabel)
#         ax.set_xlim(data[x].min(), data[x].max())
#         ax.set_ylim(data[y].min(), data[y].max())
#         ax.plot([data[x].min(), data[x].max()], [data[y].min(),
#                 data[y].max()], color='blue', linestyle='--')

#     # Create a figure for 6 plots (2 rows, 3 columns)
#     fig, axes = plt.subplots(2, 3, figsize=(18, 12))

#     # Row 1: Wind Speed Correlation Plots
#     daily_data = merged_data.resample('D').mean().dropna()
#     plot_with_correlation('speed', 'speed_1', daily_data, 'Daily Wind Speed Correlation',
#                           axes[0, 0], 'Speed Short (Measured)', 'Corrected Speed (Predicted)')

#     weekly_data = merged_data.resample('W').mean().dropna()
#     plot_with_correlation('speed', 'speed_1', weekly_data, 'Weekly Wind Speed Correlation',
#                           axes[0, 1], 'Speed Short (Measured)', 'Corrected Speed (Predicted)')

#     monthly_data = merged_data.resample('M').mean().dropna()
#     plot_with_correlation('speed', 'speed_1', monthly_data, 'Monthly Wind Speed Correlation',
#                           axes[0, 2], 'Speed Short (Measured)', 'Corrected Speed (Predicted)')

#     # Row 2: Wind Direction Correlation Plots
#     plot_with_correlation('direction', 'direction_1', daily_data, 'Daily Wind Direction Correlation',
#                           axes[1, 0], 'Direction Short (Measured)', 'Corrected Direction (Predicted)')
#     plot_with_correlation('direction', 'direction_1', weekly_data, 'Weekly Wind Direction Correlation',
#                           axes[1, 1], 'Direction Short (Measured)', 'Corrected Direction (Predicted)')
#     plot_with_correlation('direction', 'direction_1', monthly_data, 'Monthly Wind Direction Correlation',
#                           axes[1, 2], 'Direction Short (Measured)', 'Corrected Direction (Predicted)')

#     plt.tight_layout()

#     plt.show()
# with graph_tab:
#             st.title('Correlation Graphs')
#             for index, (short_table, long_table) in enumerate(zip(st.session_state.short_data_tables, st.session_state.long_data_tables)):
#                 # Filtering and merging data for plotting
#                 merge_query = f"""
#                     SELECT s.*, l.*
#                     FROM {short_table} AS s
#                     INNER JOIN {long_table} AS l
#                     ON s.Timestamp = l.Timestamp
#                 """
#                 conn.execute(merge_query)
#                 merged_data = conn.fetchdf().dropna()

#                 # Adjust column names to distinguish between short and long data
#                 merged_data.columns = [
#                     col + '_short' if 's.' in col else col for col in merged_data.columns]
#                 merged_data.columns = [
#                     col + '_long' if 'l.' in col else col for col in merged_data.columns]

#                 # plot_merged_data = merged_data.copy()
#                 # plot_merged_data.rename(columns={
#                 #     'speed_short': 'speed_short',
#                 #     'speed_long': 'speed_long',
#                 #     'direction_short': 'direction_short',
#                 #     'direction_long': 'direction_long'
#                 # }, inplace=True)
#                 # # Plot and display correlation graphs
#                 # st.subheader(f"Correlation Graphs for Pair {index + 1}")
#             fig = plot_correlation(merged_data)
#             st.pyplot(fig)
