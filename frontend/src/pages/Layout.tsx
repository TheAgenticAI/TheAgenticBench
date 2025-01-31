import {Header} from "@/components/navbar/Header";
import {AgentInfo} from "@/components/playground/AgentInfo";
import {Message} from "@/lib/types";
import {useState} from "react";
import {Chat} from "./Chat";
import Playground from "./Playground";
// import Sidebar from "../components/navbar/Sidebar";

const Layout = () => {
  const [messages, setMessages] = useState<Message[]>([]);

  return (
    <div className="h-full w-full flex flex-col">
      {/* 
      for future use
      <Sidebar /> 
      */}
      <Header setMessages={setMessages} />
      <div className="flex h-[93vh]">
        {messages && messages.length > 0 ? (
          <Chat messages={messages} setMessages={setMessages} />
        ) : (
          <Playground setMessages={setMessages} />
        )}
        <AgentInfo />
      </div>
    </div>
  );
};

export default Layout;
