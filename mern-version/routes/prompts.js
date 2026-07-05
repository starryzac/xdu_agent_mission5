const express = require('express');
const router = express.Router();
const Prompt = require('../models/Prompt');

// GET /api/prompts — 获取所有提示词（按更新时间倒序，populate 关联标签）
router.get('/', async (req, res, next) => {
  try {
    const prompts = await Prompt.find()
      .populate('tags')
      .sort({ updatedAt: -1 });
    res.json({ success: true, data: prompts });
  } catch (err) {
    next(err);
  }
});

// GET /api/prompts/:id — 获取单个提示词
router.get('/:id', async (req, res, next) => {
  try {
    const prompt = await Prompt.findById(req.params.id).populate('tags');
    if (!prompt) {
      return res.status(404).json({ success: false, error: '提示词不存在' });
    }
    res.json({ success: true, data: prompt });
  } catch (err) {
    next(err);
  }
});

// POST /api/prompts — 创建提示词
router.post('/', async (req, res, next) => {
  try {
    const prompt = await Prompt.create(req.body);
    // populate tags after creation
    const populated = await prompt.populate('tags');
    res.status(201).json({ success: true, data: populated });
  } catch (err) {
    next(err);
  }
});

// PUT /api/prompts/:id — 更新提示词
router.put('/:id', async (req, res, next) => {
  try {
    const prompt = await Prompt.findByIdAndUpdate(req.params.id, req.body, {
      new: true,
      runValidators: true,
    }).populate('tags');
    if (!prompt) {
      return res.status(404).json({ success: false, error: '提示词不存在' });
    }
    res.json({ success: true, data: prompt });
  } catch (err) {
    next(err);
  }
});

// DELETE /api/prompts/:id — 删除提示词
router.delete('/:id', async (req, res, next) => {
  try {
    const prompt = await Prompt.findByIdAndDelete(req.params.id);
    if (!prompt) {
      return res.status(404).json({ success: false, error: '提示词不存在' });
    }
    res.json({ success: true, data: { message: '删除成功' } });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
