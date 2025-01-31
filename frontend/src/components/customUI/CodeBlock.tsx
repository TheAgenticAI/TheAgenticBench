import Markdown from "react-markdown";
import {Prism as SyntaxHighlighter} from "react-syntax-highlighter";
import {tomorrow} from "react-syntax-highlighter/dist/esm/styles/prism";
import rehypeRaw from "rehype-raw";
import remarkBreaks from "remark-breaks";

export const CodeBlock = ({content}: {content: string}) => {
  return (
    <div className="relative group">
      <div className="rounded-lg bg-zinc-900 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 bg-zinc-800/50">
          <span className="text-sm text-gray-400">example.py</span>
        </div>
        <div className="overflow-x-auto [&::-webkit-scrollbar]:h-2 [&::-webkit-scrollbar-track]:bg-zinc-800 [&::-webkit-scrollbar-thumb]:bg-zinc-700 [&::-webkit-scrollbar-thumb]:rounded-full">
          <Markdown
            children={content.replaceAll("\\n", "\n")}
            rehypePlugins={[rehypeRaw]}
            remarkPlugins={[remarkBreaks]}
            className="text-sm leading-6 whitespace-pre p-4"
            components={{
              code(props) {
                const {children, className, ...rest} = props;
                const match = /language-(\w+)/.exec(className || "");
                return match ? (
                  <SyntaxHighlighter
                    PreTag="pre"
                    language={match[1]}
                    style={tomorrow}
                  >
                    {String(children).replace(/\n$/, "")}
                  </SyntaxHighlighter>
                ) : (
                  <code {...rest} className={className}>
                    {children}
                  </code>
                );
              },
            }}
          />
        </div>
      </div>
    </div>
  );
};
