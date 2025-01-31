import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {buttonVariants} from "../ui/button";

export function DeleteAlert({
  isOpen,
  handleDelete,
  setAlertOpen,
}: {
  isOpen: boolean;
  handleDelete: (e: React.MouseEvent) => void;
  setAlertOpen: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  return (
    <AlertDialog open={isOpen} onOpenChange={setAlertOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Chat?</AlertDialogTitle>
          <AlertDialogDescription>
            This chat will be deleted forever. The task history cannot be
            restored.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            className={buttonVariants({variant: "destructive"})}
          >
            Continue
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
