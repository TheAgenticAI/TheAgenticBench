import Markdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import remarkBreaks from "remark-breaks";

export const TerminalBlock = ({content}: {content: string}) => {
  return (
    <div className="relative group">
      <div className="rounded-lg bg-zinc-900 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 bg-zinc-800/50">
          <span className="text-sm text-gray-400">Terminal</span>
        </div>
        <div className="overflow-x-auto [&::-webkit-scrollbar]:h-2 [&::-webkit-scrollbar-track]:bg-zinc-800 [&::-webkit-scrollbar-thumb]:bg-zinc-700 [&::-webkit-scrollbar-thumb]:rounded-full">
          <Markdown
            rehypePlugins={[rehypeRaw]}
            remarkPlugins={[remarkBreaks]}
            className="p-4 text-sm leading-6 whitespace-pre"
          >
            {content.replaceAll("\\n", "\n")}
          </Markdown>
        </div>
      </div>
    </div>
  );
};
