# Prompt Lab — Django 版本

Django 6.0 全栈实现（Python 后端 + Django 模板前端），AI 提示词实验管理工具。

## 前置条件

- Python >= 3.10
- pip（已配置清华镜像源）

## 安装

```bash
cd django-version

# 创建虚拟环境（如未创建）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install django==6.0.6
```

## 配置

无需额外配置。Django 默认使用项目根目录下的 SQLite 数据库（`db.sqlite3`），首次运行自动创建。

## 运行

```bash
# 激活虚拟环境后
python manage.py migrate    # 首次运行：创建数据库表
python seed.py              # 填充种子数据
python manage.py runserver 8000
```

浏览器打开 **http://localhost:8000**

## 种子数据

```bash
python seed.py
```

预填 6 个标签 + 6 个提示词（含 16 条运行记录），与 MERN 版本内容一致。

## 数据模型

| 实体 | 字段 | 说明 |
|------|------|------|
| **Tag** | `title`, `notes`, timestamps | 标签，与 Prompt 多对多关联 |
| **Prompt** | `title`, `content`, `notes`, `tags` (M:N), `runs` (1:N), `version`, `rating`, timestamps | 核心实体 |
| **Run** | `prompt` (FK), `model`, `tokens`, `response_time`, createdAt | 运行记录 |

## API 端点

所有 API 返回统一格式：`{ success: bool, data?: any, error?: string }`

JSON API 端点（CSRF 豁免，可用于 curl / 第三方调用）：

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/tags` | 获取所有标签 |
| GET | `/api/tags/:id` | 获取单个标签 |
| POST | `/api/tags` | 创建标签 |
| PUT | `/api/tags/:id` | 更新标签（支持部分更新） |
| DELETE | `/api/tags/:id` | 删除标签 |
| GET | `/api/prompts` | 获取所有提示词 |
| GET | `/api/prompts/:id` | 获取单个提示词 |
| POST | `/api/prompts` | 创建提示词 |
| PUT | `/api/prompts/:id` | 更新提示词 |
| DELETE | `/api/prompts/:id` | 删除提示词 |

## 前端页面

Django 模板（服务端渲染），Tailwind CSS 通过 CDN 引入。

| 路由 | 页面 | 功能 |
|------|------|------|
| `/` | 提示词列表 | 卡片网格、空状态、排序 |
| `/prompts/new/` | 新建提示词 | 表单 + 标签多选 |
| `/prompts/<id>/` | 提示词详情 | 只读展示 + 运行记录 + 添加/删除 run |
| `/prompts/<id>/edit/` | 编辑提示词 | 预填表单 |
| `/tags/` | 标签列表 | 内联创建 + 编辑 + 删除 |
| `/tags/<id>/` | 标签详情 | notes 可编辑 + 关联提示词列表 |

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Django 6.0 (Python) |
| 数据库 | SQLite |
| ORM | Django ORM |
| 前端 | Django Templates |
| 样式 | Tailwind CSS CDN |

## 已知问题

- 模板中评分星级使用 if/elif 逐级判断，非循环生成
- Django 表单的 CSRF 保护在 curl 测试时需手动豁免（API 端点已处理）
- Windows 终端下 curl 发送中文 JSON 可能出现 GBK/UTF-8 编码问题（浏览器正常）
