/**
 * 统一错误处理中间件
 */
function errorHandler(err, req, res, _next) {
  console.error('[Error]', err.message || err);

  // Mongoose 验证错误
  if (err.name === 'ValidationError') {
    const messages = Object.values(err.errors).map((e) => e.message);
    return res.status(400).json({
      success: false,
      error: messages.join('; '),
    });
  }

  // Mongoose CastError（如非法 ObjectId）
  if (err.name === 'CastError') {
    return res.status(400).json({
      success: false,
      error: 'ID 格式不正确',
    });
  }

  res.status(err.status || 500).json({
    success: false,
    error: err.message || '服务器内部错误',
  });
}

module.exports = errorHandler;
