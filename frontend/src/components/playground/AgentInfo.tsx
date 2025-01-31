import {DUMMY_AGENTS} from "@/constants/agentInfo";
import {Box3dCenter} from "iconoir-react";
import {Dot} from "lucide-react";
import {AccordionGroup} from "../customUI/Accordion";

// for future versions
// import {ModelSelect} from "../customUI/ModelSelect";

export const AgentInfo = () => {
  return (
    <div className="w-1/5 flex flex-col border-l-2 p-6 space-y-6">
      <div className="space-y-2">
        <p className="text-muted-foreground">Connected Model</p>

        {/* 
        for future versions
        <ModelSelect models={DUMMY_MODELS} /> 
        */}
        <div className="relative flex flex-row items-center justify-between py-2 px-4 border-2 border-border rounded-md bg-input">
          <div className="flex flex-row items-center gap-2">
            <Box3dCenter />
            {process.env.MODEL_NAME}
          </div>
          <span className="absolute right-0 flex h-12 w-12 items-center justify-center">
            <Dot className="h-12 w-12 text-primary-success" />
          </span>
        </div>
      </div>
      <div className="space-y-2">
        <p className="text-muted-foreground">Agents</p>
        <AccordionGroup items={DUMMY_AGENTS} />
      </div>
    </div>
  );
};
