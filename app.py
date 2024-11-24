import streamlit as st
import pandas as pd
import altair as alt

@st.cache_data
def load_csv(url):
    df = pd.read_csv(f"data/{url}")
    return df

st.set_page_config(page_title="Recon", page_icon="✔")
st.title("✔ Recon Sample")
st.write("""
A sample example of comparing two large files that contain a numeric column
         """)

left = load_csv('left.csv')

right = load_csv('right.csv')

st.write(f"Records on left: {len(left)} " )
st.write(f"Records on right: {len(right)} " )

aggregated_file1 = right.groupby(['trade_id', 'version'], as_index=False).agg({'quantity': 'sum'})

merged = pd.merge(
    left, 
    aggregated_file1, 
    on=['trade_id', 'version'], 
    how='outer', 
    suffixes=('_left', '_right'), 
    indicator=True
)

left_only = merged[merged['_merge'] == 'left_only']  
right_only = merged[merged['_merge'] == 'right_only'] 

# Breaks: Mismatched quantity beyond a 5% tolerance
breaks = merged[
    (merged['_merge'] == 'both') & 
    (~((abs(merged['quantity_left'] - merged['quantity_right']) / merged['quantity_right']) <= 0.05))
]

left_only.drop(columns=['_merge', 'quantity_left'], inplace=True)
right_only.drop(columns=['_merge', 'quantity_right'], inplace=True)
breaks.drop(columns=['_merge'], inplace=True)

breaks['quantity_difference'] = breaks['quantity_left'] - breaks['quantity_right']

# GUI filters
quantity = st.slider("Quantity", 0, 1000, (0,1000))

breaks = breaks[(breaks["quantity_difference"].between(quantity[0], quantity[1]))]

col1, col2 = st.columns(2)

with col1:
    st.write('Left only')
    st.write(left_only)

with col2:
    st.write('Right only')
    st.write(right_only)

st.divider()

st.header('Breaks')
st.write(breaks)

bins = [-float("inf"), -100, -50, 0, 50, 100, float("inf")]
labels = ['<-100', '-100 to -50', '-50 to 0', '0 to 50', '50 to 100', '>100']
breaks['quantity_diff_range'] = pd.cut(breaks['quantity_difference'], bins=bins, labels=labels)

breaks_grouped = breaks['quantity_diff_range'].value_counts().reset_index()
breaks_grouped.columns = ['quantity_diff_range', 'count']

chart = alt.Chart(breaks_grouped).mark_arc().encode(
    theta=alt.Theta(field='count', type='quantitative'),
    color=alt.Color(field='quantity_diff_range', type='nominal', legend=alt.Legend(title="Quantity Difference Range")),
    tooltip=['quantity_diff_range', 'count']
).properties(
    title="Breaks Distribution by Quantity Difference Range"
)

st.altair_chart(chart, use_container_width=True)
