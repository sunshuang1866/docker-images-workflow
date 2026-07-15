# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: `/bin/sh^M`, `bad interpreter`, `bwa_test.sh`, `eulerpublisher`, `CRITICAL: [Check] test failed`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 工具 `eulerpublisher` 内置测试脚本）
- 失败原因: `eulerpublisher` 包中的 `bwa_test.sh` 测试脚本包含 Windows 风格行尾（CRLF），导致 shebang 行 `#!/bin/sh\r` 中的回车符 `\r`（日志中显示为 `^M`）被解析为解释器路径的一部分。Linux 无法找到名为 `/bin/sh\r` 的解释器，因此报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联

**与 PR 无关。** 本次 PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`、更新 `meta.yml`、`README.md`、`image-info.yml` 共 4 个文件。Docker 镜像构建和推送均已完成并成功（日志中 `[Build] finished` 和 `[Push] finished` 均正常，`#7 DONE 199.0s`、`#8 DONE 8.4s`），失败仅发生在 CI 工具的 `[Check]` 阶段——该阶段调用 `eulerpublisher` 包中预置的 `bwa_test.sh` 测试脚本时，因脚本本身存在 CRLF 行尾问题而无法执行。

## 修复方向

### 方向 1（置信度: 高）
CI 工具 `eulerpublisher` 仓库中的 `tests/container/app/bwa_test.sh` 文件被以 CRLF 行尾提交，导致 CI runner（Linux 环境）无法执行该脚本。需在 `eulerpublisher` 仓库中修复该文件的行尾格式（转为 LF），或确保 `.gitattributes` 配置正确，防止该文件在克隆时被转换为 CRLF。

## 需要进一步确认的点
- 确认 `eulerpublisher` 仓库中 `tests/container/app/bwa_test.sh` 的上游源文件行尾格式，以及最近是否有新增或修改该测试脚本的提交引入了 CRLF。
- 确认 CI runner 上 `git clone` `eulerpublisher` 时是否配置了 `core.autocrlf` 导致行尾转换。
