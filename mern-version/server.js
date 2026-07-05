const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const tagsRouter = require('./routes/tags');
const promptsRouter = require('./routes/prompts');
const errorHandler = require('./middleware/errorHandler');

const app = express();
const PORT = process.env.PORT || 3000;
const MONGODB_URI =
  process.env.MONGODB_URI || 'mongodb://localhost:27017/prompt-lab';

const path = require('path');

// ── 中间件 ──────────────────────────────────────────
app.use(cors());
app.use(express.json());

// ── API 路由 ────────────────────────────────────────
app.get('/api/health', (_req, res) => {
  res.json({ success: true, data: { message: 'Prompt Lab API running' } });
});

app.use('/api/tags', tagsRouter);
app.use('/api/prompts', promptsRouter);

// ── 生产环境：托管前端静态文件 + SPA fallback ──────
const clientDist = path.resolve(__dirname, 'client', 'dist');
app.use(express.static(clientDist));
// Express 5 不支持 app.get('*')；用 middleware 做 SPA fallback
app.use((req, res, next) => {
  if (req.path.startsWith('/api/')) return next();
  res.sendFile(path.join(clientDist, 'index.html'), (err) => {
    if (err) next();
  });
});

// ── 统一错误处理 ────────────────────────────────────
app.use(errorHandler);

// ── 启动 ────────────────────────────────────────────
mongoose
  .connect(MONGODB_URI)
  .then(() => {
    console.log(`[DB] MongoDB 连接成功`);
    app.listen(PORT, () => {
      console.log(`[Server] 运行在 http://localhost:${PORT}`);
    });
  })
  .catch((err) => {
    console.error('[DB] MongoDB 连接失败:', err.message);
    process.exit(1);
  });
