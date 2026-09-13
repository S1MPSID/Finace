import { createAsyncThunk, createSlice, type PayloadAction } from "@reduxjs/toolkit";
import { reportsApi } from "@/services/api";

type ReportsState = {
  reports: any[];
  auditLogs: any[];
  isLoading: boolean;
  error: string | null;
  activeReportId: string | null;
};

const initialState: ReportsState = {
  reports: [],
  auditLogs: [],
  isLoading: false,
  error: null,
  activeReportId: null,
};

export const fetchReports = createAsyncThunk("reports/fetchAll", async (_, { rejectWithValue }) => {
  try {
    const data: any = await reportsApi.getAll();
    const reports = data.reports || [];
    return {
      reports,
      auditLogs: reports.filter((r: any) => r.ipfs_cid || r.tx_hash),
    };
  } catch (err: any) {
    return rejectWithValue(err?.message || "Failed to fetch reports");
  }
});

const reportsSlice = createSlice({
  name: "reports",
  initialState,
  reducers: {
    setActiveReportId(state, action: PayloadAction<string | null>) {
      state.activeReportId = action.payload;
    },
    clearReports(state) {
      state.reports = [];
      state.auditLogs = [];
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchReports.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchReports.fulfilled, (state, action) => {
        state.reports = action.payload.reports;
        state.auditLogs = action.payload.auditLogs;
        state.isLoading = false;
      })
      .addCase(fetchReports.rejected, (state, action) => {
        state.isLoading = false;
        state.error = String(action.payload || "Failed to fetch reports");
      });
  },
});

export const { setActiveReportId, clearReports } = reportsSlice.actions;
export default reportsSlice.reducer;
