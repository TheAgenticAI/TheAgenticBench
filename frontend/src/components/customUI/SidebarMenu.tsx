import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {Bin, EditPencil} from "iconoir-react";

export const SidebarMenu = ({
  children,
  handleStartEdit,
  setAlertOpen,
}: {
  children: React.ReactNode;
  handleStartEdit: (e: React.MouseEvent) => void;
  setAlertOpen: React.Dispatch<React.SetStateAction<boolean>>;
}) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="focus:outline-none">
        {children}
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem
          className="flex items-center space-x-2"
          onClick={handleStartEdit}
        >
          <EditPencil />
          Rename
        </DropdownMenuItem>
        <DropdownMenuItem
          className="flex items-center space-x-2 text-destructive-foreground focus:text-destructive-foreground focus:bg-destructive "
          onClick={() => setAlertOpen(true)}
        >
          <Bin color="hsl(var(--destructive-foreground))" />
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
