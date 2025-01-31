import {IconoirProvider} from "iconoir-react";
import {QueryClient, QueryClientProvider} from "react-query";
import {Navigate, Route, BrowserRouter as Router, Routes} from "react-router";
import {PAGE_ROUTES} from "./constants/routes";
import Layout from "./pages/Layout";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <IconoirProvider
        iconProps={{
          color: "hsl(var(--foreground))",
          strokeWidth: 2,
          width: "16px",
          height: "16px",
        }}
      >
        <Router>
          <Routes>
            <Route path="/" element={<Navigate to={PAGE_ROUTES.home} />} />
            <Route path={PAGE_ROUTES.home} element={<Layout />} />
          </Routes>
        </Router>
      </IconoirProvider>
    </QueryClientProvider>
  );
}

export default App;
