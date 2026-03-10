---
title: "ML Training Day 2 — 24小时训练完成，Loss 1.27"
date: 2026-03-09
draft: false
tags: ['ML', 'PyTorch', 'LLM', 'Knowledge Distillation', 'Training']
description: "第二轮 24 小时训练完成，lm loss 从 1.6 降到 1.27，inference 测试加了 repetition penalty 后输出明显连贯。"
showTableOfContents: true
---

## 训练结果

跑了整整 24 小时，20 epochs。
最终 `lm loss: 1.27`，昨晚是 1.6，进步明显。
模型已上传：`s3://weijianz-ml-models/my-student-v2.pt`

---

## Inference 测试

### 纯 temperature=0.7（无任何处理）

模型有语义相关词，但严重 repetition loop：

```
Q: What is the capital of France?
A: France? France? France? France? France? France?...

Q: How to cook pasta?
A: pizza pizza pizza pizza pizza pizza pizza pizza...
```

### 加 repetition penalty（1.3）后

每次生成下一个 token 时，把已经出现过的 token 的 logit 除以 1.3，降低其概率：

```python
for token_id in ids[0].tolist():
    next_logits[0, token_id] /= rep_penalty  # 1.3
```

效果明显改善：

```
Q: How to cook pasta?
A: To make sure it meets correctly, follow your prepared and
   properly. Follow with a proper spacing...

Q: Write a poem about the ocean
A: The waves crashing from the ocean's surface of earth,
   and oceans crash to meet their own sea shells in our bodies.
   Ocean reflects this sense of calmness and awe...
```

> ⚠️ 这是推理时的 trick，模型权重没变。本质上模型还是有 repetition 问题，只是被强行压制了。要真正解决需要 loss 降到更低。

---

## Loss 目标参考

| lm loss | 状态 |
|---------|------|
| > 2.0 | 输出基本乱码 |
| 1.5 – 2.0 | 有相关词，重复严重 |
| 1.2 – 1.5 | 有语义，需要辅助手段（**现在 1.27**）|
| < 1.0 | 🎯 目标：无需 trick 自然连贯 |

181M 参数的模型能不能到 1.0 以下还不确定——Qwen 0.5B 本身也才 500M 参数。

---

## 决策

**换大模型？**
暂不换。数据和 epoch 不够才是主要瓶颈，不是模型太小。

| 模型规模 | 预期 lm loss | 显存需求 |
|---------|------------|---------|
| 181M（现在）| ~1.2 | 7GB ✅ |
| 350M | ~1.0 | 10GB ⚠️ |
| 500M | ~0.9 | 14GB ⚠️ |
| 1B+ | ~0.7 | 需升级实例 |

**用 Bedrock Claude 当老师？**
Bedrock API 只返回文本，不返回 logits，无法做 soft label distillation。
备选方案：用 Claude 生成高质量问答数据，做 supervised fine-tuning（data distillation）。

**保留 repetition penalty hack？**
不保留。用纯模型能力跑，靠降 loss 真正解决问题。

---

## 继续训练

再跑 24 小时，从 checkpoint resume，目标降到 **1.1 以下**。

```
Student: 181.2M params
Resumed from checkpoint
[1.1min] step=200 epoch=1 kl=23.58 lm=1.27 total=24.85
```

明天看结果。
