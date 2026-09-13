/** PM2 config — run from python-rag/: pm2 start ecosystem.config.cjs */
module.exports = {
  apps: [
    {
      name: "finace-rag",
      cwd: __dirname,
      script: "python3",
      args: "-m uvicorn api.app:app --host 0.0.0.0 --port 8000 --workers 1",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "900M",
      env: {
        PYTHONUNBUFFERED: "1",
        OMP_NUM_THREADS: "1",
        OPENBLAS_NUM_THREADS: "1",
        MKL_NUM_THREADS: "1",
      },
    },
  ],
};
