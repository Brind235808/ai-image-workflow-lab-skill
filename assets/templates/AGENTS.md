# 操作纪律

每次会话开始，按顺序读：本文件 → `STATE.md` → `runs/` 下最新一条 `record.md`。总行数不超过 300。

1. 图片不进主上下文。看图派子 agent，只回传不超过 150 字的结构化判定。
2. 日志只 grep 不整读。输出重定向到 `runs/E0NN/error.log`，grep `Error|Traceback|OOM|CUDA`。
3. 工作流 JSON 不整读，只读本轮要改的节点。
4. 一次会话只做一个实验。做到第三个实验必须停下。
5. 每轮必须写回。收场更新 `STATE.md` 的版本号、新结论、下一件事。
6. 只信文件不信记忆。不说"你还记得吗"，只说"读 STATE.md"。

会话结束前必须执行收场四件事：写 `record.md`、追加 `LESSONS.md`、更新 `STATE.md`、只回三行摘要。
