import os
from dataclasses import dataclass
import datetime

import streamlit as st
import psycopg2
from dotenv import load_dotenv

from annotated_text import annotated_text

load_dotenv()

st.set_page_config(
    page_title="Promptbase",
    page_icon="📝",
    layout="centered",
)

@dataclass
class Prompt:
    id: int = None
    title: str = ""
    prompt: str = ""
    is_favorite: bool = False
    created_at: datetime.datetime = None
    updated_at: datetime.datetime = None

def setup_database():
    con = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prompts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            prompt TEXT NOT NULL,
            is_favorite BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    con.commit()
    return con, cur

def create_prompt_form(cur):
    with st.form("new_prompt_form", clear_on_submit=True):
        st.subheader("Add New Prompt")
        title = st.text_input("Title")
        prompt_content = st.text_area("Prompt", height=200)
        is_favorite = st.checkbox("Favorite")

        submitted = st.form_submit_button("Submit")
        if submitted and title and prompt_content:
            cur.execute(
                "INSERT INTO prompts (title, prompt, is_favorite) VALUES (%s, %s, %s) RETURNING id",
                (title, prompt_content, is_favorite)
            )
            prompt_id = cur.fetchone()[0]
            st.success("Prompt added successfully!")
            con.commit()

def edit_prompt_form(cur, prompt_id):
    cur.execute("SELECT * FROM prompts WHERE id = %s", (prompt_id,))
    result = cur.fetchone()
    if result:
        prompt = Prompt(id=result[0], title=result[1], prompt=result[2], is_favorite=result[3], created_at=result[4], updated_at=result[5])
    else:
        st.error("Prompt not found.")
        return

    with st.form(f"edit_prompt_form_{prompt.id}"):
        st.write("Edit Prompt")
        title = st.text_input("Title", value=prompt.title)
        prompt_content = st.text_area("Prompt", height=200, value=prompt.prompt)
        is_favorite = st.checkbox("Favorite", value=prompt.is_favorite)

        submitted = st.form_submit_button("Update")
        if submitted and (title and prompt_content):
            cur.execute(
                "UPDATE prompts SET title = %s, prompt = %s, is_favorite = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (title, prompt_content, is_favorite, prompt.id)
            )
            st.success("Prompt updated successfully!")
            con.commit()
            del st.session_state['edit_prompt_id']  # Remove the edit state

def display_prompts(cur, search_query, order_by, descending, filter_option):
    st.subheader("Prompt List")
    search_clause = "%" + search_query + "%"
    order_clause = "DESC" if descending else "ASC"
    filter_clause = ""
    if filter_option == "Favorites":
        filter_clause = "AND is_favorite = TRUE"
    elif filter_option == "Non-favorites":
        filter_clause = "AND is_favorite = FALSE"

    cur.execute(
        f"""
        SELECT * FROM prompts 
        WHERE (title ILIKE %s OR prompt ILIKE %s)
        {filter_clause}
        ORDER BY {order_by} {order_clause}
        """, (search_clause, search_clause))
    prompts = cur.fetchall()

    for p in prompts:
        with st.expander(f"{p[1]}"):
            st.write(f"Prompt: {p[2]}")
            st.write(f"Favorite: {'Yes' if p[3] else 'No'}")
            if st.button("Edit", key=f"edit_{p[0]}"):
                st.session_state.edit_prompt_id = p[0]
                st.experimental_rerun()
            if st.button("Delete", key=f"delete_{p[0]}"):
                cur.execute("DELETE FROM prompts WHERE id = %s", (p[0],))
                con.commit()
                st.experimental_rerun()

            if 'edit_prompt_id' in st.session_state and st.session_state.edit_prompt_id == p[0]:
                edit_prompt_form(cur, p[0])

if __name__ == "__main__":
    st.title("Promptbase")
    annotated_text(("App", "", "#faf"), " | ", ("ChatGPT", "", "#8ef"), " | ", ("Prompt", "", "#fea"))
    st.markdown("""
            Welcome to my app, the ultimate tool for effortlessly storing and retrieving prompts. 
            Tailored for writers, educators, and creative minds, it provides a seamless way to organize and access your ideas with a user-friendly interface. 
            """)

    st.divider()

    con, cur = setup_database()

    with st.sidebar:
        st.header("Search, Sort, and Filter")
        search_query = st.text_input("Search Prompts")
        order_by = st.selectbox("Sort by", ["created_at","title"], index=0)
        descending = st.checkbox("Descending Order", value=True)
        filter_options = ["All", "Favorites", "Non-favorites"]
        filter_option = st.selectbox("Filter by/Show", filter_options, index=0)

    # Always show the create prompt form
    create_prompt_form(cur)
    st.divider()

    # Display existing prompts with edit/delete options
    display_prompts(cur, search_query, order_by, descending, filter_option)

    con.close()
