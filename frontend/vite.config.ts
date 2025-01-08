import react from "@vitejs/plugin-react-swc";
import {config} from "dotenv";
import path from "path";
import {defineConfig} from "vite";
import svgr from "vite-plugin-svgr";

config();

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), svgr()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  preview: {
    port: 3000,
    strictPort: true,
  },
  server: {
    port: 3000,
    strictPort: true,
    host: true,
    origin: "http://0.0.0.0:3000",
  },
  define: {
    "process.env.MODEL_NAME": JSON.stringify(
      process.env.AGENTIC_BENCH_MODEL_NAME
    ),
  },
});
