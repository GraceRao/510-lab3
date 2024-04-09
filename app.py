import os
from dataclasses import dataclass
import datetime

import streamlit as st
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Connect/establish to the database
con = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = con.cursor()

# Create the table
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

# Design the table
@dataclass
class Prompt:
    title: str
    prompt: str
    genre: str 
    is_favorite: bool = False
    id: int = None
    created_at: datetime.datetime = None # make this datetime type
    updated_at: datetime.datetime = None # make this datetime type

# Create a form to add a prompt
def prompt_form(prompt=Prompt(0,"", "", "", "")):
    """
    TODO: Add validation to the form, so that the title and prompt are required.
    """
    with st.form(key="prompt_form", clear_on_submit=True):
        title = st.text_input("Title", value=prompt.title)
        prompt_content = st.text_area("Prompt", height=200, value=prompt.prompt)
        is_favorite = st.checkbox("Favorite", value=prompt.is_favorite)

        submitted = st.form_submit_button("Submit")
        if submitted:
            return Prompt(title, prompt_content, is_favorite)

st.title("Promptbase")
st.subheader("A simple app to store and retrieve prompts")

# Add a prompt
prompt = prompt_form()
if prompt:
    cur.execute(
        "INSERT INTO prompts (title, prompt, is_favorite) VALUES (%s, %s, %s)", 
        (prompt.title, prompt.prompt, prompt.is_favorite)
    )
    con.commit()
    st.success("Prompt added successfully!")

# Prepare the data, alawyas fetch the data from the database
cur.execute("SELECT * FROM prompts")
prompts = cur.fetchall()

"""
prompts = [
    (1, "Title 1", "Prompt 1", True), p[0] -> id, p[1] -> "title1", p[2] -> "prompt1", p[3] -> True
    (2, "Title 2", "Prompt 2", True),
    (3, "Title 3", "Prompt 3", True),
]
"""

# TODO: Add a search bar
# TODO: Add a sort by date
# TODO: Add favorite button
for p in prompts:
    with st.expander(p[1]):
        st.code(p[2])
        # TODO: Add a edit function
        if st.button("Delete", key = p[0]):
            cur.execute("DELETE FROM prompts WHERE id = %s", (p[0],))
            con.commit()
            st.rerun()