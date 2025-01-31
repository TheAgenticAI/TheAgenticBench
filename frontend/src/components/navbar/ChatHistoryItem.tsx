import {PAGE_ROUTES} from "@/constants/routes";
import {MoreHoriz} from "iconoir-react";
import {useEffect, useRef, useState} from "react";
import {useNavigate} from "react-router";
import {DeleteAlert} from "../customUI/DeleteAlert";
import {SidebarMenu} from "../customUI/SidebarMenu";
import {SidebarItem} from "./SidebarItem";
export const ChatHistoryItem = ({
  id,
  name,
  onUpdateName,
}: {
  id: string;
  name: string;
  onUpdateName: (id: string, newName: string) => void;
}) => {
  const nav = useNavigate();

  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState(name);
  const [isOpen, setIsOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  const handleStartEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(true);
    setEditedName(name);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      onUpdateName(id, editedName);
      setIsEditing(false);
    } else if (e.key === "Escape") {
      setIsEditing(false);
      setEditedName(name);
    }
  };
  const handleBlur = () => {
    setIsEditing(false);
    setEditedName(name);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  return (
    <SidebarItem>
      {isEditing ? (
        <input
          ref={inputRef}
          type="text"
          value={editedName}
          onChange={(e) => setEditedName(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          className="p-1 text-sm w-full bg-secondary border rounded-sm focus:outline-none "
        />
      ) : (
        <>
          <p
            className="text-base flex-1"
            onClick={() => nav(PAGE_ROUTES.chat(id))}
          >
            {name}
          </p>
          <SidebarMenu
            handleStartEdit={handleStartEdit}
            setAlertOpen={setIsOpen}
          >
            <MoreHoriz />
          </SidebarMenu>
        </>
      )}
      <DeleteAlert
        isOpen={isOpen}
        handleDelete={handleDelete}
        setAlertOpen={setIsOpen}
      />
    </SidebarItem>
  );
};
