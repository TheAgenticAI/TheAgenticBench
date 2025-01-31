import {CodeBlock} from "@/components/customUI/CodeBlock";
import {PromptInput} from "@/components/customUI/PromptInput";
import {TerminalBlock} from "@/components/customUI/TerminalBlock";
import {Card} from "@/components/ui/card";
import {ScrollArea} from "@/components/ui/scroll-area";
import {Message, SystemMessage} from "@/lib/types";
import {BrainElectricity, Pin, User} from "iconoir-react";
import {useEffect, useRef, useState} from "react";

import Markdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import remarkBreaks from "remark-breaks";

import {ErrorAlert} from "@/components/customUI/ErrorAlert";
import Loading from "@/components/customUI/Loading";
import useWebSocket, {ReadyState} from "react-use-websocket";

const {VITE_WEBSOCKET_URL} = import.meta.env;

const OrchestratorHeader = () => {
  return (
    <div className="flex items-center gap-6">
      <div className="flex items-center justify-center bg-secondary border h-6 w-6 rounded-sm">
        <svg
          width="16"
          height="9"
          viewBox="0 0 16 9"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M1 9V5.36364C1 2.95367 2.79067 1 5 1H8H11C13.2093 1 15 2.95367 15 5.36364V9"
            stroke="#39B552"
            stroke-width="2"
          />
        </svg>
      </div>
      <span className="text-base break-words">Orchestrator Agent</span>
    </div>
  );
};

export const Chat = ({
  messages,
  setMessages,
}: {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
}) => {
  const [prompt, setPrompt] = useState<string>("");

  const scrollItem = useRef<HTMLDivElement | null>(null);

  const [loading, setLoading] = useState<boolean>(false);

  const {sendMessage, lastJsonMessage, readyState} = useWebSocket(
    VITE_WEBSOCKET_URL,
    {
      onOpen: () => {
        if (messages[0]?.prompt && messages[0].prompt.length > 0)
          sendMessage(messages[0].prompt);
      },
      onError: () => {
        setLoading(false);
      },
    }
  );

  const scrollToBottom = () => {
    if (scrollItem.current) {
      const lastElement = scrollItem.current?.lastChild as HTMLElement;

      lastElement?.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }
  };

  useEffect(() => {
    // call this function when the data is received from the API. It will stream the data to the chat UI
    // const handleDataReceivedFromAPI = (item: SystemMessage) => {

    setMessages((prev) => {
      console.log(lastJsonMessage);

      const lastMessage = prev[prev.length - 1];
      if (lastJsonMessage && lastMessage?.role === "system") {
        setLoading(true);

        const lastMessageData = lastMessage.data || [];
        const {agent_name, instructions, steps, output, status_code} =
          lastJsonMessage as SystemMessage;
        // find the agent name in the last message data and update the fields
        const agentIndex = lastMessageData.findIndex(
          (agent) => agent.agent_name === agent_name
        );
        if (agentIndex !== -1) {
          lastMessageData[agentIndex] = {
            agent_name,
            instructions,
            steps,
            output,
            status_code,
          };
        } else {
          lastMessageData.push({
            agent_name,
            instructions,
            steps,
            output,
            status_code,
          });
        }

        if (agent_name === "Orchestrator" && output.length > 0) {
          setLoading(false);
        }
      }
      return [...prev];
    });
    // };
  }, [lastJsonMessage, setMessages]);

  const addUserChat = () => {
    // Once the user sends a message, add it to the chat
    // Also add the system message
    // Hit the API to get the response
    // Append the response into the latest system message array
    if (prompt === "") return;
    setMessages((prev) => {
      return [
        ...prev,
        {
          role: "user",
          prompt: prompt,
        },
        {
          role: "system",
          data: [],
        },
      ];
    });

    //sends message to websocket server
    sendMessage(prompt);
    //clears the prompt
    setPrompt("");
  };

  useEffect(() => {
    scrollToBottom();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const getOutputBlock = (type: string, output: string | undefined) => {
    switch (type) {
      case "Coder Agent":
        return <CodeBlock content={output || ""} />;
      case "Code Executor Agent":
        return <TerminalBlock content={output || ""} />;
      case "Executor Agent":
        return <TerminalBlock content={output || ""} />;

      default:
        return (
          <span className="text-base break-words">
            <Markdown
              remarkPlugins={[remarkBreaks]}
              rehypePlugins={[rehypeRaw]}
            >
              {output}
            </Markdown>
          </span>
        );
    }
  };

  return (
    <div className="flex flex-col h-full w-4/5 ">
      {/* Refer to the scrollarea issue: https://github.com/shadcn-ui/ui/issues/2090 */}
      <ScrollArea className="flex-1 py-10 [&>div>div[style]]:!block">
        {readyState === ReadyState.CONNECTING ? (
          <div className="flex items-center justify-center">
            <Loading size="md" />
          </div>
        ) : (
          <div ref={scrollItem} className="flex flex-col items-center gap-6">
            {messages.map((chat, index) => (
              <div key={index} className="w-[75%]">
                {chat?.role === "user" ? (
                  <div className="flex gap-6 text-white items-start">
                    <div className="bg-green-600 p-1 rounded-sm flex items-center justify-center">
                      <User />
                    </div>
                    <span className="text-base">{chat?.prompt}</span>
                  </div>
                ) : (
                  <div className="flex flex-col gap-4">
                    <OrchestratorHeader />
                    <div className="ml-12 w-[90%]">
                      {chat.data?.map((systemMessage, index) =>
                        systemMessage.agent_name === "Orchestrator" ? (
                          <div className="space-y-5 bg-background mb-4 max-w-full">
                            <div className="flex flex-col gap-3 text-gray-300">
                              {systemMessage.steps.map((text, i) => (
                                <div
                                  key={i}
                                  className="flex gap-2 text-gray-300 items-start"
                                >
                                  <div className="h-4 w-4 flex-shrink-0 mt-[0.15rem]">
                                    <Pin />
                                  </div>
                                  <span className="text-base break-words">
                                    {text}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <Card
                            key={index}
                            className="p-4 bg-background pr-12 mb-4 max-w-full"
                          >
                            <div className="bg-secondary border flex items-center gap-2 mb-4 px-3 py-1 rounded-md w-max">
                              <BrainElectricity />
                              <span className="text-white text-base">
                                {systemMessage.agent_name}
                              </span>
                            </div>
                            <div className="space-y-3 px-2">
                              <div className="flex flex-col gap-2 text-gray-300">
                                <span className="text-base break-words">
                                  {systemMessage.instructions}
                                </span>
                              </div>
                              <div className="flex flex-col gap-2 text-gray-300">
                                <p className="text-muted-foreground text-base">
                                  Steps:
                                </p>
                                {systemMessage.steps.map((text, i) => (
                                  <div
                                    key={i}
                                    className="flex gap-2 text-gray-300 items-start"
                                  >
                                    <div className="h-4 w-4 flex-shrink-0 mt-[0.15rem]">
                                      <Pin />
                                    </div>
                                    <span className="text-base break-words">
                                      <Markdown rehypePlugins={[rehypeRaw]}>
                                        {text}
                                      </Markdown>
                                    </span>
                                  </div>
                                ))}
                              </div>
                              {systemMessage.output && (
                                // systemMessage.agent_name !== "Orchestrator" &&
                                <div className="flex flex-col gap-2 text-gray-300">
                                  <p className="text-muted-foreground text-base">
                                    Output:
                                  </p>
                                  {getOutputBlock(
                                    systemMessage.agent_name,
                                    systemMessage.output
                                  )}
                                </div>
                              )}
                            </div>
                          </Card>
                        )
                      )}
                      {/* Add output of the orchestrator */}
                      {chat.data?.find(
                        (systemMessage) =>
                          systemMessage.agent_name === "Orchestrator"
                      )?.output && (
                        <div className="space-y-3">
                          {chat.data?.find(
                            (systemMessage) =>
                              systemMessage.agent_name === "Orchestrator"
                          )?.status_code === 200 ? (
                            <div className="flex flex-col gap-2 text-gray-300">
                              <p className="text-muted-foreground text-base">
                                Summary:
                              </p>
                              {getOutputBlock(
                                "Orchestrator",
                                chat.data?.find(
                                  (systemMessage) =>
                                    systemMessage.agent_name === "Orchestrator"
                                )?.output
                              )}
                            </div>
                          ) : (
                            <ErrorAlert
                              errorMessage={
                                chat.data?.find(
                                  (systemMessage) =>
                                    systemMessage.agent_name === "Orchestrator"
                                )?.output
                              }
                            />
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="ml-12 w-[75%]">
                <Loading size="md" />
              </div>
            )}
          </div>
        )}
      </ScrollArea>

      <div className="relative my-4 mx-auto w-[75%]">
        <PromptInput
          disable={loading}
          task={prompt}
          setTask={setPrompt}
          sendTask={addUserChat}
        />
      </div>
    </div>
  );
};
