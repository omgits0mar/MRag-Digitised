import { lazy } from "react";
import {
  createBrowserRouter,
  type RouteObject,
  useRouteError,
} from "react-router-dom";

import { EnvBanner } from "@/components/layout/EnvBanner";
import { AppShell } from "@/components/layout/AppShell";

const ChatPage = lazy(() => import("@/pages/ChatPage"));
const HistoryPage = lazy(() => import("@/pages/HistoryPage"));
const SettingsPage = lazy(() => import("@/pages/SettingsPage"));
const UploadPage = lazy(() => import("@/pages/UploadPage"));

function RouteErrorBoundary(): JSX.Element {
  const error = useRouteError();
  const message =
    error instanceof Error
      ? error.message
      : "Something went wrong while loading this view. Try reloading the page.";

  return <EnvBanner message={message} />;
}

export const routes: RouteObject[] = [
  {
    path: "/",
    element: <AppShell />,
    errorElement: <RouteErrorBoundary />,
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
        path: "upload",
        element: <UploadPage />,
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
