import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
import numpy as np

st.set_page_config(page_title="CSE Analytics Dashboard", layout="wide")




df = pd.read_excel(
    r"C:\Users\VIHANGI\Downloads\Expolanka_WebApp\Expolanka_WebApp\Annual Trading Statistics.xlsx",
    sheet_name=None
)


gics_df = pd.read_excel(r"C:\Users\VIHANGI\Downloads\Expolanka_WebApp\Expolanka_WebApp\GICS.xlsx")

gics_df.columns = gics_df.columns.str.strip().str.replace(" ", "_")



expected_years = set(str(y) for y in range(2006, 2023))
actual_years = set(df.keys())

missing_years = expected_years - actual_years
print("Missing years:", missing_years)

for year, yearly_df in df.items():
    yearly_df.columns = (
        yearly_df.columns
        .str.strip()
        .str.replace(' ', '_')
        .str.replace('.', '', regex=False)
        .str.replace('Close_Price_', 'Close_', regex=False)
    )



company_sets = []

for year, yearly_df in df.items():
    companies = set(yearly_df['Symbol'].dropna())
    company_sets.append(companies)

companies_all_years = set.intersection(*company_sets)

agg_dict = {
    'Company_Name': 'first',
    'Open_(Rs)': 'mean',
    'High_(Rs)': 'max',
    'Low_(Rs)': 'min',
    'Close_(Rs)': 'mean',
    'Trade_Volume': 'sum',
    'Share_Volume': 'sum',
    'Turnover(Rs)': 'sum'
}


all_years_data = []

for year, yearly_df in df.items():

    annual_df = (
        yearly_df
        .groupby('Symbol', as_index=False)
        .agg(agg_dict)
    )

   
    annual_df = annual_df[
        annual_df['Symbol'].isin(companies_all_years)
    ]

   
    annual_df['Year'] = int(year)

   
    annual_df = annual_df.merge(
        gics_df,
        on='Symbol',
        how='left'
    )

    all_years_data.append(annual_df)


# Final dataset

merged_df = (
    pd.concat(all_years_data, ignore_index=True)
    .sort_values(['Year', 'Symbol'])
    .reset_index(drop=True)
)


merged_df.to_excel("final_merged_dataset.xlsx", index=False)

print(" Final dataset created successfully!")



@st.cache_data
def load_data():
    df = pd.read_excel("final_merged_dataset.xlsx")
    df.columns = df.columns.str.strip()
    df["Volatility (%)"] = ((df["High_(Rs)"] - df["Low_(Rs)"]) / df["Low_(Rs)"]) * 100
    return df

df = load_data()

# Sidebar
st.sidebar.title(" CSE Analytics")

companies = st.sidebar.multiselect(
    "Select Company",
    df["Company_Name"].unique(),
    default=df["Company_Name"].unique()
)

year_range = st.sidebar.slider(
    "Select Year Range",
    int(df["Year"].min()),
    int(df["Year"].max()),
    (int(df["Year"].min()), int(df["Year"].max()))
)

filtered_df = df[
    (df["Company_Name"].isin(companies)) &
    (df["Year"] >= year_range[0]) &
    (df["Year"] <= year_range[1])
]

page = st.sidebar.radio(
    "Navigation",
    ["Expolanka Analysis","Sector Comparison","Advanced Analytics","Raw Data Explorer"]
)

# -------------------------------
# EXPOLANKA ANALYSIS
# -------------------------------

if page == "Expolanka Analysis":

    expo_df = filtered_df[
        filtered_df["Company_Name"].str.contains("EXPOLANKA", case=False)
    ].sort_values("Year")

    st.title(" Expolanka Holdings PLC: Performance Analysis")

    m1,m2,m3,m4 = st.columns(4)

    m1.metric("Avg Annual Turnover",f"Rs {expo_df['Turnover(Rs)'].mean()/1e9:.2f}B")
    m2.metric("Peak Share Price",f"Rs {expo_df['High_(Rs)'].max():.2f}")
    m3.metric("Total Trades",f"{expo_df['Trade_Volume'].sum():,}")
    m4.metric("Avg Volatility",f"{expo_df['Volatility (%)'].mean():.2f}%")

    st.divider()

    col1,col2 = st.columns(2)

    with col1:
        st.subheader("High, Low & Closing Prices")

        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(x=expo_df["Year"], y=expo_df["High_(Rs)"], name="High"))
        fig_price.add_trace(go.Scatter(x=expo_df["Year"], y=expo_df["Low_(Rs)"], name="Low"))
        fig_price.add_trace(go.Scatter(x=expo_df["Year"], y=expo_df["Close_(Rs)"], name="Close"))

        st.plotly_chart(fig_price, use_container_width=True)

        st.info("This plot illustrates the yearly movement of stock prices, including high, low, and closing values. A consistent upward trend indicates strong company growth and investor confidence, while fluctuations reflect market volatility.")

    with col2:
        st.subheader("Annual Turnover")

        fig_turnover = px.bar(expo_df, x="Year", y="Turnover(Rs)", color="Turnover(Rs)")
        st.plotly_chart(fig_turnover, use_container_width=True)

        st.info("This chart represents annual trading turnover. Higher turnover indicates increased market activity and investor participation, while sudden changes may reflect shifts in market sentiment.")

    st.divider()

    col3,col4 = st.columns(2)

    with col3:
        st.subheader("Volatility vs Trade Volume")

        fig_scatter = px.scatter(expo_df, x="Volatility (%)", y="Trade_Volume", size="Turnover(Rs)", color="Year")
        st.plotly_chart(fig_scatter, use_container_width=True)

        st.info("This scatter plot shows the relationship between volatility and trade volume. High volatility with high volume indicates active market conditions and possible uncertainty.")

    with col4:
        st.subheader("Share Volume vs Trade Counts")

        fig_vol = go.Figure()
        fig_vol.add_trace(go.Bar(x=expo_df["Year"], y=expo_df["Share_Volume"], name="Share Volume"))
        fig_vol.add_trace(go.Scatter(x=expo_df["Year"], y=expo_df["Trade_Volume"], yaxis="y2", name="Trade Volume"))

        fig_vol.update_layout(
            yaxis=dict(title="Share Volume"),
            yaxis2=dict(title="Trade Volume", overlaying="y", side="right")
        )

        st.plotly_chart(fig_vol, use_container_width=True)

        st.info("This visualization compares share volume and trade volume. A strong relationship indicates consistent trading behavior, while differences may highlight changes in investor activity.")

# -------------------------------
# SECTOR COMPARISON
# -------------------------------

elif page == "Sector Comparison":

    st.title(" Industry Benchmarking")

    avg_sector_turnover = filtered_df.groupby(
        ["Year","GICS_Industry_Group"]
    )["Turnover(Rs)"].mean().reset_index()

    fig_sector = px.line(avg_sector_turnover, x="Year", y="Turnover(Rs)", color="GICS_Industry_Group")
    st.plotly_chart(fig_sector, use_container_width=True)

    st.info("This plot compares turnover across different industry groups. It helps identify which sectors dominate the market and how their performance changes over time.")

    st.subheader("Volatility Distribution by Industry")

    fig_box = px.box(filtered_df, x="GICS_Industry_Group", y="Volatility (%)")
    st.plotly_chart(fig_box, use_container_width=True)

    st.info("This box plot shows the distribution of volatility across industries. Wider spreads indicate higher variability, while compact distributions suggest stability.")

# -------------------------------
# ADVANCED ANALYTICS
# -------------------------------

elif page == "Advanced Analytics":

    st.title(" Advanced Analytics")

    numeric_cols = filtered_df.select_dtypes(include=np.number).columns

    x_var = st.selectbox("Select X Variable", numeric_cols)
    y_var = st.selectbox("Select Y Variable", numeric_cols)

    st.subheader(" Regression Analysis Insight")

    X = filtered_df[[x_var]]
    y = filtered_df[y_var]

  
    reg_df = pd.concat([X, y], axis=1).dropna()

    if len(reg_df) > 1:

        model = LinearRegression()
        model.fit(reg_df[[x_var]], reg_df[y_var])

        coef = model.coef_[0]

        st.write(f"Regression coefficient between **{x_var}** and **{y_var}** = {coef:.3f}")

        # Interpretation
        if coef > 0:
            st.success("There is a positive relationship between the selected variables. As one increases, the other tends to increase.")
        elif coef < 0:
            st.warning("There is a negative relationship between the selected variables. As one increases, the other tends to decrease.")
        else:
            st.info("No significant linear relationship detected between the variables.")

    else:
        st.error("Not enough data for regression analysis.")

    fig = px.scatter(filtered_df, x=x_var, y=y_var, color="Company_Name", trendline="ols")
    st.plotly_chart(fig, use_container_width=True)

    st.info("This plot analyzes the relationship between selected variables using regression. The trendline shows whether the relationship is positive or negative.")

    st.subheader("Correlation Heatmap")

    corr = filtered_df[numeric_cols].corr()
    fig_heat, ax = plt.subplots(figsize=(10,6))
    sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
    st.pyplot(fig_heat)

    st.info("The heatmap displays relationships between variables. Strong correlations help identify which factors influence stock behavior.")

    st.subheader("K-Means Clustering")

    features = st.multiselect("Select Features", numeric_cols, default=["Close_(Rs)","Trade_Volume"])
    k = st.slider("Clusters",2,6,3)

    if len(features) >= 2:
        kmeans = KMeans(n_clusters=k)
        filtered_df["Cluster"] = kmeans.fit_predict(filtered_df[features])

        fig_cluster = px.scatter(filtered_df, x=features[0], y=features[1], color="Cluster")
        st.plotly_chart(fig_cluster, use_container_width=True)

        st.info("Clustering groups similar data points. Each cluster represents a unique market behavior pattern.")

    # -----------------------
    # TIME SERIES
    # -----------------------

    st.header(" Time Series Trend")

    company_ts = st.selectbox(
        "Select Company",
        filtered_df["Company_Name"].unique()
    )

    ts_df = filtered_df[filtered_df["Company_Name"] == company_ts]

    fig_ts = px.line(
        ts_df,
        x="Year",
        y="Close_(Rs)",
        markers=True
    )

    st.plotly_chart(fig_ts,use_container_width=True)

    st.info(
    "This time series plot shows how the selected company's closing price changes over time. "
    "An upward trend indicates long-term growth and increasing investor confidence, while "
    "downward trends suggest declining performance. Fluctuations in the line highlight "
    "periods of market volatility, which may be influenced by economic conditions or company-specific events."
)

# -------------------------------
# RAW DATA
# -------------------------------

elif page == "Raw Data Explorer":

    st.title(" Data Explorer")

    search = st.text_input("Filter by Company Name")

    if search:
        display_df = filtered_df[filtered_df["Company_Name"].str.contains(search, case=False)]
    else:
        display_df = filtered_df

    st.dataframe(display_df)

    csv = display_df.to_csv(index=False).encode("utf-8")

    st.download_button("Download Data", csv, "cse_data.csv")

st.sidebar.info("Data source: Colombo Stock Exchange (2006-2022)")