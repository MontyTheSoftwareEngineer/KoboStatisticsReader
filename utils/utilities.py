import streamlit as st
import sqlite3
import pandas as pd
from utils.sqlite_utils import connect_to_database
from datetime import datetime, timedelta
import pytz
import tempfile

def create_reading_entries_ui(uploaded_file):
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite3") as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name

        try:
            # Display the book table for reference
            conn = connect_to_database(temp_file_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, pages FROM book")
            data = cursor.fetchall()

            if data:
                df_books = pd.DataFrame(data, columns=["Book ID", "Title", "Pages"])
                st.write("### Available Books")
                st.dataframe(df_books)
            else:
                st.warning("No books found in the database.")
        except sqlite3.Error as e:
            st.error(f"An error occurred while fetching book details: {e}")
            return
        finally:
            conn.close()

        # Input fields for the utility
        book_id = st.number_input("Enter Book ID:", min_value=1, step=1)
        start_date = st.text_input("Enter Start Date (MM/DD/YYYY):", value="01/01/2024")
        days = st.number_input("Enter Number of Days:", min_value=1, step=1)
        minutes_per_day = st.number_input("Enter Minutes Per Day:", min_value=1, step=1)
        pages_per_minute = st.number_input("Enter Pages Per Minute:", min_value=0.1, step=0.1)

        if st.button("Create Reading Entries"):
            result = create_reading_entries(temp_file_path, book_id, start_date, days, minutes_per_day, pages_per_minute)
            st.success(result)

            # Allow the user to download the updated file
            with open(temp_file_path, "rb") as updated_file:
                st.download_button(
                    label="Download Updated SQLite File",
                    data=updated_file,
                    file_name="updated_database.sqlite3",
                    mime="application/octet-stream",
                )

def create_reading_entries(file_path, book_id, start_date, days, minutes_per_day, pages_per_minute):
    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()

        # Fetch total pages for the book
        cursor.execute("SELECT pages FROM book WHERE id = ?", (book_id,))
        book = cursor.fetchone()

        if not book:
            return f"Book with ID {book_id} not found."

        total_pages = book[0]
        if not total_pages:
            return f"Book with ID {book_id} has no page count specified."

        current_page = 0
        est = pytz.timezone("US/Eastern")

        # Parse start date
        try:
            start_date_dt = datetime.strptime(start_date, "%m/%d/%Y")
            start_date_dt = est.localize(start_date_dt)
        except ValueError:
            return "Invalid date format. Please use MM/DD/YYYY."

        reading_sessions = []
        session_duration = 60
        total_minutes = minutes_per_day

        for day in range(days):
            day_start_time = start_date_dt + timedelta(days=day, hours=19, minutes=30)
            pages_to_read = int(pages_per_minute * total_minutes)

            for page in range(pages_to_read):
                current_page += 1
                if current_page > total_pages:
                    break

                session_time = day_start_time + timedelta(minutes=(page // pages_per_minute))
                epoch_time = int(session_time.timestamp())

                reading_sessions.append((book_id, current_page, epoch_time, session_duration, total_pages))

            if current_page >= total_pages:
                break

        if reading_sessions:
            cursor.executemany(
                "INSERT INTO page_stat_data (id_book, page, start_time, duration, total_pages) VALUES (?, ?, ?, ?, ?)",
                reading_sessions
            )
            conn.commit()
            return f"Inserted {len(reading_sessions)} entries for Book ID: {book_id}. Last Page Processed: {current_page}"
        else:
            return f"No entries created for Book ID: {book_id}. Already at the last page."

    except sqlite3.Error as e:
        return f"An error occurred: {e}"
    finally:
        if conn:
            conn.close()

def merge_books(file_path, source_id, target_id):
    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()

        # Reassign all associated data from source_id to target_id
        tables_to_update = ["page_stat_data"]  # List of tables with foreign key to book id
        for table in tables_to_update:
            cursor.execute(f"UPDATE {table} SET id_book = ? WHERE id_book = ?", (target_id, source_id))

        # Combine the reading stats from the source book into the target book
        cursor.execute("""
            UPDATE book
            SET total_read_time = COALESCE(total_read_time, 0) +
                                  (SELECT COALESCE(total_read_time, 0) FROM book WHERE id = ?),
                total_read_pages = COALESCE(total_read_pages, 0) +
                                   (SELECT COALESCE(total_read_pages, 0) FROM book WHERE id = ?)
            WHERE id = ?
        """, (source_id, source_id, target_id))

        # Remove the duplicate book entry
        cursor.execute("DELETE FROM book WHERE id = ?", (source_id,))

        conn.commit()
        return f"Successfully merged book ID {source_id} into book ID {target_id}."

    except sqlite3.Error as e:
        return f"An error occurred: {e}"
    finally:
        if conn:
            conn.close()

def merge_books_ui(uploaded_file):
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite3") as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name

        try:
            conn = connect_to_database(temp_file_path)
            cursor = conn.cursor()

            # Display the book table for reference
            cursor.execute("SELECT id, title, pages FROM book")
            data = cursor.fetchall()

            if data:
                df_books = pd.DataFrame(data, columns=["Book ID", "Title", "Pages"])
                st.write("### Available Books")
                st.dataframe(df_books)
            else:
                st.warning("No books found in the database.")

        except sqlite3.Error as e:
            st.error(f"An error occurred while fetching book details: {e}")
            return
        finally:
            conn.close()

        # Input fields for merging books
        source_id = st.number_input("Enter Source Book ID:", min_value=1, step=1)
        target_id = st.number_input("Enter Target Book ID:", min_value=1, step=1)

        if st.button("Merge Books"):
            if source_id == target_id:
                st.error("Source ID and Target ID must be different!")
            else:
                result = merge_books(temp_file_path, source_id, target_id)
                st.success(result)

                # Allow the user to download the updated file
                with open(temp_file_path, "rb") as updated_file:
                    st.download_button(
                        label="Download Updated SQLite File",
                        data=updated_file,
                        file_name="updated_database.sqlite3",
                        mime="application/octet-stream",
                    )

def utilities_ui():
    # Dropdown to select a utility
    utility = st.selectbox("Select a Utility:", ["Create Reading Entries", "Merge Books"])

    uploaded_file = st.file_uploader("Upload your SQLite3 file", type=["sqlite3", "db"], key="utilities_file_uploader")

    if utility == "Create Reading Entries":
        with st.expander("Create Reading Entries"):
            create_reading_entries_ui(uploaded_file)
    elif utility == "Merge Books":
        with st.expander("Merge Books"):
            merge_books_ui(uploaded_file)
