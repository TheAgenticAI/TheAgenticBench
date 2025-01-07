import {IconoirProvider} from "iconoir-react";
import {useEffect} from "react";
import {QueryClient, QueryClientProvider} from "react-query";
import {Navigate, Route, BrowserRouter as Router, Routes} from "react-router";
import {PAGE_ROUTES} from "./constants/routes";
import Layout from "./pages/Layout";
// For future use
// import { Chat } from "./pages/Chat";
// import Playground from "./pages/Playground";

const {VITE_PRODUCT_ICON, VITE_PRODUCT_PAGE_TITLE} = import.meta.env;

const queryClient = new QueryClient();

function App() {
  useEffect(() => {
    let link = document.querySelector("link[rel~='icon']") as HTMLLinkElement;
    if (!link) {
      link = document.createElement("link");
      link.rel = "icon";
      document.getElementsByTagName("head")[0].appendChild(link);
    }
    link.href =
      VITE_PRODUCT_ICON ||
      "https://sg-ui-assets.s3.us-east-1.amazonaws.com/ta_bench_favicon.svg";

    document.title = VITE_PRODUCT_PAGE_TITLE || "TheAgentic | Bench";
  });

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
