export const DUMMY_AGENTS = [
  {
    title: "Orchestrator",
    content: "Manages task assignment to agents and controls flow.",
  },
  {
    title: "WebAgent",
    content:
      "Can access any web-page to extract information or perform actions.",
  },
  {
    title: "FileSurferAgent",
    content: "Can access files in file-system and perform actions.",
  },
  {
    title: "RAGAgent",
    content: "Agent specialized in using RAG to answer questions. Utilizes the existing data uploaded by user",
  },
  {
    title: "CoderAgent",
    content:
      "Writes code that is needed to transform data from other agents to complete user's query.",
  },
  {
    title: "CodeExecutorAgent",
    content: "Executes code from coder agent and handles errors/retries.",
  },
];
