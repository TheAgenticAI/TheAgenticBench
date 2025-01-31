import {AlertCircle} from "lucide-react";

import {Alert, AlertDescription} from "@/components/ui/alert";

export const ErrorAlert = ({errorMessage}: {errorMessage?: string}) => {
  return (
    <Alert variant="destructive">
      <AlertCircle
        color="hsl(var(--destructive-foreground))"
        className="h-5 w-5"
      />
      <AlertDescription>
        {errorMessage || "Something went wrong."}
      </AlertDescription>
    </Alert>
  );
};
