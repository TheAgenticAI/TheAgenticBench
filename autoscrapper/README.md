# AutoScraper

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Features](#features)
- [Architecture](#architecture)
- [Agents Workflow](#agents-workflow)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Overview

AutoScraper is an agent-based system designed to automate browser interactions using a natural language interface. Built upon the [PydanticAI Python agent framework](https://github.com/pydantic/pydantic-ai), AutoScraper allows users to automate tasks such as form filling, product searches on e-commerce platforms, content retrieval, media interaction, and project management on various platforms. Its derived from the open source project Agent-E which is based on AutoGen.

## Quick Start

### Setup

To get started with AutoScraper, follow the steps below to install dependencies and configure your environment.

#### 1. Install `uv`

AutoScraper uses `uv` to manage the Python virtual environment and package dependencies.

- macOS/Linux:

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- Windows:

  ```bash
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

  You can install uv using pip

#### 2. Clone the repository:

    git clone https://github.com/TheAgenticAI/AutoScraper.git

#### 3. Set up the virtual environment

Use uv to create and activate a virtual environment for the project.

    uv venv --python=3.11
    source .venv/bin/activate
    # On Windows: .venv\Scripts\activate

#### 4. Install dependencies

    uv pip install -r requirements.txt

#### 5. Install Playwright Drivers

    playwright install

If you want to use your local Chrome browser over Playwright, go to chrome://version/ in Chrome, find the path to your profile, and set BROWSER_STORAGE_DIR to that path in .env

#### 6. Configure the environment

Create a .env file by copying the provided example file.

    cp .env.example .env

Edit the .env file and set the following variables:

    AUTOSCRAPER_TEXT_MODEL=
    AUTOSCRAPER_TEXT_API_KEY=
    AUTOSCRAPER_TEXT_BASE_URL=
    AUTOSCRAPER_SS_MODEL=
    AUTOSCRAPER_SS_API_KEY=
    AUTOSCRAPER_SS_BASE_URL=
    LOGFIRE_TOKEN=
    GOOGLE_API_KEY=
    GOOGLE_CX=
    BROWSER_STORAGE_DIR=

#### 7. Running the project

You can directly run the project from the main.py file or even spin up a server to interact through an API

- Direct
  ```bash
  python3 -m core.main
  ```
- API

  ```bash
  uvicorn core.server.api_routes:app --loop asyncio
  ```

  Details -

  ```
  POST http://127.0.0.1:8082/execute_task

  {
      "command": "Give me the price of RTX 3060ti on amazon.in and give me the latest delivery date."
  }
  ```

### Running API with Docker (for AgenticBench)

#### For Ubuntu/Windows :

```bash

docker build -t autoscraper .
docker run -it --net=host --env-file .env autoscraper

```

#### For macOS :

```bash

docker build -t autoscraper .
docker run -it -p 8082:8082 --env-file .env autoscraper

```

## Features

### Browser Automation

- **Web Form Filling**: Automatically fill web forms using user information or external data.
- **Product Search & Sort**: Search and sort e-commerce product listings (e.g., Amazon) based on criteria such as price or bestsellers.
- **Content Retrieval**: Retrieve specific data from websites (e.g., sports scores, contact info, historical data).
- **Web-Based Media Interaction**: Manage and interact with media on platforms like YouTube (e.g., playback, fullscreen, mute).
- **Web Search**: Perform broad internet searches on any topic, from restaurant recommendations to historical sites.
- **Project Management Automation**: Automate tasks on platforms like JIRA, such as filtering and managing issues.
- **Personal Shopping Assistance**: Suggest products based on user preferences and requirements.

## Architecture

![AutoScraper](https://github.com/user-attachments/assets/76c819dd-3e9b-4be2-8f66-5b682801bad3)

AutoScraper operates through three core agents:

- **Browser Agent**: Performs web actions such as navigating, interacting with page elements, and managing media.
- **Planner Agent**: Creates a base plan for tasks based on the user's input and previous actions.
- **Critique Agent**: Analyzes actions performed by the Browser Agent, provides feedback, and determines if the task has been completed successfully.

The agents work in a feedback loop to ensure that actions are taken correctly and tasks are completed effectively.

## Agents Workflow

### Step 1: Planner Agent

- The `Planner Agent` generates an initial plan based on the user's query and previous feedback.

### Step 2: Browser Agent

- The `Browser Agent` performs actions (like filling out forms or searching for products) within the browser.

### Step 3: Critique Agent

- The `Critique Agent` analyzes the browser actions, provides feedback, and informs the system if the task is complete.

### Step 4: Task Iteration

- This loop continues until the critique agent approves the completion of the task or gives feedback for re-execution of an action.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Agent-E](https://github.com/EmergenceAI/Agent-E?tab=readme-ov-file)
- [PydanticAI Python Agent Framework](https://github.com/pydantic/pydantic-ai)
