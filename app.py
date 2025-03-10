import streamlit as st
import requests
import os
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

# Structure to hold repo details
repo_structure = []
file_contents = {}

# Function to fetch and download files
def fetch_repo_contents(url, local_dir="repo_contents"):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        contents = response.json()
        os.makedirs(local_dir, exist_ok=True)

        for item in contents:
            if item['type'] == 'file':
                repo_structure.append(item['path'])
                file_response = requests.get(item['download_url'], headers=headers)
                if file_response.status_code == 200:
                    file_contents[item['path']] = file_response.text[:500]
                    file_path = os.path.join(local_dir, item['name'])
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(file_response.text)

            elif item['type'] == 'dir':
                new_local_dir = os.path.join(local_dir, item['name'])
                fetch_repo_contents(item['url'], new_local_dir)
    else:
        st.error(f"Failed to fetch repo contents: {response.status_code}")

if st.button("Fetch Repo Contents"):
    fetch_repo_contents(url)
    st.success("Repository contents fetched successfully!")

    readme_prompt = f"""
    I have a GitHub project called {repo}. Based on its structure and content, generate a well-structured README.md file.

    Project Structure:
    {os.linesep.join(repo_structure)}

    Key File Contents:
    {os.linesep.join(f'File: {path}\nContent: {content}' for path, content in file_contents.items())}

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

    st.subheader("Generated README.md")
    response = agent.run(readme_prompt)
    st.text_area("README.md", response.content, height=800)
