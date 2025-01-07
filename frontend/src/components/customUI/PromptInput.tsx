import {Button} from "@/components/ui/button";
import {SendSolid} from "iconoir-react";
import {useEffect, useRef} from "react";

export const PromptInput = ({
  task,
  setTask,
  sendTask,
  disable,
}: {
  task: string;
  setTask: (task: string) => void;
  sendTask?: () => void;
  disable?: boolean;
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Update height and multiline state
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      // Set a small height initially to properly measure single line
      textarea.style.height = "24px";
      const scrollHeight = textarea.scrollHeight;
      textarea.style.height = `${scrollHeight + 2}px`;
    }
  }, [task]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      if (sendTask) {
        e.preventDefault();
        sendTask();
      }
    }
  };

  const handleInput = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setTask(event.target.value);
  };

  return (
    <>
      <textarea
        ref={textareaRef}
        placeholder="Provide the goal ..."
        className="w-full px-4 py-3 bg-secondary border rounded-md pr-12 focus:outline-none placeholder-muted-foreground resize-none overflow-hidden leading-[1.2] disabled:placeholder-disabled-foreground"
        value={task}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        disabled={disable}
      />
      <Button
        size="icon"
        className="absolute right-2 mt-1 bg-secondary hover:bg-secondary"
        onClick={sendTask}
      >
        <SendSolid
          color={
            disable
              ? "hsl(var(--disabled-foreground))"
              : task.length > 0
              ? "hsl(var(--foreground))"
              : "hsl(var(--muted-foreground))"
          }
        />
      </Button>
    </>
  );
};
