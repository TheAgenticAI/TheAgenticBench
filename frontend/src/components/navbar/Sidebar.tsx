import {Button} from "@/components/ui/button";
import {PAGE_ROUTES} from "@/constants/routes";
import {
  ArrowUpRight,
  ChatBubbleEmptySolid,
  Github,
  OpenBook,
} from "iconoir-react";
import {useNavigate} from "react-router";
import {SidebarItem} from "./SidebarItem";

const {VITE_PRODUCT_LOGO} = import.meta.env;

const Sidebar = () => {
  const nav = useNavigate();

  return (
    <div className="flex flex-col h-screen w-1/6 border-r-2 ">
      {/* since logo was not given: till that time */}
      <div className="h-[8vh] flex items-center px-6 py-2">
        <img
          src={`${
            VITE_PRODUCT_LOGO ||
            "https://sg-ui-assets.s3.us-east-1.amazonaws.com/ta_bench_logo.svg"
          }`}
          style={{
            height: "6vh",
            maxWidth: "80%",
          }}
          alt={"TheAgentic | Bench logo"}
        />
      </div>
      <Button
        className="mx-4 mt-4 rounded-full flex items-center gap-2"
        onClick={() => nav(PAGE_ROUTES.home)}
      >
        <ChatBubbleEmptySolid
          color="hsl(var(--background))"
          className="mt-[-2px]"
        />
        <span className="text-base tracking-tight font-medium">New Chat</span>
      </Button>
      <div className="flex flex-col h-full justify-between p-4 pt-6">
        <div className="flex flex-col space-y-2">
          <p className="text-muted-foreground text-base">History</p>
        </div>
        <div className="flex flex-col space-y-2">
          <SidebarItem onClick={() => {}}>
            <OpenBook />
            <p className="text-base flex-1">Documentation</p>
            <ArrowUpRight />
          </SidebarItem>
          <SidebarItem onClick={() => {}}>
            <Github />
            <p className="text-base flex-1">Github</p>
            <ArrowUpRight />
          </SidebarItem>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
