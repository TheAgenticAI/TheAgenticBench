from core.orchestrator import Orchestrator
import asyncio  # Add this import

async def main():
    orchestrator = Orchestrator()
    await orchestrator.start()

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())