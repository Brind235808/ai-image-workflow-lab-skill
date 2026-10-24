---
name: ai-image-workflow-lab-skill
description: Run AI image workflow research across many sessions using file-based memory instead of chat history. Use for ComfyUI or diffusion workflow iteration, experiment logs, scoring cards, and retro-fitting past runs. Not for one-off generation.
---

# AI 生图工作流实验室

把 AI 生图工作流当作长期研究项目运行。唯一目标：**每轮会话的上下文成本固定在 200 行以内，与项目总时长无关。**

## 第一步：建立目录

在工作机上建立根目录（默认 `ai-image-lab/`），结构固定为：

```
ai-image-lab/
  AGENTS.md          # 硬纪律摘要，每次会话必读
  STATE.md           # 当前最优工作流快照，上限 80 行
  BACKLOG.md         # 实验队列，一行一条
  LESSONS.md         # 已证实结论，只增不改，一行一条带证据
  workflows/         # vNN.json + env-vNN.json（环境快照）
  runs/E0NN/         # record.md、params.json、error.log、out/
  refs/              # 参考图与 refs.csv（含 meta_level 列）
  scripts/inventory.py
```

模板在 `assets/templates/`，复制到根目录后改名。`scripts/inventory.py` 扫描历史图并导出元数据清单，纯标准库，无第三方依赖。

## 六条硬纪律

1. **图片永不进主上下文。** 看图交给子 agent 或用户本人，只回传不超过 150 字的结构化判定（主体、手部、文字、构图、风格，各 0-2 分）。一张图几千 token，这是第一号黑洞。
2. **日志只 grep 不整读。** 命令输出重定向到 `runs/E0NN/error.log`，只 grep `Error|Traceback|OOM|CUDA`。
3. **工作流 JSON 不整读。** 只读本轮要改的节点，其余用 `params.json` 参数表代替。
4. **一次会话只做一个实验。** 做完立刻写回，再开新会话。同一会话做到第三个实验必须停下。
5. **每轮必须写回。** 不写回的实验等于没做。收场更新 `STATE.md` 三处：版本号、新结论、下一件事。
6. **只信文件不信记忆。** 不用"你还记得吗"，只说"读 `STATE.md`"。

## 会话协议

开场只读三个文件，总行数控制在 300 行内：`AGENTS.md`、`STATE.md`、`runs/` 下最新一条 `record.md`。完整开场与收场提示词见 `references/session-protocol.md`。

收场必须完成四件事：写 `record.md`、把可复现的结论追加到 `LESSONS.md`、更新 `STATE.md`、只回三行摘要。**收场是整套系统的命门，漏了它下次会话就是新人。**

## 实验设计

单变量、固定种子集、固定样本数、固定评分卡，每次只改一个维度。评分卡必须带锚点图，否则分数每轮漂移。完整规则见 `references/experiment-design.md`。

## 自动分数只做粗筛

任何自动指标（VQAScore、ImageReward、美学分）只用来淘汰最差的一批，不得用来选冠军，最终判定由人做。理由与用法见 `references/experiment-design.md`。

## 历史工作怎么接进来

不要编年史，只提资产：可复现工作流、好图、踩坑、提示词片段。四个会话分步做，见 `references/legacy-migration.md`。第一步永远是跑 `scripts/inventory.py` 出清单，不是看图。

## 工具栈

MLflow 记"发生过什么"，DVC 记"当时用了什么"，环境快照保证"现在还能跑"。分期上线，不要一次装完，见 `references/tooling-stack.md`。

## 拒绝执行的情形

- 要求"一次把历史全部整理进来"：先说明上下文成本，只做资产提取。
- 要求在同一会话里连跑多个实验：先收场，再开新会话。
- 要求用自动分数直接判定重跑：改为粗筛后人看。
- 要求在一个基线版本上同时改多个参数：拆成多次单变量实验。
