import React from "react";

interface SidebarItemProps {
  children: React.ReactNode;
  onClick?: () => void;
}

export const SidebarItem: React.FC<SidebarItemProps> = ({
  children,
  onClick,
}) => {
  return (
    <div
      className="flex items-center px-2 py-2 gap-[10px]  rounded-sm hover:cursor-pointer hover:bg-secondary"
      onClick={onClick}
    >
      {children}
    </div>
  );
};
