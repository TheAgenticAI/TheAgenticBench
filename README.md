<p align="center">
  <img src="assets/ta_bench_logo.svg" alt="Agentic Bench Logo" width="200"/>
</p>

# Agentic Bench

## Table of Contents
- [Overview](#Overview)
- [List of existing agents](#List-of-existing-agents)
- [Quick Start](#Quick-Start)
- [License](#License)

## Overview
An extendable digital worker framework for web scraping, code generation, code execution, file access, RAG and much more!
Build, customize, and deploy dynamic workflows—from research to business process automation with pre-built AI agents and custom options. All operated via a natural language interface.

## List of existing agents:
- **Orchestrator Agent**: Takes the initial prompt, generates an action plan, and decides on the action control what agent performs what task, and in what order, to get to the final solution. This can be thought of as the parent agent.
- **Web Agent** ([TheAgenticBrowser](https://github.com/TheAgenticAI/TheAgenticBrowser)): Can access any web-page to extract information or perform actions.
- **Local File Agent**: Can download files from browser, perform actions on file-system.
- **RAG Agent**: An AI assistant specialized in using RAG to answer questions. Utilizes the existing data uploaded by user.
- **Code Generator Agent**: Writes code to perform any action or algorithm or process other agent's response
- **Code Executor Agent**: Executes code from coder agent with automated dependencies installation and runtime inputs.
- **API Agent**: Agent for executing REST API calls.

## Quick Start
### Docker Setup
- Clone the Agentic Bench repo including the submodules (Agentic Browser)
  ```
  git clone --recurse-submodules https://github.com/TheAgenticAI/agentic-bench.git
  ```
- Setup the environment variables
  ```
  cp example.env .env
  ```
- [Additional Step] (Only for Docker Desktop)
  > Ref: https://docs.docker.com/engine/network/drivers/host/ 
  - Sign in to your Docker account in Docker Desktop.
  - Navigate to Settings.
  - Under the Resources tab, select Network.
  - Check the Enable host networking option.
  - Select Apply and restart.

    
- Run all docker configuration
  ```
  docker-compose up
  ```
- Access the services
  ```
  Frontend: (http://localhost:3000)
  Agentic Bench: (http://localhost:8081) or (http://localhost:8081/docs to access the APIs)
  Agentic Browser: (http:localhost:8000) or (http://localhost:8000/docs to access the APIs)
  ```

## License

This project is licensed under the [Agentic Community License Agreement](LICENSE).
