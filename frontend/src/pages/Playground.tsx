import {Button} from "@/components/ui/button";
import {DUMMY_PROMPTS} from "@/constants/dashboard";
import {Message} from "@/lib/types";
import {ArrowUpRight, SendSolid} from "iconoir-react";
import {useState} from "react";

const Playground = ({
  setMessages,
}: {
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
}) => {
  const [prompt, setPrompt] = useState<string>("");

  const handleSend = () => {
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
    setPrompt("");
  };

  return (
    <div className="w-4/5 flex flex-col items-center justify-center space-y-6">
      <div className="flex items-center flex-col ">
        <h2 className="text-2xl tracking-tight">
          Start the chat by providing a goal.
        </h2>
        <p className="text-2xl tracking-tight">Try the examples given below!</p>
      </div>

      {/* Input Box */}
      <div className="w-[70%] relative ">
        <input
          type="text"
          placeholder="Provide the goal ..."
          className="w-full px-4 py-3 bg-secondary border rounded-md pr-12 focus:outline-none placeholder:text-muted-foreground"
          value={prompt}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend();
          }}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <Button
          size="icon"
          className="absolute right-2 top-1/2 -translate-y-1/2 bg-secondary hover:bg-secondary"
          onClick={handleSend}
        >
          <SendSolid
            color={
              prompt.length > 0
                ? "hsl(var(--foreground))"
                : "hsl(var(--muted-foreground))"
            }
          />
        </Button>
      </div>

      {/* Example Cards */}
      <div className="grid grid-cols-3 gap-4 w-7/12 mt-8">
        {DUMMY_PROMPTS.map((example, index) => (
          <div
            key={index}
            className="p-4 rounded-md border bg-background hover:bg-secondary cursor-pointer"
            onClick={() => {
              setMessages((prev) => {
                return [
                  ...prev,
                  {
                    role: "user",
                    prompt: example,
                  },
                  {
                    role: "system",
                    data: [],
                  },
                ];
              });
            }}
          >
            <ArrowUpRight className="w-4 h-4 ml-auto opacity-100 transition-opacity mb-3" />
            <p className="text-sm">{example}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Playground;
