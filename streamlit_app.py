import streamlit as st
import pandas as pd
import math
from pathlib import Path
import plotly.express as px

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Shipping Data Dashboard',
    page_icon=':ship:', # This is an emoji shortcode. Could be a URL too.
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_shipping_data(company):
    """Grab shipping data from a CSV file based on the selected company.
    """
    DATA_FILENAME = Path(__file__).parent/f'data/{company}.csv'
    shipping_df = pd.read_csv(DATA_FILENAME, parse_dates=['ARRIVAL DATE'], dayfirst=True)
    return shipping_df

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :ship: Shipping Data Dashboard
'''

# Company selection dropdown
companies = ['Sayatva', 'Sri Energy', 'WOM', 'Parveen', 'JVS']
selected_company = st.selectbox('Select Company:', companies)

# Display the selected company name
st.write(f"**{selected_company}**")

# Load data based on the selected company
shipping_df = get_shipping_data(selected_company)

# Step 1: Date Range Picker
min_date = shipping_df['ARRIVAL DATE'].min().date()
max_date = shipping_df['ARRIVAL DATE'].max().date()

st.sidebar.header('Filters')
start_date = st.sidebar.date_input('Start Date', min_value=min_date, max_value=max_date, value=min_date)
end_date = st.sidebar.date_input('End Date', min_value=min_date, max_value=max_date, value=max_date)

filtered_df = shipping_df[(shipping_df['ARRIVAL DATE'].dt.date >= start_date) & (shipping_df['ARRIVAL DATE'].dt.date <= end_date)]

# Step 2: Dropdown Menus for Filtering
importers = list(filtered_df['IMPORTER NAME'].unique())
selected_importers = st.sidebar.multiselect(
    'Select importers:',
    importers,
    default=importers[:5]  # Default to the first 5 importers
)

importer_countries = ['All'] + list(filtered_df['IMPORTER COUNTRY'].unique())
selected_importer_country = st.sidebar.selectbox('Importer Country', importer_countries)

exporter_countries = ['All'] + list(filtered_df['COUNTRY OF ORIGIN'].unique())
selected_exporter_country = st.sidebar.selectbox('Exporter Country', exporter_countries)

if selected_importers:
    filtered_df = filtered_df[filtered_df['IMPORTER NAME'].isin(selected_importers)]
if selected_importer_country != 'All':
    filtered_df = filtered_df[filtered_df['IMPORTER COUNTRY'] == selected_importer_country]
if selected_exporter_country != 'All':
    filtered_df = filtered_df[filtered_df['COUNTRY OF ORIGIN'] == selected_exporter_country]

# Step 3: Top Importers
top_importers = filtered_df.groupby('IMPORTER NAME')[['IMPORT VALUE CIF', 'IMPORT VALUE FOB']].sum()
top_importers['TOTAL VALUE'] = top_importers['IMPORT VALUE CIF'].fillna(0) + top_importers['IMPORT VALUE FOB'].fillna(0)
top_importers = top_importers.sort_values('TOTAL VALUE', ascending=False).head(10)

st.header('Top Importers by Value')
fig = px.bar(top_importers, x=top_importers.index, y='TOTAL VALUE', color=top_importers.index,
             labels={'IMPORTER NAME': 'Importer', 'TOTAL VALUE': 'Total Value'})
fig.update_layout(showlegend=False)
st.plotly_chart(fig)

# Step 4: Top Products
top_products = filtered_df.groupby('PRODUCT DETAILS')[['IMPORT VALUE CIF', 'IMPORT VALUE FOB']].sum()
top_products['TOTAL VALUE'] = top_products['IMPORT VALUE CIF'].fillna(0) + top_products['IMPORT VALUE FOB'].fillna(0)
top_products = top_products.sort_values('TOTAL VALUE', ascending=False).head(10)

st.header('Top Products by Value')
fig = px.bar(top_products, x=top_products.index, y='TOTAL VALUE', color=top_products.index,
             labels={'PRODUCT DETAILS': 'Product', 'TOTAL VALUE': 'Total Value'})
fig.update_layout(showlegend=False)
st.plotly_chart(fig)

# Step 5: Time-Series Analysis
filtered_df['TOTAL VALUE'] = filtered_df['IMPORT VALUE CIF'].fillna(0) + filtered_df['IMPORT VALUE FOB'].fillna(0)
time_series_df = filtered_df.groupby(pd.Grouper(key='ARRIVAL DATE', freq='ME'))['TOTAL VALUE'].sum().reset_index()

st.header('Total Value Over Time')
fig = px.line(time_series_df, x='ARRIVAL DATE', y='TOTAL VALUE',
              labels={'ARRIVAL DATE': 'Date', 'TOTAL VALUE': 'Total Value'})
st.plotly_chart(fig)

# Step 6: Geographic Insights
geo_df = filtered_df.groupby('IMPORTER COUNTRY')['TOTAL VALUE'].sum().reset_index()

st.header('Total Value by Importer Country')
fig = px.choropleth(geo_df, locations='IMPORTER COUNTRY', locationmode='country names',
                    color='TOTAL VALUE', hover_name='IMPORTER COUNTRY', projection='natural earth',
                    color_continuous_scale='Viridis', range_color=[0, geo_df['TOTAL VALUE'].max()])
fig.update_layout(coloraxis_colorbar=dict(title='Total Value'))
st.plotly_chart(fig)

# Step 7: Quantity Analysis by Unit
st.header('Quantity Analysis by Unit')

quantity_units = ['PCS', 'NOS', 'SET', 'PKG', 'FTS', 'KGS', 'INC', 'METER', 'WDC']

# Replace 'Pieces' with 'PCS' in the 'QUANTITY UNIT' column
filtered_df['QUANTITY UNIT'] = filtered_df['QUANTITY UNIT'].replace('Pieces', 'PCS')

selected_unit = st.selectbox('Select Unit:', quantity_units)

unit_df = filtered_df[filtered_df['QUANTITY UNIT'] == selected_unit]
if not unit_df.empty:
    top_products_by_unit = unit_df.groupby('PRODUCT DETAILS')['QUANTITY'].sum().reset_index()
    top_products_by_unit = top_products_by_unit.nlargest(5, 'QUANTITY')
    fig = px.bar(top_products_by_unit, x='PRODUCT DETAILS', y='QUANTITY', color='PRODUCT DETAILS',
                 labels={'PRODUCT DETAILS': 'Product', 'QUANTITY': f'Quantity in {selected_unit}'})
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig)
else:
    st.write(f"No data available for the selected unit: {selected_unit}")
# Step 8: Metrics and KPIs
st.header('Metrics and KPIs')

total_value = filtered_df['TOTAL VALUE'].sum()
num_shipments = len(filtered_df)
num_importers = len(filtered_df['IMPORTER NAME'].unique())

col1, col2, col3 = st.columns(3)
col1.metric('Total Value', f'{total_value:,.2f}')
col2.metric('Number of Shipments', num_shipments)
col3.metric('Number of Importers', num_importers)
# Step 9: Searchable and Sortable Table
st.header('Shipment Details')
st.dataframe(filtered_df)

# Step 10: Trend Analysis
st.header('Trend Analysis')
trend_df = filtered_df.groupby([pd.Grouper(key='ARRIVAL DATE', freq='ME'), 'PRODUCT DETAILS'])['TOTAL VALUE'].sum().reset_index()
trend_df['PREV TOTAL VALUE'] = trend_df.groupby('PRODUCT DETAILS')['TOTAL VALUE'].shift(1)
trend_df['GROWTH RATE'] = ((trend_df['TOTAL VALUE'] - trend_df['PREV TOTAL VALUE']) / trend_df['PREV TOTAL VALUE']) * 100
trend_df = trend_df.dropna()

top_growth_products = trend_df.groupby('PRODUCT DETAILS')['GROWTH RATE'].mean().nlargest(5).reset_index()

fig = px.bar(top_growth_products, x='PRODUCT DETAILS', y='GROWTH RATE',
             labels={'PRODUCT DETAILS': 'Product', 'GROWTH RATE': 'Average Growth Rate (%)'})
st.plotly_chart(fig)

# Step 11: Product Details Drill-Down
st.header('Product Details')
selected_product = st.selectbox('Select Product:', filtered_df['PRODUCT DETAILS'].unique())

product_df = filtered_df[filtered_df['PRODUCT DETAILS'] == selected_product]
total_value_product = product_df['TOTAL VALUE'].sum()
total_quantity_product = product_df['QUANTITY'].sum()

st.write(f"Total Value for {selected_product}: {total_value_product:,.2f}")
st.write(f"Total Quantity for {selected_product}: {total_quantity_product:,.2f}")

top_importers_product = product_df.groupby('IMPORTER NAME')['TOTAL VALUE'].sum().nlargest(5).reset_index()
fig = px.bar(top_importers_product, x='IMPORTER NAME', y='TOTAL VALUE',
             labels={'IMPORTER NAME': 'Importer', 'TOTAL VALUE': 'Total Value'})
st.plotly_chart(fig)

# Step 12: Importer Details Drill-Down
st.header('Importer Details')
selected_importer = st.selectbox('Select Importer:', filtered_df['IMPORTER NAME'].unique())

importer_df = filtered_df[filtered_df['IMPORTER NAME'] == selected_importer]
total_value_importer = importer_df['TOTAL VALUE'].sum()
total_quantity_importer = importer_df['QUANTITY'].sum()

st.write(f"Total Value for {selected_importer}: {total_value_importer:,.2f}")
st.write(f"Total Quantity for {selected_importer}: {total_quantity_importer:,.2f}")

top_products_importer = importer_df.groupby('PRODUCT DETAILS')['TOTAL VALUE'].sum().nlargest(5).reset_index()
fig = px.bar(top_products_importer, x='PRODUCT DETAILS', y='TOTAL VALUE',
             labels={'PRODUCT DETAILS': 'Product', 'TOTAL VALUE': 'Total Value'})
st.plotly_chart(fig)