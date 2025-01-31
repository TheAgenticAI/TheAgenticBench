# TheAgentic | Bench

TheAgentic | Bench is a web application designed to manage and interact with various agents. This application provides a user-friendly interface to start new chats, view chat history, and interact with different registered agents.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Scripts](#scripts)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [License](#license)

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/TheAgenticAI/agentic-one-fe.git
   cd agentic-one-fe
   ```

2. Install dependencies:

   ```sh
   npm install
   ```

3. Create a `.env` file in the root directory and add the necessary environment variables.

## Usage

To start the development server, run:

```sh
npm run dev
```

The application will be available at `http://localhost:3000`.

## Scripts

- `dev`: Starts the development server.
- `build`: Builds the project for production.
- `lint`: Runs ESLint to check for linting errors.
- `preview`: Previews the production build.

## Project Structure

```
.gitignore
components.json
Dockerfile
eslint.config.js
index.html
package.json
postcss.config.js
README.md
src/
  App.css
  App.tsx
  assets/
  components/
    customUI/
      Accordion.tsx
      ...
    navbar/
    playground/
    ui/
  constants/
    agentInfo.tsx
    dashboard.tsx
    routes.ts
  index.css
  lib/
    types.ts
    utils.ts
  main.tsx
  pages/
    Chat.tsx
    Layout.tsx
    Playground.tsx
  vite-env.d.ts
tailwind.config.js
tsconfig.app.json
tsconfig.json
tsconfig.node.json
vite.config.ts
```

## Environment Variables

The application uses the following environment variables:

- `VITE_PRODUCT_LOGO`: URL for the product logo.
- `VITE_PRODUCT_ICON`: URL for the product icon.
- `VITE_PRODUCT_PAGE_TITLE`: Title for the product page.
- `VITE_WEBSOCKET_URL`: WebSocket URL for real-time communication.

## Docker

To create and run a Docker image for this application, follow these steps:

1. Build the Docker image:

   ```sh
   docker build --build-arg PRODUCT_LOGO=[your-logo] --build-arg PRODUCT_ICON=[your-favicon] --build-arg PRODUCT_PAGE_TITLE=[your-page-title] --build-arg WEBSOCKET_URL=[your-ws-link] -t agentic-bench-fe .
   ```

2. Run the Docker container:

   ```sh
   docker run -dp 3000:3000 agentic-bench-fe
   ```

The application will be available at `http://localhost:3000`.
