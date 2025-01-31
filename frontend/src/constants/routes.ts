export const PAGE_ROUTES = {
  home: "/playground",
  chat: (id?: string) =>
    id ? `/playground/chat/${id}` : "/playground/chat/:id",
};
