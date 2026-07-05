const express = require('express');
const router = express.Router();
const Tag = require('../models/Tag');

// GET /api/tags — 获取所有标签（按更新时间倒序）
router.get('/', async (req, res, next) => {
  try {
    const tags = await Tag.find().sort({ updatedAt: -1 });
    res.json({ success: true, data: tags });
  } catch (err) {
    next(err);
  }
});

// GET /api/tags/:id — 获取单个标签
router.get('/:id', async (req, res, next) => {
  try {
    const tag = await Tag.findById(req.params.id);
    if (!tag) {
      return res.status(404).json({ success: false, error: '标签不存在' });
    }
    res.json({ success: true, data: tag });
  } catch (err) {
    next(err);
  }
});

// POST /api/tags — 创建标签
router.post('/', async (req, res, next) => {
  try {
    const tag = await Tag.create(req.body);
    res.status(201).json({ success: true, data: tag });
  } catch (err) {
    next(err);
  }
});

// PUT /api/tags/:id — 更新标签
router.put('/:id', async (req, res, next) => {
  try {
    const tag = await Tag.findByIdAndUpdate(req.params.id, req.body, {
      new: true,
      runValidators: true,
    });
    if (!tag) {
      return res.status(404).json({ success: false, error: '标签不存在' });
    }
    res.json({ success: true, data: tag });
  } catch (err) {
    next(err);
  }
});

// DELETE /api/tags/:id — 删除标签
router.delete('/:id', async (req, res, next) => {
  try {
    const tag = await Tag.findByIdAndDelete(req.params.id);
    if (!tag) {
      return res.status(404).json({ success: false, error: '标签不存在' });
    }
    res.json({ success: true, data: { message: '删除成功' } });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
