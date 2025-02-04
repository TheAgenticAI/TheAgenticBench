For Adding your own custom client follow the below steps:

1. Refer to (https://ai.pydantic.dev/) for an overview of setting up agents and some predefined methods
2. Create your custom_agent file inside `/agentic_bench/agents`
3. Setup your Agent prompt defining in detail the use case, reasoning steps if any, and all the steps applicable.
   > Entire Agent workflow depends on the quality of prompt, so keep it as detailed and naive as possible
4. Create a class for your agent in the format:
   ```
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
6. If the agent has to handle complex tasks which might include certain tool calls, uncomment the `self._register_tools()` statement and configure the method with all the tools as below:
   ```
   def _register_tools(self):
        @self._agent.tool
        async def call_an_api(ctx:RunContext[CustomAgentDependency])-> <--A return data type expected from the tool-->:
           ......
       # Make sure to mention tool details within the prompt so agent knows when to use a tool while the execution
   ```
   > Refer to (https://ai.pydantic.dev/tools/) to understand tools in-depth
7. Configure a `generate_reply` function as below:
   ```
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
   
