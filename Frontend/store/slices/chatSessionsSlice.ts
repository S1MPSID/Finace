import { createAsyncThunk, createSlice, type PayloadAction } from "@reduxjs/toolkit";
import { chatHistoryApi } from "@/services/api";
import { logout } from "./authSlice";

export type ChatSessionRow = {
  session_id: string;
  title: string;
  last_risk_level?: string;
  last_score?: number;
  updated_at?: string;
};

type ChatSessionsState = {
  sessions: ChatSessionRow[];
  status: "idle" | "loading" | "succeeded" | "failed";
  loaded: boolean;
};

const initialState: ChatSessionsState = {
  sessions: [],
  status: "idle",
  loaded: false,
};

export function toSessionRow(session: any): ChatSessionRow {
  return {
    session_id: session.session_id,
    title: session.title || "New compliance chat",
    last_risk_level: session.last_risk_level,
    last_score: session.last_score,
    updated_at: session.updated_at,
  };
}

function sortSessions(sessions: ChatSessionRow[]) {
  return [...sessions].sort((a, b) => {
    const aTime = a.updated_at ? Date.parse(a.updated_at) : 0;
    const bTime = b.updated_at ? Date.parse(b.updated_at) : 0;
    return bTime - aTime;
  });
}

/** One-time load after login — sidebar reads from Redux after this. */
export const fetchChatSessions = createAsyncThunk(
  "chatSessions/fetchAll",
  async (_, { getState, rejectWithValue }) => {
    const role = (getState() as { auth?: { user?: { role?: string } } }).auth?.user?.role;
    if (role === "evaluator") return [];

    try {
      const data: any = await chatHistoryApi.list();
      return (data.sessions || []).map(toSessionRow);
    } catch (err: any) {
      return rejectWithValue(err?.message || "Failed to load chats");
    }
  }
);

const chatSessionsSlice = createSlice({
  name: "chatSessions",
  initialState,
  reducers: {
    upsertChatSession(state, action: PayloadAction<ChatSessionRow>) {
      const idx = state.sessions.findIndex((s) => s.session_id === action.payload.session_id);
      if (idx >= 0) {
        state.sessions[idx] = action.payload;
      } else {
        state.sessions.unshift(action.payload);
      }
      state.sessions = sortSessions(state.sessions);
    },
    removeChatSession(state, action: PayloadAction<string>) {
      state.sessions = state.sessions.filter((s) => s.session_id !== action.payload);
    },
    clearChatSessions(state) {
      state.sessions = [];
      state.status = "idle";
      state.loaded = false;
    },
    markChatSessionsLoaded(state) {
      state.sessions = [];
      state.status = "succeeded";
      state.loaded = true;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchChatSessions.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchChatSessions.fulfilled, (state, action) => {
        state.sessions = sortSessions(action.payload);
        state.status = "succeeded";
        state.loaded = true;
      })
      .addCase(fetchChatSessions.rejected, (state) => {
        state.status = "failed";
        state.loaded = true;
      })
      .addCase(logout, (state) => {
        state.sessions = [];
        state.status = "idle";
        state.loaded = false;
      });
  },
});

export const { upsertChatSession, removeChatSession, clearChatSessions, markChatSessionsLoaded } =
  chatSessionsSlice.actions;
export default chatSessionsSlice.reducer;
