import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="AI Ecommerce Insights Assistant", layout="wide")

st.title("🧠 AI-Powered Ecommerce Insights Assistant")

st.markdown("""
Upload your sales CSV file to generate business KPIs,
SQL-based aggregations, and AI-driven growth recommendations.
""")

# -----------------------------
# Mock AI Layer (Stable Version)
# -----------------------------
def mock_ai_response(summary, question=None):
    if question:
        return f"""
📊 Based on the sales data:

- Revenue appears concentrated on top-performing SKUs.
- Consider diversifying revenue sources.
- Monitor low-performing products for pricing or bundling strategies.

📝 Answer to your question:
{question}

Based on current summary metrics, total sales performance depends largely on the top SKU contribution.
"""
    else:
        return """
🚀 AI Growth Insights:

1. Increase marketing spend on top-performing products.
2. Introduce bundles for low-performing SKUs.
3. Run pricing experiments for mid-tier products.
4. Monitor revenue concentration risk.
5. Improve inventory planning for high-demand items.
"""

# -----------------------------
# File Upload
# -----------------------------
uploaded_file = st.file_uploader("📂 Upload Sales CSV", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.subheader("🔍 Data Preview")
    st.dataframe(df.head())

    # -----------------------------
    # KPI Calculations
    # -----------------------------
    total_revenue = df["Revenue"].sum()
    avg_revenue = df["Revenue"].mean()
    top_product = df.groupby("Product")["Revenue"].sum().idxmax()
    lowest_product = df.groupby("Product")["Revenue"].sum().idxmin()

    st.subheader("📊 Business KPIs")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Revenue", f"₹ {total_revenue:,.2f}")
    col2.metric("Average Revenue", f"₹ {avg_revenue:,.2f}")
    col3.metric("Top Product", top_product)
    col4.metric("Lowest Product", lowest_product)

    summary = f"""
    Total Revenue: {total_revenue}
    Average Revenue: {avg_revenue}
    Top Product: {top_product}
    Lowest Product: {lowest_product}
    """

    # -----------------------------
    # SQL Integration Layer
    # -----------------------------
    conn = sqlite3.connect("sales.db")
    df.to_sql("sales_data", conn, if_exists="replace", index=False)

    query = """
    SELECT Product, SUM(Revenue) as Total_Revenue
    FROM sales_data
    GROUP BY Product
    ORDER BY Total_Revenue DESC
    """

    sql_df = pd.read_sql(query, conn)

    st.subheader("🗄 SQL Aggregated Results")
    st.dataframe(sql_df)

    # -----------------------------
    # AI Insights Button
    # -----------------------------
    st.subheader("🤖 AI Business Insights")

    if st.button("Generate AI Growth Recommendations"):
        st.write(mock_ai_response(summary))

    # -----------------------------
    # AI Business Chat
    # -----------------------------
    st.subheader("💬 Ask Business Questions")

    user_question = st.text_input("Ask about the sales performance")

    if user_question:
        st.write(mock_ai_response(summary, user_question))

    # -----------------------------
    # Architecture Overview
    # -----------------------------
    st.markdown("---")
    st.subheader("🏗 Architecture Overview")

    st.markdown("""
    **1️⃣ Data Ingestion Layer**  
    - CSV Upload  

    **2️⃣ Processing Layer**  
    - Pandas transformations  
    - KPI extraction  

    **3️⃣ SQL Layer**  
    - SQLite aggregation queries  

    **4️⃣ AI Reasoning Layer**  
    - LLM-style recommendation engine (mocked for stability)  

    This architecture demonstrates how structured data can be combined with AI reasoning
    to support business decision-making.
    """)



# import streamlit as st
# import google.generativeai as genai
# import pandas as pd

# # Replace with your API key
# genai.configure(api_key="0") ## paste ur key

# #model = genai.GenerativeModel("models/gemini-1.5-flash")
# model = genai.GenerativeModel("gemini-1.5-flash")

# st.title("AI Ecommerce Insights Assistant")

# uploaded_file = st.file_uploader("Upload Sales CSV", type=["csv"])

# if uploaded_file:
#     df = pd.read_csv(uploaded_file)
#     st.write("Data Preview:")
#     st.dataframe(df.head())

#     total_revenue = df["Revenue"].sum()
#     avg_revenue = df["Revenue"].mean()
#     top_product = df.groupby("Product")["Revenue"].sum().idxmax()
#     lowest_product = df.groupby("Product")["Revenue"].sum().idxmin()

#     st.subheader("Business Metrics")
#     st.write("Total Revenue:", total_revenue)
#     st.write("Average Revenue:", avg_revenue)
#     st.write("Top Product:", top_product)
#     st.write("Lowest Performing Product:", lowest_product)

#     summary = f"""
#     Total Revenue: {total_revenue}
#     Average Revenue: {avg_revenue}
#     Top Product: {top_product}
#     Lowest Product: {lowest_product}
#     """
#     st.subheader("Ask Business Questions")
#     user_question = st.text_input("Ask about the sales data")

#     if user_question:
#         chat_response = model.generate_content(
#         f"You are a business analyst. Based on this sales summary:\n{summary}\nAnswer this question:\n{user_question}"
#         )
#         st.write(chat_response.text)



#     if st.button("Generate AI Insights"):
#         response = model.generate_content(
#             f"You are an ecommerce growth consultant. Based on this sales summary, give growth strategies, pricing suggestions, and inventory recommendations:\n{summary}"
#         )
#         st.write(response.text)
    

