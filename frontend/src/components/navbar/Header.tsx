import {
  ArrowUpRight,
  ChatBubbleEmptySolid,
  Github,
  OpenBook,
} from "iconoir-react";
import { Button } from "../ui/button";
import { SidebarItem } from "./SidebarItem";
import { Message } from "@/lib/types";

const { VITE_PRODUCT_LOGO } = import.meta.env;

export const Header = ({
  setMessages,
}: {
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
}) => {
  return (
    <div className="h-[7vh] flex items-center justify-between px-7 border-b-2 text-primary">
      {/* <h1 className="text-lg text-primary-success">Playground</h1> */}
      <img
        src={`${
          VITE_PRODUCT_LOGO ||
          "https://sg-ui-assets.s3.us-east-1.amazonaws.com/ta_bench_logo.svg"
        }`}
        style={{
          height: "5vh",
          maxWidth: "20%",
        }}
        alt={"TheAgentic | Bench logo"}
      />
      <div className="flex items-center gap-3">
        <Button
          className="rounded-full flex items-center gap-2"
          onClick={() => setMessages([])}
          size="sm">
          <ChatBubbleEmptySolid
            color="hsl(var(--background))"
            className="mt-[-2px]"
          />
          <span className="text-base tracking-tight font-medium">New Chat</span>
        </Button>
        <SidebarItem
          onClick={() =>
            window.open(
              "https://github.com/TheAgenticAI/agentic-one-fe",
              "_blank"
            )
          }>
          <OpenBook />
          <p className="text-base flex-1">Documentation</p>
          <ArrowUpRight />
        </SidebarItem>
        <SidebarItem
          onClick={() =>
            window.open(
              "https://github.com/TheAgenticAI/agentic-one-fe",
              "_blank"
            )
          }>
          <Github />
          <p className="text-base flex-1">Github</p>
          <ArrowUpRight />
        </SidebarItem>
      </div>
    </div>
  );
};

