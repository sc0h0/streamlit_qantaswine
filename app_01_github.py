import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Retrieve the DATA_LINK from Streamlit Secrets
decrypted_link = st.secrets["DATA_LINK"]

# Google Drive link for the CSV file
file_url = decrypted_link

# Google Drive link for the CSV file
file_url = decrypted_link

# Load the CSV file from Google Drive link
df = pd.read_csv(file_url)

# Remove any slug which contains the word 'subscription'
df = df[~df['slug'].str.contains('subscription', case=False, na=False)]

# retrieve the last updated timestamp
last_updated_url = st.secrets["LAST_UPDATED"]

# read the text from the url
last_updated = pd.read_csv(last_updated_url, header=None).iloc[0, 0]


# observed that the way the bonus points works is that currentprice_bonusPoint reflects the number of points earnt per casevariant_1
# and that currentprice_cashprice reflects the price of casevariant_1
# let's create a new column which is the price per point
df['price_per_point'] = df['currentprice_cashprice'] / df['currentprice_bonusPoint']
# again as cents per point
df['cents_per_point'] = df['price_per_point'] * 100
# round to 2 decimal places
df['cents_per_point'] = df['cents_per_point'].round(2)


# calculate the price per bottle
df['price_per_bottle'] = df['currentprice_cashprice']

# remove any non wine with price per bottle less thatn $1
df = df[df['price_per_bottle'] >= 1]



# create a historical df containing only price_per_bottle and price_per_point
# select the following columns and filter on eff_to = '9999-12-31'
# 'wine_name', 'price_per_bottle', 'cents_per_point', 'rec_deleted_flag'
df_hist = df[(df['eff_to'] == '9999-12-31')][['wine_name', 'price_per_bottle', 'cents_per_point', 'rec_deleted_flag', 'slug', 'wine_key']].copy()

# Add app title and last updated timestamp to the main page
st.title("Qantas Wine Bonus Point Tracker")
st.text(last_updated)

# Sidebar form for user input
with st.sidebar.form(key='filter_form'):
    # User input for filtering
    price_threshold = st.number_input('Max Price per Bottle (AUD)', min_value=0.0, value=100.0, step=5.0)
    
    # Checkbox toggles for categories
    show_available = st.checkbox('Show Available', value=True)
    show_available_pareto = st.checkbox('Show Available and Pareto-efficient', value=True)
    show_unavailable = st.checkbox('Show Unavailable', value=True)
    show_unavailable_pareto = st.checkbox('Show Unavailable and Pareto-efficient', value=True)

    # Submit button
    submit_button = st.form_submit_button(label='Apply Filters')

# Filter the DataFrame based on user input
filtered_df = df_hist[df_hist['price_per_bottle'] <= price_threshold].copy()

# Function to find Pareto-efficient wines
def is_pareto_efficient(costs):
    is_efficient = np.ones(costs.shape[0], dtype=bool)
    for i, cost in enumerate(costs):
        if is_efficient[i]:
            is_efficient[is_efficient] = np.any(costs[is_efficient] < cost, axis=1)
            is_efficient[i] = True  # Keep the current point
    return is_efficient

# Apply the function to identify Pareto-efficient wines
pareto_mask = is_pareto_efficient(filtered_df[['price_per_bottle', 'cents_per_point']].values)

# Update the entire DataFrame for rows with matching price and point values
filtered_df['is_pareto_efficient'] = False  # Default to not Pareto-efficient
filtered_df.loc[pareto_mask, 'is_pareto_efficient'] = True

# Ensure all wines with the same price_per_bottle and cents_per_point as a Pareto-efficient wine are marked
for price, point in filtered_df.loc[filtered_df['is_pareto_efficient'], ['price_per_bottle', 'cents_per_point']].values:
    filtered_df.loc[
        (filtered_df['price_per_bottle'] == price) & (filtered_df['cents_per_point'] == point),
        'is_pareto_efficient'
    ] = True

# Corrected categorisation based on availability and Pareto efficiency
filtered_df['category'] = filtered_df.apply(
    lambda row: 'Available and Pareto-efficient' if row['is_pareto_efficient'] and row['rec_deleted_flag'] == 0 else
                'Available' if not row['is_pareto_efficient'] and row['rec_deleted_flag'] == 0 else
                'Unavailable and Pareto-efficient' if row['is_pareto_efficient'] and row['rec_deleted_flag'] == 1 else
                'Unavailable',
    axis=1
)

# Filter based on the selected categories
categories_to_show = []
if show_available:
    categories_to_show.append('Available')
if show_available_pareto:
    categories_to_show.append('Available and Pareto-efficient')
if show_unavailable:
    categories_to_show.append('Unavailable')
if show_unavailable_pareto:
    categories_to_show.append('Unavailable and Pareto-efficient')

filtered_df = filtered_df[filtered_df['category'].isin(categories_to_show)]

# Add random noise for plotting, but keep original values
filtered_df['plot_price_per_bottle'] = filtered_df['price_per_bottle'] + np.random.uniform(-0.1, 0.1, size=filtered_df.shape[0])
filtered_df['plot_cents_per_point'] = filtered_df['cents_per_point'] + np.random.uniform(-0.1, 0.1, size=filtered_df.shape[0])

# Construct the full URL for each wine
filtered_df['url'] = 'https://wine.qantas.com/p/' + filtered_df['slug'] + '/' + filtered_df['wine_key']

# Define colours that work well on a dark background
color_discrete_map = {
    'Available': '#1f77b4',  # Bright blue
    'Available and Pareto-efficient': '#ff7f0e',  # Orange
    'Unavailable': '#d62728',  # Bright red
    'Unavailable and Pareto-efficient': '#9467bd'  # Purple
}

# Scatter Plot using Plotly
fig = px.scatter(
    filtered_df, 
    x='plot_price_per_bottle', 
    y='plot_cents_per_point', 
    hover_name='wine_name',
    hover_data={'price_per_bottle': True, 'cents_per_point': True, 'plot_price_per_bottle': False, 'plot_cents_per_point': False},  # Show original values on hover
    custom_data=['url'],  # Add URL to custom_data for click event
    color='category',
    labels={
        'plot_price_per_bottle': 'Price per Bottle ($)', 
        'plot_cents_per_point': 'Cents per Qantas Point',
        'category': 'Category'
    },
    symbol='category',
    size_max=10,  # Set maximum size for consistency
    color_discrete_map=color_discrete_map,
    symbol_map={
        'Available': 'circle', 
        'Available and Pareto-efficient': 'star', 
        'Unavailable': 'circle', 
        'Unavailable and Pareto-efficient': 'star'
    }
)

# Set axis limits to ensure they start from 0
fig.update_xaxes(range=[0, filtered_df['price_per_bottle'].max()])
fig.update_yaxes(range=[0, filtered_df['cents_per_point'].max()])

# Update layout to move legend below the graph
fig.update_layout(
    legend=dict(
        orientation="h",  # Horizontal layout
        yanchor="top",  # Anchor legend at the top of the extra space
        y=-0.3,  # Position below the chart, adjust this to move it further down
        xanchor="center",  # Center the legend horizontally
        x=0.5  # Center the legend relative to the chart
    ),
    margin=dict(b=80)  # Add more margin to the bottom to accommodate the legend
)

# Display the plot in Streamlit
st.plotly_chart(fig)

# Search bar for filtering the table
search_term = st.text_input("Search for a wine:")

# Filter the DataFrame based on the search term
if search_term:
    filtered_df = filtered_df[filtered_df['wine_name'].str.contains(search_term, case=False, na=False)]

# Limit the number of results to a maximum of 10
filtered_df = filtered_df.head(10)

# Display a table with wine name, price, and clickable URL
filtered_df['View Wine'] = filtered_df['url'].apply(lambda x: f'<a href="{x}" target="_blank">View Wine</a>')

# Create a dictionary to map original column names to prettier versions
pretty_column_names = {
    'wine_name': 'Wine Name',
    'price_per_bottle': 'Price per Bottle ($)',
    'cents_per_point': 'Cents per Qantas Point',
    'category': 'Category',
    'View Wine': 'Link to Wine'
}

# Select the relevant columns to display
table_df = filtered_df[['wine_name', 'price_per_bottle', 'cents_per_point', 'category', 'View Wine']]

# Rename columns for display purposes
table_df = table_df.rename(columns=pretty_column_names)

# Display the table with clickable links and prettified column names
st.write(table_df.to_html(escape=False), unsafe_allow_html=True)






