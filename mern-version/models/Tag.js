const mongoose = require('mongoose');

const tagSchema = new mongoose.Schema(
  {
    title: {
      type: String,
      required: [true, '标签名称不能为空'],
      trim: true,
      maxlength: [100, '标签名称不能超过100个字符'],
      validate: {
        validator: function (v) {
          return v.trim().length > 0;
        },
        message: '标签名称不能全为空格',
      },
    },
    notes: {
      type: String,
      required: [true, '标签说明不能为空'],
      trim: true,
      validate: {
        validator: function (v) {
          return v.trim().length > 0;
        },
        message: '标签说明不能全为空格',
      },
    },
  },
  {
    timestamps: true,
  }
);

module.exports = mongoose.model('Tag', tagSchema);
