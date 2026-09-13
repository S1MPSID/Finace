import cors from "cors";
import express from "express";
import path from "path";
import { fileURLToPath } from "url";

import { env } from "./config/env.js";
import { errorHandler, notFoundHandler } from "./middlewares/errorHandler.js";
import { attachRequestContext } from "./middlewares/requestContext.js";
import apiRouter from "./routes/index.js";

import { serveDoc } from "./controllers/docsController.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

app.disable("x-powered-by");
app.use(attachRequestContext);
app.use(
  cors({
    origin: env.corsOrigins.length > 0 ? env.corsOrigins : true,
    credentials: true,
  })
);
app.use(express.json({ limit: env.jsonBodyLimit }));

// Dynamic document server (supports subdirectories and fuzzy matching)
app.get(/^\/docs\/(.*)/, serveDoc);

app.get("/health", (_req, res) => {
  res.json({
    ok: true,
    service: env.serviceName,
    environment: env.nodeEnv,
  });
});

app.use(env.apiPrefix, apiRouter);

app.use(notFoundHandler);
app.use(errorHandler);

export default app;
