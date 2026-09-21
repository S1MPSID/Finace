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
  const fullUri = buildMongoUri(env.mongoUri, env.mongoDb);
  try {
    await mongoose.connect(fullUri, { serverSelectionTimeoutMS: 5000 });
    console.log(`[MongoDB] Connected to database: ${env.mongoDb}`);

    try {
      const usersCol = mongoose.connection.collection("users");
      const indexes = await usersCol.indexes();
      if (indexes.some((idx) => idx.name === "email_1")) {
        await usersCol.dropIndex("email_1");
        console.log("[MongoDB] Dropped legacy email_1 index from users collection");
      }
    } catch {
      // ignore
    }
  } catch (error) {
    const fallback = env.mongoFallbackUri?.trim();
    if (fallback && env.nodeEnv !== "production") {
      const fallbackUri = buildMongoUri(fallback, env.mongoDb);
      console.warn(`[MongoDB] Primary connection failed (${error.code || error.name}); trying configured development fallback.`);
      try {
        await mongoose.connect(fallbackUri, { serverSelectionTimeoutMS: 5000 });
        console.warn(`[MongoDB] Connected to development fallback database: ${env.mongoDb}`);
        return;
      } catch (fallbackError) {
        console.error("[MongoDB] Fallback connection error:", fallbackError);
      }
    }
    console.error("[MongoDB] Connection error:", error);
    process.exit(1);
  }
}
