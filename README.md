<p align="center">
  <img src="assets/ta_bench_logo.svg" alt="Agentic Bench Logo" width="200"/>
</p>

# agentic-bench

An extendable multi-agent framework for web scraping, code generation, code execution, file access, RAG and much more!
List of existing agents:
- Web Surfer
- File Access
- RAG Agent
- Code Generator
- Code Executor
- Web Scraper (TheAgenticBrowser)

## Quick Start

### To use host networking in docker compose, follow these steps if using Docker Desktop as per docker website (https://docs.docker.com/engine/network/drivers/host/):

- Sign in to your Docker account in Docker Desktop.
- Navigate to Settings.
- Under the Resources tab, select Network.
- Check the Enable host networking option.
- Select Apply and restart.

```bash
git clone --recurse-submodules https://github.com/TheAgenticAI/agentic-bench.git
docker compose up
```

## License

This project is licensed under the [Agentic Community License Agreement](LICENSE).
