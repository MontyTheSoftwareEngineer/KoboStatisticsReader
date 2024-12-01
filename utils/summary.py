import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from utils.sqlite_utils import connect_to_database
import tempfile
from datetime import datetime

def generate_summary():
    # File upload widget with a unique key
    uploaded_file = st.file_uploader("Upload your SQLite3 file", type=["sqlite3", "db"], key="summary_file_uploader")

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name

        conn = connect_to_database(temp_file_path)

        try:
            # Query for books read summary
            cursor = conn.cursor()
            query = """
                SELECT 
                    b.title AS book_title,
                    COUNT(DISTINCT psd.page) AS total_pages_read,
                    SUM(psd.duration) AS total_time_seconds
                FROM page_stat_data psd
                JOIN book b ON psd.id_book = b.id
                GROUP BY b.title
                ORDER BY total_pages_read DESC;
            """
            cursor.execute(query)
            data = cursor.fetchall()

            # Create DataFrame for books read
            df_books = pd.DataFrame(data, columns=["Book Title", "Total Pages Read", "Total Time (seconds)"])
            df_books["Total Time (hours)"] = df_books["Total Time (seconds)"] / 3600
            df_books["Average Reading Speed (pages/hour)"] = (
                df_books["Total Pages Read"] / df_books["Total Time (hours)"]
            ).round(2)

            # Display Summary
            st.write("### Books Read Summary")
            st.dataframe(df_books[["Book Title", "Total Pages Read", "Average Reading Speed (pages/hour)"]])

            # Graph: Pages Read Per Book
            st.write("### Pages Read Per Book")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh(df_books["Book Title"], df_books["Total Pages Read"], color="skyblue")
            ax.set_xlabel("Total Pages Read")
            ax.set_ylabel("Book Title")
            ax.set_title("Pages Read Per Book")
            st.pyplot(fig)

            # Graph: Average Reading Speed Per Book
            st.write("### Average Reading Speed (pages/hour)")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(df_books["Book Title"], df_books["Average Reading Speed (pages/hour)"], color="lightgreen")
            ax.set_xticklabels(df_books["Book Title"], rotation=45, ha="right")
            ax.set_xlabel("Book Title")
            ax.set_ylabel("Reading Speed (pages/hour)")
            ax.set_title("Average Reading Speed by Book")
            st.pyplot(fig)

            # Query for "Year in Review"
            year = datetime.now().year
            query = f"""
                SELECT 
                    strftime('%m', datetime(psd.start_time, 'unixepoch', 'localtime')) AS month,
                    COUNT(DISTINCT b.title) AS books_read
                FROM page_stat_data psd
                JOIN book b ON psd.id_book = b.id
                WHERE strftime('%Y', datetime(psd.start_time, 'unixepoch', 'localtime')) = '{year}'
                GROUP BY month
                ORDER BY month;
            """
            cursor.execute(query)
            data = cursor.fetchall()

            # Create DataFrame for "Year in Review"
            df_year = pd.DataFrame(data, columns=["Month", "Books Read"])
            df_year["Month"] = df_year["Month"].astype(int)  # Convert months to integers for sorting

            # Graph: Year in Review
            st.write("### Year in Review: Books Read Per Month")
            if not df_year.empty:
                df_year = df_year.set_index("Month").reindex(range(1, 13), fill_value=0)  # Fill missing months
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.bar(df_year.index, df_year["Books Read"], color="lightcoral")
                ax.set_xticks(range(1, 13))
                ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
                ax.set_xlabel("Month")
                ax.set_ylabel("Books Read")
                ax.set_title(f"Books Read in {year}")
                st.pyplot(fig)
            else:
                st.write("No books read in the current year.")

        except sqlite3.Error as e:
            st.error(f"An error occurred: {e}")
        finally:
            conn.close()