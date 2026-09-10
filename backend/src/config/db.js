import mongoose from "mongoose";
import { env } from "./env.js";

function buildMongoUri(uri, dbName) {
  const raw = (uri || "").trim();
  if (!raw) {
    throw new Error("MONGO_URI is required");
  }

  // Atlas SRV URIs should keep query params and set DB via path segment.
  // Example: mongodb+srv://user:pass@cluster/.../?appName=Cluster0
  if (raw.startsWith("mongodb+srv://") || raw.includes("mongodb.net")) {
    const [base, query = ""] = raw.split("?");
    const withoutSlash = base.replace(/\/$/, "");
    const withDb = withoutSlash.includes(`/${dbName}`)
      ? withoutSlash
      : `${withoutSlash}/${dbName}`;
    return query ? `${withDb}?${query}` : withDb;
  }

  const cleaned = raw.endsWith("/") ? raw.slice(0, -1) : raw;
  return `${cleaned}/${dbName}`;
}

export async function connectDB() {
  try {
    const fullUri = buildMongoUri(env.mongoUri, env.mongoDb);
    await mongoose.connect(fullUri);
    console.log(`[MongoDB] Connected to database: ${env.mongoDb}`);
  } catch (error) {
    console.error("[MongoDB] Connection error:", error);
    process.exit(1);
  }
}
