import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  client: "@hey-api/client-axios",
  input: "http://127.0.0.1:8010/openapi.json",
  output: "src/api/generated",
});
