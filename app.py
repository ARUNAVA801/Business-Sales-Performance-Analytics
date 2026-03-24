import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Business Sales Performance Analytics", layout="wide")

st.title("Business Sales Performance Analytics Dashboard")
st.write("Upload your sales CSV file to analyze revenue trends, products, categories, and regional performance.")

# -----------------------------
# FILE UPLOAD
# -----------------------------
uploaded_file = st.file_uploader("Upload your sales dataset (CSV only)", type=["csv"])

if uploaded_file is None:
    st.info("Please upload a CSV file to begin.")
    st.stop()

# -----------------------------
# READ FILE SAFELY
# -----------------------------
encodings_to_try = ["utf-8", "latin1", "cp1252", "ISO-8859-1"]
separators_to_try = [",", ";", "\t"]

df = None
read_success = False

for enc in encodings_to_try:
    for sep in separators_to_try:
        try:
            uploaded_file.seek(0)
            temp_df = pd.read_csv(uploaded_file, encoding=enc, sep=sep)

            # Check if expected important columns exist
            expected_cols = ["Order ID", "Order Date", "Region", "Category", "Sub-Category", "Product Name", "Sales", "Quantity", "Profit"]
            matched_cols = [col for col in expected_cols if col in temp_df.columns]

            if len(matched_cols) >= 5:
                df = temp_df.copy()
                st.success(f"Dataset uploaded successfully using encoding='{enc}' and separator='{sep}'")
                read_success = True
                break
        except Exception:
            continue
    if read_success:
        break

if df is None:
    st.error("Could not read the file correctly. Please check whether it is a valid CSV.")
    st.stop()

# -----------------------------
# CLEAN COLUMN NAMES
# -----------------------------
df.columns = df.columns.str.strip()

# -----------------------------
# VALIDATE REQUIRED COLUMNS
# -----------------------------
required_columns = [
    "Order ID", "Order Date", "Region", "Category",
    "Sub-Category", "Product Name", "Sales", "Quantity", "Profit"
]

missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    st.error(f"Missing required columns: {missing_columns}")
    st.stop()

# -----------------------------
# DATA CLEANING
# -----------------------------
df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

if "Ship Date" in df.columns:
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")

numeric_cols = ["Sales", "Quantity", "Profit", "Discount"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df["Year"] = df["Order Date"].dt.year
df["Month"] = df["Order Date"].dt.month_name()
df["Month_Num"] = df["Order Date"].dt.month

df = df.dropna(subset=["Order Date", "Sales"])

if df.empty:
    st.error("Dataset is empty after cleaning. Please check your uploaded file.")
    st.stop()

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("Filter Data")

year_options = sorted(df["Year"].dropna().unique().tolist())
region_options = sorted(df["Region"].dropna().unique().tolist())
category_options = sorted(df["Category"].dropna().unique().tolist())

selected_years = st.sidebar.multiselect("Select Year", year_options, default=year_options)
selected_regions = st.sidebar.multiselect("Select Region", region_options, default=region_options)
selected_categories = st.sidebar.multiselect("Select Category", category_options, default=category_options)

filtered_df = df[
    (df["Year"].isin(selected_years)) &
    (df["Region"].isin(selected_regions)) &
    (df["Category"].isin(selected_categories))
].copy()

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# -----------------------------
# DATA PREVIEW
# -----------------------------
st.subheader("Dataset Preview")
st.dataframe(filtered_df.head())

# -----------------------------
# KPI SECTION
# -----------------------------
total_revenue = filtered_df["Sales"].sum()
total_profit = filtered_df["Profit"].sum()
total_orders = filtered_df["Order ID"].nunique()
total_quantity = filtered_df["Quantity"].sum()
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

st.subheader("Key Performance Indicators")
c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Total Revenue", f"{total_revenue:,.2f}")
c2.metric("Total Profit", f"{total_profit:,.2f}")
c3.metric("Total Orders", f"{total_orders:,}")
c4.metric("Total Quantity", f"{total_quantity:,.0f}")
c5.metric("Avg Order Value", f"{avg_order_value:,.2f}")

# -----------------------------
# REVENUE TREND
# -----------------------------
st.subheader("Revenue Trend Over Time")

monthly_sales = (
    filtered_df.groupby(["Year", "Month_Num", "Month"], as_index=False)["Sales"]
    .sum()
    .sort_values(["Year", "Month_Num"])
)

monthly_sales["Year-Month"] = monthly_sales["Month"] + " " + monthly_sales["Year"].astype(str)

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(monthly_sales["Year-Month"], monthly_sales["Sales"], marker="o")
ax.set_title("Monthly Revenue Trend")
ax.set_xlabel("Month")
ax.set_ylabel("Revenue")
plt.xticks(rotation=45)
st.pyplot(fig)

# -----------------------------
# TOP PRODUCTS
# -----------------------------
st.subheader("Top 10 Selling Products by Revenue")

top_products = (
    filtered_df.groupby("Product Name", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
    .head(10)
)

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(top_products["Product Name"][::-1], top_products["Sales"][::-1])
ax.set_title("Top 10 Products by Revenue")
ax.set_xlabel("Revenue")
ax.set_ylabel("Product Name")
st.pyplot(fig)

st.dataframe(top_products.rename(columns={"Sales": "Total Revenue"}), use_container_width=True)

# -----------------------------
# CATEGORY PERFORMANCE
# -----------------------------
st.subheader("High-Value Categories")

category_sales = (
    filtered_df.groupby("Category", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
)

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(category_sales["Category"], category_sales["Sales"])
ax.set_title("Revenue by Category")
ax.set_xlabel("Category")
ax.set_ylabel("Revenue")
st.pyplot(fig)

st.dataframe(category_sales.rename(columns={"Sales": "Total Revenue"}), use_container_width=True)

# -----------------------------
# SUB-CATEGORY PERFORMANCE
# -----------------------------
st.subheader("Top Sub-Categories by Revenue")

subcat_sales = (
    filtered_df.groupby("Sub-Category", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
    .head(10)
)

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(subcat_sales["Sub-Category"][::-1], subcat_sales["Sales"][::-1])
ax.set_title("Top Sub-Categories by Revenue")
ax.set_xlabel("Revenue")
ax.set_ylabel("Sub-Category")
st.pyplot(fig)

# -----------------------------
# REGIONAL PERFORMANCE
# -----------------------------
st.subheader("Regional Performance")

region_sales = (
    filtered_df.groupby("Region", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
)

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(region_sales["Region"], region_sales["Sales"])
ax.set_title("Revenue by Region")
ax.set_xlabel("Region")
ax.set_ylabel("Revenue")
st.pyplot(fig)

st.dataframe(region_sales.rename(columns={"Sales": "Total Revenue"}), use_container_width=True)

# -----------------------------
# PROFIT BY CATEGORY
# -----------------------------
st.subheader("Profit by Category")

category_profit = (
    filtered_df.groupby("Category", as_index=False)["Profit"]
    .sum()
    .sort_values("Profit", ascending=False)
)

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(category_profit["Category"], category_profit["Profit"])
ax.set_title("Profit by Category")
ax.set_xlabel("Category")
ax.set_ylabel("Profit")
st.pyplot(fig)

# -----------------------------
# SEGMENT ANALYSIS
# -----------------------------
if "Segment" in filtered_df.columns:
    st.subheader("Revenue by Segment")

    segment_sales = (
        filtered_df.groupby("Segment", as_index=False)["Sales"]
        .sum()
        .sort_values("Sales", ascending=False)
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(segment_sales["Segment"], segment_sales["Sales"])
    ax.set_title("Revenue by Segment")
    ax.set_xlabel("Segment")
    ax.set_ylabel("Revenue")
    st.pyplot(fig)

# -----------------------------
# AUTO-GENERATED INSIGHTS
# -----------------------------
st.subheader("Auto-Generated Insights")

insights = []

best_category_row = category_sales.iloc[0]
insights.append(
    f"Highest revenue category is **{best_category_row['Category']}** with revenue of **{best_category_row['Sales']:,.2f}**."
)

best_region_row = region_sales.iloc[0]
insights.append(
    f"Top-performing region is **{best_region_row['Region']}** with revenue of **{best_region_row['Sales']:,.2f}**."
)

best_product_row = top_products.iloc[0]
insights.append(
    f"Top-selling product is **{best_product_row['Product Name']}** with revenue of **{best_product_row['Sales']:,.2f}**."
)

best_month_row = monthly_sales.sort_values("Sales", ascending=False).iloc[0]
insights.append(
    f"Best sales month is **{best_month_row['Year-Month']}** with revenue of **{best_month_row['Sales']:,.2f}**."
)

if total_profit < 0:
    insights.append("Overall profit is negative, which suggests serious profitability issues despite sales.")
else:
    insights.append(f"Overall business profit is **{total_profit:,.2f}**, indicating the business is profitable for the selected filters.")

for item in insights:
    st.write("- " + item)

# -----------------------------
# ACTIONABLE RECOMMENDATIONS
# -----------------------------
st.subheader("Actionable Recommendations")

recommendations = [
    "Focus marketing and inventory planning on top-selling products and highest revenue categories.",
    "Expand sales efforts in the best-performing region while investigating weaker regions for improvement opportunities.",
    "Review low-profit or high-discount categories to improve profitability.",
    "Use monthly trend analysis to plan promotions and stock for peak sales periods."
]

for rec in recommendations:
    st.write("- " + rec)

# -----------------------------
# DOWNLOAD CLEANED DATA
# -----------------------------
st.subheader("Download Cleaned Dataset")

output_df = filtered_df.copy()
csv_data = output_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download cleaned_sales_data.csv",
    data=csv_data,
    file_name="cleaned_sales_data.csv",
    mime="text/csv"
)
