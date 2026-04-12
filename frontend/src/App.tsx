import { RouterProvider } from "react-router-dom";

import { ThemeProvider } from "@/components/layout/ThemeProvider";
import { createAppRouter } from "@/router";

export function App(): JSX.Element {
  return (
    <ThemeProvider>
      <RouterProvider router={createAppRouter()} />
    </ThemeProvider>
  );
}

export default App;
