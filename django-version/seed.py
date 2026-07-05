import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from prompts.models import Tag, Prompt, Run

Tag.objects.all().delete()
Prompt.objects.all().delete()

tags_data = [
    {"title": "代码生成", "notes": "用于生成各类代码的提示词，包括函数、组件、算法等"},
    {"title": "文案润色", "notes": "优化文本表达，使其更流畅、专业、有感染力"},
    {"title": "翻译", "notes": "中英文及多语言翻译，可指定风格和领域"},
    {"title": "知识问答", "notes": "向模型提问，获取解释、分析和建议"},
    {"title": "角色扮演", "notes": "让模型扮演特定角色，如面试官、客服、导师等"},
    {"title": "数据分析", "notes": "处理和分析数据的提示词，包括清洗、统计、可视化建议"},
]
tags = [Tag.objects.create(**d) for d in tags_data]
print(f"Tags: {len(tags)}")

prompts_data = [
    {
        "title": "通用代码生成器",
        "content": "你是一位资深全栈开发者，拥有 10 年以上经验。请根据以下需求生成高质量代码。\n\n要求：\n1. 代码结构清晰，命名规范\n2. 包含必要的错误处理\n3. 关键逻辑添加注释\n4. 优先使用现代语法和最佳实践\n\n需求：{{requirement}}",
        "notes": "第一版效果不错，但对复杂需求的分解能力不足。建议在提需求时尽量拆分步骤，每次只让模型做一件事。DeepSeek 对中文需求理解更好，Claude 对英文和代码风格把控更强。",
        "version": "v1", "rating": 4,
        "tags": [0, 1],
        "runs": [("deepseek-v4-pro", 1520, 3200), ("claude-sonnet-5", 2100, 1800)],
    },
    {
        "title": "文章润色助手",
        "content": "你是一位专业的中文编辑，擅长提升文章的表达质量。请对以下文本进行润色，使其更加流畅、准确、有感染力。\n\n润色原则：\n1. 保持原意不变\n2. 优化句式结构\n3. 替换平淡的词汇\n4. 修正语法错误和错别字\n5. 适应目标读者群体：{{audience}}\n\n原文：\n{{text}}",
        "notes": "中文润色效果非常好，尤其是学术和商务场景。GPT-4o 的润色比 DeepSeek 更自然，但 DeepSeek 速度快很多。",
        "version": "v2", "rating": 5,
        "tags": [1, 2, 3],
        "runs": [("deepseek-v4-pro", 980, 2100), ("claude-sonnet-5", 1100, 2500), ("gpt-4o", 1350, 4200)],
    },
    {
        "title": "中英互译专家",
        "content": "你是一位资深翻译，精通中文和英文，擅长在两种语言间进行地道、准确的翻译。\n\n翻译要求：\n1. 翻译结果自然地道，符合目标语言表达习惯\n2. 保留原文的语气和风格\n3. 专业术语翻译准确\n4. 文化特定表达做适当本地化处理\n\n翻译方向：{{direction}}\n领域：{{domain}}\n\n原文：\n{{text}}",
        "notes": "技术文档翻译很精准，文学类翻译偏生硬。DeepSeek 的中译英有时会出现中式英语，Claude 好很多。",
        "version": "v1", "rating": 4,
        "tags": [2, 3],
        "runs": [("deepseek-v4-pro", 850, 1800), ("claude-sonnet-5", 920, 2200)],
    },
    {
        "title": "前端组件生成器",
        "content": "你是一位资深前端工程师，精通 React + Tailwind CSS。请根据以下描述生成一个可复用的 UI 组件。\n\n要求：\n1. 使用 React 函数组件 + Hooks\n2. 样式使用 Tailwind CSS\n3. 组件接收合理的 props\n4. 包含 loading、error、empty 等边界状态\n5. 符合无障碍访问标准\n\n组件描述：{{description}}",
        "notes": "生成质量很高。需要注意：AI 偶尔会编造不存在的 Tailwind 类名，需要实际运行确认。React 19 的 forwardRef 已不需要。",
        "version": "v3", "rating": 5,
        "tags": [3, 4, 5],
        "runs": [("deepseek-v4-pro", 2200, 4500), ("claude-sonnet-5", 1800, 2800), ("claude-opus-4-8", 2500, 5100)],
    },
    {
        "title": "Bug 诊断助手",
        "content": "你是一位资深调试工程师。请分析以下错误信息并给出诊断和修复方案。\n\n分析步骤：\n1. 解释错误的直接原因\n2. 追溯可能的根本原因\n3. 给出 2-3 个修复方案（按推荐度排序）\n4. 说明如何避免类似问题\n\n技术栈：{{techstack}}\n错误信息：\n```\n{{error}}\n```\n相关代码：\n```\n{{code}}\n```",
        "notes": "非常实用！对常见错误诊断很准。建议提供完整的堆栈信息，而不是只给最后一行。",
        "version": "v2", "rating": 5,
        "tags": [4, 5],
        "runs": [("deepseek-v4-pro", 1800, 3500), ("claude-sonnet-5", 1600, 2600), ("claude-opus-4-8", 2100, 4200), ("gpt-4o", 1900, 3800)],
    },
    {
        "title": "API 文档生成器",
        "content": "你是一位技术文档撰写专家。请根据以下 API 代码自动生成接口文档。\n\n文档格式：\n1. 接口概述（一句话）\n2. 请求方法 + URL\n3. 请求参数及说明\n4. 响应示例（成功 + 失败各一个）\n5. 错误码说明\n6. 调用示例（curl + JavaScript）\n\nAPI 代码：\n```\n{{code}}\n```",
        "notes": "对 Express 和 Django REST 的代码解析很准确，对 Spring Boot 有时会搞混注解。生成的文档可以直接粘贴到 README。",
        "version": "v1", "rating": 4,
        "tags": [5, 0, 1],
        "runs": [("deepseek-v4-pro", 1100, 2400), ("claude-sonnet-5", 950, 1900)],
    },
]

for d in prompts_data:
    tag_objs = [tags[i] for i in d.pop("tags")]
    runs = d.pop("runs")
    prompt = Prompt.objects.create(**d)
    prompt.tags.set(tag_objs)
    for model, tokens, rt in runs:
        Run.objects.create(prompt=prompt, model=model, tokens=tokens, response_time=rt)

print(f"Prompts: {Prompt.objects.count()}, Runs: {Run.objects.count()}")
print("Seed done.")
