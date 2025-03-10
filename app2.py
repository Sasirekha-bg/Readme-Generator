import streamlit as st
import requests
import os
import shutil
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.groq import Groq

# Load environment variables
load_dotenv()

# Streamlit app
st.title("GitHub Repo Content Fetcher")

# User input for GitHub repo details
owner = st.text_input("GitHub Username", "Sasirekha-bg")
repo = st.text_input("Repository Name", "RESUME_BUILDER")

# User input for GitHub personal access token
github_token = st.text_input("GitHub Personal Access Token", type="password")
headers = {"Authorization": f"token {github_token}"} if github_token else {}

url = f"https://api.github.com/repos/{owner}/{repo}/contents/"

# Initialize session state for repo structure and file contents
if 'repo_structure' not in st.session_state:
    st.session_state.repo_structure = []
if 'file_contents' not in st.session_state:
    st.session_state.file_contents = {}
if 'readme_response' not in st.session_state:
    st.session_state.readme_response = ""

# Function to fetch and download files
def fetch_repo_contents(url, local_dir="repo_contents"):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        contents = response.json()
        os.makedirs(local_dir, exist_ok=True)

        for item in contents:
            if item['type'] == 'file':
                st.session_state.repo_structure.append(item['path'])
                file_response = requests.get(item['download_url'], headers=headers)
                if file_response.status_code == 200:
                    st.session_state.file_contents[item['path']] = file_response.text[:500]
                    file_path = os.path.join(local_dir, item['name'])
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(file_response.text)

            elif item['type'] == 'dir':
                new_local_dir = os.path.join(local_dir, item['name'])
                fetch_repo_contents(item['url'], new_local_dir)
    else:
        st.error(f"Failed to fetch repo contents: {response.status_code}")

if st.button("Fetch Repo Contents"):
    st.session_state.repo_structure = []
    st.session_state.file_contents = {}
    fetch_repo_contents(url)
    st.success("Repository contents fetched successfully!")

    readme_prompt = f"""
    I have a GitHub project called {repo}. Based on its structure and content, generate a well-structured README.md file.

    Project Structure:
    {os.linesep.join(st.session_state.repo_structure)}

    Key File Contents:
    {os.linesep.join(f'File: {path}\nContent: {content}' for path, content in st.session_state.file_contents.items())}

    README Sections:
    - Project Title
    - Description
    - Installation
    - Usage
    - Features
    - Folder Structure
    - Contributing
    - License

    Make sure the README is clear, professional, and easy for beginners to follow.
    """

    # Initialize agent
    agent = Agent(model=Groq(id="qwen-2.5-32b"))

    st.session_state.readme_response = agent.run(readme_prompt)

st.subheader("Generated README.md")
st.text_area("README.md", st.session_state.readme_response, height=400)

# Chat interface for tweaking README
st.subheader("Chat with the README Generator")
user_message = st.text_input("Ask a question or request a change:")
if st.button("Send") and user_message:
    agent = Agent(model=Groq(id="qwen-2.5-32b"))
    chat_response = agent.run(user_message)
    st.text_area("Agent Response", chat_response.content, height=200)

# Clean up repo_contents folder after use
if os.path.exists("repo_contents"):
    shutil.rmtree("repo_contents")
