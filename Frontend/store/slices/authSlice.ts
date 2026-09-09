import { createAsyncThunk, createSlice, type PayloadAction } from "@reduxjs/toolkit";
import {
  clearAuthCookies,
  getAuthToken,
  setAuthCookies,
  userFromToken,
  type AuthUser,
} from "@/lib/authCookies";
import api from "@/services/api";

export type AppUser = AuthUser;

type AuthState = {
  user: AppUser | null;
  token: string | null;
  isAuthenticated: boolean;
  authReady: boolean;
  status: "idle" | "loading" | "succeeded" | "failed";
  error: string | null;
};

const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  authReady: false,
  status: "idle",
  error: null,
};

/** Read cookie → call GET /auth/me → put user in Redux */
export const hydrateAuth = createAsyncThunk("auth/hydrate", async (_, { rejectWithValue }) => {
  const token = getAuthToken();
  if (!token) {
    return rejectWithValue("no_token");
  }

  // Optimistic JWT decode so UI can show a name immediately
  const jwtUser = userFromToken(token);

  // Evaluator sessions: prefer JWT + evaluator /me (company /auth/me may 401 on older backends)
  if (jwtUser?.role === "evaluator") {
    try {
      const data: any = await api.get("/evaluator/auth/me");
      if (data?.ok && data.user) {
        const user = data.user as AppUser;
        setAuthCookies(token, user);
        return { token, user };
      }
    } catch {
      /* fall through to JWT */
    }
    setAuthCookies(token, jwtUser);
    return { token, user: jwtUser };
  }

  try {
    const data: any = await api.get("/auth/me");
    if (data?.ok && data.user) {
      const user = data.user as AppUser;
      setAuthCookies(token, user);
      return { token, user };
    }
  } catch {
    // Fall back to JWT claims if /me fails (offline / old backend)
  }

  if (jwtUser) {
    setAuthCookies(token, jwtUser);
    return { token, user: jwtUser };
  }

  clearAuthCookies();
  return rejectWithValue("invalid_session");
});

export const fetchCurrentUser = createAsyncThunk("auth/fetchMe", async (_, { rejectWithValue }) => {
  const token = getAuthToken();
  if (!token) return rejectWithValue("no_token");
  try {
    const data: any = await api.get("/auth/me");
    if (data?.ok && data.user) {
      setAuthCookies(token, data.user);
      return { token, user: data.user as AppUser };
    }
    return rejectWithValue("bad_response");
  } catch (err: any) {
    return rejectWithValue(err?.message || "fetch_failed");
  }
});

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    loginSuccess(state, action: PayloadAction<{ user: AppUser; token: string }>) {
      const { user, token } = action.payload;
      setAuthCookies(token, user);
      state.user = user;
      state.token = token;
      state.isAuthenticated = true;
      state.authReady = true;
      state.status = "succeeded";
      state.error = null;
    },
    logout(state) {
      clearAuthCookies();
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      state.authReady = true;
      state.status = "idle";
      state.error = null;
    },
    markAuthReady(state) {
      state.authReady = true;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(hydrateAuth.pending, (state) => {
        state.status = "loading";
      })
      .addCase(hydrateAuth.fulfilled, (state, action) => {
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.isAuthenticated = true;
        state.authReady = true;
        state.status = "succeeded";
        state.error = null;
      })
      .addCase(hydrateAuth.rejected, (state) => {
        state.user = null;
        state.token = null;
        state.isAuthenticated = false;
        state.authReady = true;
        state.status = "failed";
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action) => {
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.isAuthenticated = true;
        state.authReady = true;
        state.status = "succeeded";
      });
  },
});

export const { loginSuccess, logout, markAuthReady } = authSlice.actions;
export default authSlice.reducer;
