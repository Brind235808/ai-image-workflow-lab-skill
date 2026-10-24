# ai-image-workflow-lab-skill

长期管理 AI 生图工作流研发项目的 agent skill：用文件做外部记忆，让每轮会话的上下文成本固定在 200 行以内，而不是随着项目变长而爆掉。

适用于 ComfyUI 及各类扩散模型的提示词、参数、工作流迭代，以及历史产出的复古归档。

## 解决什么问题

生图研究和普通编码不同：一次要看的图、几百行的工作流 JSON、动辄上千行的报错日志，都是 token 黑洞。做完一两个任务，上下文就满了，后面的改进全部作废。

这个 skill 的核心做法是：**agent 只读结论，原始材料留在磁盘上按需检索。**

## 结构

```
SKILL.md                        # 主体：目录契约 + 六条硬纪律
references/
  session-protocol.md           # 开场/收场提示词、读预算、子 agent 看图协议
  experiment-design.md          # 单变量实验、评分卡、种子决策树、自动指标政策
  legacy-migration.md           # 历史产出复古：四个会话、资产提取、A/B 分级
  tooling-stack.md              # MLflow / DVC / 环境快照 / FiftyOne / Optuna 分期
assets/templates/               # AGENTS.md、STATE.md、BACKLOG.md、LESSONS.md、record.md
scripts/inventory.py            # 扫描历史图并导出元数据清单（纯标准库）
```

## 快速开始

1. 把 `assets/templates/` 里的文件复制到你的工作目录并改名。
2. 用 `scripts/inventory.py` 扫一遍历史图片，得到 `inventory.csv`。
3. 按 `references/legacy-migration.md` 的四个会话流程建出基线。
4. 之后每轮按 `references/session-protocol.md` 的开场/收场提示词执行。

## 安装

把本仓库放到 agent 的 skills 目录即可，目录名需与 `SKILL.md` 里的 `name` 一致。

## License

MIT
