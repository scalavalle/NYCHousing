"""
Class: CS230--Section 005
Name: Saskia Calavalle
Description: Final Project - New York Housing Market
I pledge that I have completed the programming assignment independently.
I have not copied the code from a student or any source.
I have not given my code to any student.
"""

import streamlit as st
import pandas as pd
import pydeck as pdk     #[MAP]
import plotly.express as px   #[CHART1] #[CHART2]

DATA_FILE = "NY-House-Dataset.csv"

# ---------------- DATA LOADING ----------------
def load_data():
    df = pd.read_csv(DATA_FILE)
    df = df.dropna(     #[COLUMNS]
        subset=["PRICE", "BEDS", "BATH", "PROPERTYSQFT", "LOCALITY", "LATITUDE", "LONGITUDE", "TYPE", "FORMATTED_ADDRESS"]
    )
    df["BEDS"] = df["BEDS"].astype(int)
    df["PRICE_PER_SQFT"] = df["PRICE"] / df["PROPERTYSQFT"]     #[COLUMNS]
    return df

# --------- FILTER HELPERS ---------
#[FUNC2P] #[FUNCCALL2]
def apply_bed_filter(df, bed_choice="Any"):
    if bed_choice == "Any": return df
    if bed_choice == "6 or more": return df[df["BEDS"] >= 6]    #[FILTER1]
    return df[df["BEDS"] == int(bed_choice)]

#[FUNC2P] #[FUNCCALL2]
def apply_bath_filter(df, bath_choice):
    if bath_choice == "Any": return df
    if "or more" in bath_choice:
        n = int(bath_choice.split()[0])
        return df[df["BATH"] >= n]
    return df[df["BATH"] == float(bath_choice)]

#[FUNCRETURN2] #[ST2]
def price_dropdown(df, key_prefix):
    step = 50_000
    raw_min = df["PRICE"].min()
    raw_max = df["PRICE"].quantile(0.95)
    min_price = int(raw_min // step * step)
    max_price = int(raw_max // step * step) + step
    options = list(range(min_price, max_price + step, step))
    st.sidebar.markdown("Price range ($):")
    col_min, col_max = st.sidebar.columns(2)
    min_val = col_min.selectbox("Min", options, format_func=lambda x: f"${x:,}", key=f"{key_prefix}_min")
    max_val = col_max.selectbox("Max", options, index=len(options) - 1, format_func=lambda x: f"${x:,}", key=f"{key_prefix}_max")
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    return min_val, max_val

# ---------------- MAIN APP ----------------
def main():
    st.set_page_config(page_title="New York Housing Market Explorer", layout="wide")
    st.markdown("""
    <style>
    .block-container {padding-top: 1.5rem; background-color: #f9f9f9;}
    h1, h2, h3 {color: #1f77b4;}
    .welcome-section {text-align: center; margin-bottom: 2rem;}
    .left-align-text {text-align: left; max-width: 700px; margin: 0 auto;}
    </style>
    """, unsafe_allow_html=True)    #[ST3]

    df = load_data()
    st.image("ny.jpeg", use_container_width=True)   #[ST3]

    st.markdown("""
    <div class="welcome-section">
        <h1>New York Housing Market</h1>
        <p>Welcome to the New York Housing Market Explorer!</p>
        <div class="left-align-text">
            <p>Use the navigation bar below to:</p>
            <ul>
                <li>🔍 <strong>Find homes under a set price in a city</strong></li>
                <li>⚖️ <strong>Compare average home prices across cities</strong></li>
                <li>🏡 <strong>See which property type gives the most space for your budget</strong></li>
                <li>🗺️ <strong>View listings on a map</strong></li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

    section = st.radio("Choose a section to explore:", [
        "🔍 Find Homes in a City",
        "⚖️ Compare Two Cities",
        "🏡 Best Property Type for Space",
        "🗺️ Map of Listings"], horizontal=True)

    locality_options = sorted(df["LOCALITY"].unique())
    type_options = sorted(df["TYPE"].unique())
    bath_options = ["Any"] + [str(i) for i in range(1, int(df["BATH"].max()))] + [f"{int(df['BATH'].max())} or more"]   #[LISTCOMP]

    if section == "🔍 Find Homes in a City":
        st.sidebar.title("Filters")
        st.sidebar.markdown("Use these filters to find homes in one city below a set price.")
        city = st.sidebar.selectbox("City:", locality_options, key="s1_city")
        price_min, price_max = price_dropdown(df, "s1")
        bed = st.sidebar.selectbox("Bedrooms:", ["Any", "1", "2", "3", "4", "5", "6 or more"], key="s1_beds")   #[ST1]
        bath = st.sidebar.selectbox("Bathrooms:", bath_options, key="s1_bath")
        prop = st.sidebar.selectbox("Property Type:", ["Any"] + type_options, key="s1_type")

        filtered = df[(df["LOCALITY"] == city) & (df["PRICE"] >= price_min) & (df["PRICE"] <= price_max)]   #[FILTER2]
        filtered = apply_bed_filter(filtered, bed)
        filtered = apply_bath_filter(filtered, bath)
        if prop != "Any": filtered = filtered[filtered["TYPE"] == prop]

        # [ITERLOOP]
        for selected in [city]:
            st.caption(f"Showing listings for: {selected}")

        st.subheader(f"Listings in {city}")

        # [DICTMETHOD]
        city_notes = {
            "New York": "Includes Manhattan and Brooklyn",
            "Yonkers": "Known for affordable options",
            "Albany": "New York State's capital with diverse housing"
        }
        city_notes.update({"Bronx County": "Offers a mix of condos and co-ops at various prices"})
        if city in city_notes:
            st.info(f"📌 Note about {city}: {city_notes.get(city)}")

        if filtered.empty:
            st.info("No results. Adjust your filters.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Number of listings", len(filtered))
            col2.metric("Median price", f"${int(filtered['PRICE'].median()):,}")    #[MAXMIN]
            col3.metric("Median price per sqft", f"${int(filtered['PRICE_PER_SQFT'].median()):,}")      #[MAXMIN]

            st.markdown("### Results Table")
            display = filtered[["FORMATTED_ADDRESS", "PRICE", "BEDS", "BATH", "PROPERTYSQFT", "TYPE"]].sort_values("PRICE")     #[SORT]
            display["PRICE"] = display["PRICE"].map(lambda x: f"${x:,.0f}")
            st.dataframe(display)

    elif section == "⚖️ Compare Two Cities":
        st.sidebar.title("Filters")
        city1 = st.sidebar.selectbox("City 1:", locality_options, key="s2_city1")
        city2 = st.sidebar.selectbox("City 2:", [c for c in locality_options if c != city1], key="s2_city2")
        price_min, price_max = price_dropdown(df, "s2")
        bed = st.sidebar.selectbox("Bedrooms:", ["1", "2", "3", "4", "5", "6 or more"], key="s2_beds")

        subset = df[df["LOCALITY"].isin([city1, city2]) & (df["PRICE"] >= price_min) & (df["PRICE"] <= price_max)]
        subset = apply_bed_filter(subset, bed)

        st.subheader(f"Comparing {city1} and {city2} for {bed}-bedroom homes")
        if subset.empty:
            st.info("No results found.")
        else:
            stats = subset.groupby("LOCALITY")["PRICE"].agg(["mean", "median", "count"]).reset_index()
            stats.columns = ["City", "Average Price", "Median Price", "Listings"]

            fig = px.bar(stats, x="City", y="Average Price", title="Average Listing Price by City", color="City")       #[CHART1]
            fig.update_yaxes(tickprefix="$", separatethousands=True)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Pivot Table: Count of Listings by Area and Property Type")
            pivot = pd.pivot_table(subset, index="LOCALITY", columns="TYPE", values="PRICE", aggfunc="count", fill_value=0)     #[PIVOTTABLE]
            st.dataframe(pivot)

    elif section == "🏡 Best Property Type for Space":
        st.sidebar.title("Filters")
        sqft_min = int(df["PROPERTYSQFT"].min())
        sqft_max = int(df["PROPERTYSQFT"].quantile(0.99))
        sqft_low, sqft_high = st.sidebar.slider("Square footage range (sqft):", sqft_min, sqft_max, (sqft_min, sqft_max), step=50)
        price_min, price_max = price_dropdown(df, "s3")

        filtered = df[(df["PROPERTYSQFT"] >= sqft_low) & (df["PROPERTYSQFT"] <= sqft_high) & (df["PRICE"] >= price_min) & (df["PRICE"] <= price_max)]

        st.subheader("Average Square Footage by Property Type")
        if filtered.empty:
            st.info("No homes match these filters.")
        else:
            sqft_stats = filtered.groupby("TYPE")["PROPERTYSQFT"].mean().reset_index().sort_values("PROPERTYSQFT", ascending=False)
            sqft_stats.columns = ["Property Type", "Average Square Footage"]
            sqft_stats["Average Square Footage"] = sqft_stats["Average Square Footage"].map(lambda x: f"{x:,.0f} sqft")
            st.dataframe(sqft_stats)

            fig = px.scatter(       #[CHART2]
                sqft_stats,
                x="Property Type",
                y="Average Square Footage",
                title="Average Space per Property Type",
                labels={"Average Square Footage": "Average SqFt"},
            )
            st.plotly_chart(fig, use_container_width=True)

    elif section == "🗺️ Map of Listings":
        st.sidebar.title("Filters")
        city = st.sidebar.selectbox("City:", ["All areas"] + locality_options, key="s4_city")
        price_min, price_max = price_dropdown(df, "s4")
        bed = st.sidebar.selectbox("Bedrooms:", ["Any", "1", "2", "3", "4", "5", "6 or more"], key="s4_beds")
        bath = st.sidebar.selectbox("Bathrooms:", bath_options, key="s4_bath")
        prop = st.sidebar.selectbox("Property Type:", ["Any"] + type_options, key="s4_type")

        filtered = df[(df["PRICE"] >= price_min) & (df["PRICE"] <= price_max)]
        if city != "All areas":
            filtered = filtered[filtered["LOCALITY"] == city]
        filtered = apply_bed_filter(filtered, bed)
        filtered = apply_bath_filter(filtered, bath)
        if prop != "Any":
            filtered = filtered[filtered["TYPE"] == prop]

        st.subheader("Map of Filtered Listings")
        if filtered.empty:
            st.info("No homes to show on the map with the current filters.")
        else:
            center_lat = filtered["LATITUDE"].mean()
            center_lon = filtered["LONGITUDE"].mean()

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=filtered,
                get_position="[LONGITUDE, LATITUDE]",
                get_radius=40,
                get_fill_color=[236, 72, 153, 160],
                pickable=True,
            )

            tooltip = {
                "html": "<b>{FORMATTED_ADDRESS}</b><br/>Price: ${PRICE}<br/>Beds: {BEDS}, Baths: {BATH}<br/>SqFt: {PROPERTYSQFT}<br/>Type: {TYPE}",
                "style": {"backgroundColor": "black", "color": "white"},
            }

            view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=10, pitch=0)
            deck = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip)
            st.pydeck_chart(deck)   #[MAP]

if __name__ == "__main__":
    main()