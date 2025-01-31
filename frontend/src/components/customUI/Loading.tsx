import {cn} from "@/lib/utils";
interface LoadingProps {
  className?: string;
  dotClassName?: string;
  size?: "sm" | "md" | "lg";
}
const Loading = ({className, dotClassName, size = "md"}: LoadingProps) => {
  const sizes = {
    sm: "w-1 h-1",
    md: "w-2 h-2",
    lg: "w-3 h-3",
  };
  const containerSizes = {
    sm: "h-4",
    md: "h-6",
    lg: "h-8",
  };
  return (
    <div
      className={cn(
        "flex items-center gap-1 m-4 mb-0",
        containerSizes[size],
        className
      )}
      role="status"
    >
      <div
        className={cn(
          "animate-jump rounded-full bg-foreground",
          sizes[size],
          dotClassName
        )}
        style={{animationDelay: "0ms"}}
      />
      <div
        className={cn(
          "animate-jump rounded-full bg-foreground",
          sizes[size],
          dotClassName
        )}
        style={{animationDelay: "150ms"}}
      />
      <div
        className={cn(
          "animate-jump rounded-full bg-foreground",
          sizes[size],
          dotClassName
        )}
        style={{animationDelay: "300ms"}}
      />
    </div>
  );
};
export default Loading;
