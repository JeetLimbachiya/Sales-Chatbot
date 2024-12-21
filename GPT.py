from dotenv import load_dotenv
import streamlit as st
import sqlite3
import google.generativeai as genai
import os
import re

# Load environment variables (if any)
load_dotenv()

# Configure the Gemini API key (replace with your actual API key)
genai.configure(api_key="AIzaSyBeSEPugvPSNEjEuLGOwnSPlG0KctT1kFI")

# Function to load Gemini model and provide SQL query based on a question
def get_gemini_response(question, prompt):
    model_name = 'gemini-1.5-flash'  # Use the correct model
    model = genai.GenerativeModel(model_name)
    response = model.generate_content([{"text": prompt[0]}, {"text": question}])  # Properly format the prompt and question
    return response.text.strip()  # Return the response as a cleaned-up string

# Function to clean up the SQL query (remove unwanted Markdown formatting)
def clean_sql_query(query):
    # Remove any Markdown-style formatting such as ```sql or other unwanted characters
    query = re.sub(r"```sql|```", "", query)  # Remove code block delimiters
    query = query.strip()  # Remove any leading/trailing spaces
    return query


# Function to retrieve and print the schema of the SQLite database
def get_database_schema(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Retrieve the list of tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    schema_info = {}

    # Iterate through tables and retrieve column names and data types
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()

        column_info = []
        for column in columns:
            column_info.append((column[1], column[2]))  # (Column name, Data type)

        schema_info[table_name] = column_info

    conn.close()
    return schema_info

# Function to execute the SQL query on the SQLite database
def read_sql_query(sql, db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    try:
        cursor.execute(sql)  # Execute the generated SQL query
        rows = cursor.fetchall()  # Fetch all rows of the result
        conn.commit()
        conn.close()
        return rows
    except Exception as e:
        conn.close()
        return f"Error executing SQL query: {str(e)}"

# Define prompt for the Gemini model
prompt = [
    """You are an expert in converting English questions to SQL queries! 
    The SQL database has a name 'E-commerce dataset.sqlite' and includes tables like 'customers', 
    'geolocation', 'leads_closed', 'leads_qualified', 'order_items', 'order_payments', 'order_reviews', 'orders', 
    'product_category_name_translation', 'products', and 'sellers'. 
    For example: 'How many entries of records are present in the customers table?' 
    The answer in SQL command will be something like: 'SELECT count(*) from customers;' also SQL should not have ''' in beginning or end sql word in output
    """
]

# Set up the Streamlit app
st.set_page_config(page_title="SQL Query Generator with Gemini")
st.header("Gemini App to Retrieve SQL Data")

# Input from the user
question = st.text_input("Input your question (e.g., 'How many records in the customers table?'):")

# Button to submit the question
submit = st.button("Ask the question")

# Display the database schema (for reference, optional)
#st.subheader("Database Schema")
#schema = get_database_schema("E-commerce dataset.sqlite")
#for table, columns in schema.items():
#    st.write(f"Table: {table}")
#    for col, dtype in columns:
#        st.write(f"  - {col}: {dtype}")

# When the submit button is clicked
if submit:
    if question:
        # Generate SQL query from the English question using the Gemini model
        generated_sql = get_gemini_response(question, prompt)

        # Clean the generated SQL query to remove unwanted characters
        cleaned_sql = clean_sql_query(generated_sql)

        # Log and display the cleaned SQL query for debugging purposes
        st.subheader("Generated SQL Query")
        st.write(generated_sql)  # Display the generated SQL query

        # Display the query before execution for debugging
        print("Cleaned SQL Query: ", cleaned_sql)  # This will print in your server logs

        # Execute the generated SQL query on the SQLite database
        results = read_sql_query(cleaned_sql, "E-commerce dataset.sqlite")

        st.subheader("Query Results:")
        if isinstance(results, str):  # If there's an error, display the message
            st.error(results)
        else:
            # Display the results in a readable format
            for row in results:
                st.write(row)

    else:
        st.warning("Please enter a question to generate the SQL query.")
