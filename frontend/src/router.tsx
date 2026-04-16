import { lazy } from "react";
import {
  createBrowserRouter,
  type RouteObject,
} from "react-router-dom";

import { AppShell } from "@/components/layout/AppShell";

const ChatPage = lazy(() => import("@/pages/ChatPage"));
const HistoryPage = lazy(() => import("@/pages/HistoryPage"));
const SettingsPage = lazy(() => import("@/pages/SettingsPage"));

export const routes: RouteObject[] = [
  {
    path: "/",
    element: <AppShell />,
    children: [
      {
        index: true,
        element: <ChatPage />,
      },
      {
        path: "history",
        element: <HistoryPage />,
      },
      {
        path: "settings",
        element: <SettingsPage />,
      },
    ],
  },
];

export function createAppRouter() {
  return createBrowserRouter(routes);
}
