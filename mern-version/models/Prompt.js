const mongoose = require('mongoose');

const promptSchema = new mongoose.Schema(
  {
    title: {
      type: String,
      required: [true, '提示词名称不能为空'],
      trim: true,
      maxlength: [100, '提示词名称不能超过100个字符'],
      validate: {
        validator: function (v) {
          return v.trim().length > 0;
        },
        message: '提示词名称不能全为空格',
      },
    },
    content: {
      type: String,
      required: [true, '提示词内容不能为空'],
      trim: true,
      validate: {
        validator: function (v) {
          return v.trim().length > 0;
        },
        message: '提示词内容不能全为空格',
      },
    },
    notes: {
      type: String,
      required: [true, '反思备注不能为空'],
      trim: true,
      validate: {
        validator: function (v) {
          return v.trim().length > 0;
        },
        message: '反思备注不能全为空格',
      },
    },
    tags: [
      {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Tag',
      },
    ],
    // 运行记录（可叠加多次，每次记录模型/token/耗时）
    runs: [
      {
        model: {
          type: String,
          trim: true,
          required: [true, '模型名称不能为空'],
        },
        tokens: {
          type: Number,
          min: [0, 'token 消耗不能为负数'],
          default: 0,
        },
        responseTime: {
          type: Number,
          min: [0, '响应耗时不能为负数'],
          default: 0,
        },
        createdAt: {
          type: Date,
          default: Date.now,
        },
      },
    ],
    version: {
      type: String,
      trim: true,
    },
    rating: {
      type: Number,
      min: [1, '评分最低为1'],
      max: [5, '评分最高为5'],
    },
  },
  {
    timestamps: true,
  }
);

module.exports = mongoose.model('Prompt', promptSchema);
