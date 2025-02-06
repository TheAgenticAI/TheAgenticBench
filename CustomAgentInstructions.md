# Add Your Custom Agents
---


## For Adding your own custom agents, follow the steps mentioned below:

1. Refer to (https://ai.pydantic.dev/) for an overview of setting up agents and some predefined methods
2. Create your custom_agent file inside `/agentic_bench/agents`
3. Setup your Agent prompt defining in detail the use case, reasoning steps if any, and all the steps applicable.
   > Entire Agent workflow depends on the quality of prompt, so keep it as detailed and naive as possible
4. Create a class for your agent in the format:
   ```py
   class CustomAgent:
    def __init__(self,agent:Agent,name:str="CustomAgent",system_prompt:str=custom_agent_prompt)-> None:
        try:
            self._agent:Agent=agent
            self.name:str=name
            self.description="An agent that performs this custom operation"
            self._system_prompt:str=system_prompt
            self.websocket:Optional[WebSocket]=None
            self.stream_output: Optional[StreamResponse] = None
            # self._register_tools()

        except Exception as e:
            print(str(e))

   # Configure your Agent Name, description and its system prompt
   ```
5. [Optional] Refer to (https://ai.pydantic.dev/dependencies/) & (https://ai.pydantic.dev/results/) to understand about Agent dependencies and results and configure if required. 
6. [Optional] If the agent has to handle complex tasks which might include certain tool calls, uncomment the `self._register_tools()` statement and configure the method with all the tools as below:
   ```py
   def _register_tools(self):
        @self._agent.tool
        async def call_an_api(ctx:RunContext[CustomAgentDependency])-> <--A return data type expected from the tool-->:
           ......
       # Make sure to mention tool details within the prompt so agent knows when to use a tool while the execution
   ```
   > Refer to (https://ai.pydantic.dev/tools/) to understand tools in-depth
7. Configure a `generate_reply` function as below:
   ```py
   async def generate_reply(
        self, user_message: str, deps: CustomAgentDependency,websocket:WebSocket,
                    stream_output:StreamResponse
    ) -> Tuple[bool, str, List[ModelMessage]]:
         self.websocket = websocket
         self.stream_output = stream_output
         ....
         ....
         result = await self._agent.run(user_message, deps=deps) #This calls your agent and the execution begins. Handle the response and format the output before returning
         if hasattr(result, "data"):
                content = (
                    str(result.data.content)
                    if hasattr(result.data, "content")
                    else str(result.data)
                ) #Assuming you have configured pydantic_ai results type and have content param within the class. You can skip this if no result_type defined for the Agent

                # Build properly formatted response
                response += f"content='{content}'"

                return True, response, result.all_messages()
            else:
                return False, "No data in result", []
   


   # This is the entry method of the agent hence we initialize the websocket and the format of streaming responses in this method
   # You can skip the Dependency if not already configured
   ```
8. Go to the `orchestrator.py` and include your agent in the below sections:
   - Import the relevant functions and your agent class previously configured just like done below
      ```py
      from agents.file_surfer import FileSurfer, FileToolDependencies, RequestsMarkdownBrowser
      from agents.web_surfer import WebSurfer
      from agents.coder_agent import (
          CoderAgent, CoderDependencies, Executor, ExecutorDependencies,
          DockerCodeExecutor, LocalCodeExecutor, CoderResult, coder_system_message
      )
      from agents.rag_agent import RAGAgent, RAGDependencies
      ```
   - Include your agent in the init block of the System Orchestrator
     ```py
     class SystemOrchestrator:
     def __init__(self):
        self.agents: List[Union[FileSurfer, CoderAgent, Executor, WebSurfer, RAGAgent]] = []
     ```
   - Include your agent in the initialize_agents return List as below
     ```py
     async def initialize_agents(self) -> List[Union[FileSurfer, CoderAgent, Executor, WebSurfer, RAGAgent]]:
     ```
   - Initialize the agent within the initialize_agents in a similar manner.
     ```py
     file_surfer = Agent(
                model=self.model,
                name="File Surfer Agent"
            )
     file_surfer_agent = FileSurfer(
          agent=file_surfer
      )
     ```
   - [Optional] In case your agent includes dependencies as well, you can follow this snippet
     ```py
      self.coder_deps = CoderDependencies(
                description=coder_description,
                system_messages=coder_system_message,
                request_terminate=False
            )

      cod_agent = Agent(
          model=self.model,
          name="Coder Agent",
          deps_type=CoderDependencies,
          result_type=CoderResult
      )
      coder_agent = CoderAgent(
          agent=cod_agent,
          system_prompt=coder_system_message
      )
     ```
   - Include your agent within the execute_agent_instruction function definition just as below
     ```py
      async def execute_agent_instruction(self, agent: Union[FileSurfer, CoderAgent, Executor, WebSurfer, RAGAgent], instruction: str) -> AgentExecutionResult:
        """Execute agent instruction with robust error handling using generate_reply"""
     ```
   - Write your agent execution snippet or the entry point to your agent in a similar manner
     ```py
      if isinstance(agent, CoderAgent):
             success, response, messages = await agent.generate_reply(
                 user_message=instruction,
                 deps=self.coder_deps,websocket=self.websocket,
                 stream_output=self.stream_output
             )
     ```
   - Include your agent within the return block of _get_agent_by_name in a similar manner
     ```py
      def _get_agent_by_name(self, name: str) -> Optional[Union[FileSurfer, CoderAgent, Executor, WebSurfer, RAGAgent]]:
     ```

9. Now configure websocket so as to realtime stream your agent actions to the UI
   - Setup the intermediate steps you want to stream realtime. Include this snippet and tweak it as per your use case at every part which might be relevant to be shown in the UI
     ```py
     if self.stream_output and self.websocket:
            self.stream_output.steps.append(
                event_data["message"]
            )
            await self.websocket.send_text(
                json.dumps(asdict(self.stream_output))
            )
     ```
   
   
   
   
   
