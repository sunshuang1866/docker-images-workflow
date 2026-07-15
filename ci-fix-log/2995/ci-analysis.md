# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符错误
- 新模式症状关键词: `bad interpreter`, `No such file or directory`, `^M`, CRLF, shebang

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: eulerpublisher 内置测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`
- 失败原因: 该测试脚本文件使用 Windows 风格换行符（CRLF，`\r\n`），导致 shebang 行 `#!/bin/sh` 末尾携带不可见的回车符 `\r`（日志中显示为 `^M`）。系统将 `/bin/sh\r` 视为解释器路径，该路径不存在，因此报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了以下文件：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新 Dockerfile，构建成功）
- `HPC/bwa/README.md`、`HPC/bwa/doc/image-info.yml`、`HPC/bwa/meta.yml`（元数据更新）

Docker 镜像构建和推送阶段均已成功完成（`[Build] finished`、`[Push] finished`），失败发生在 CI 基础设施（eulerpublisher）的 `[Check]` 测试阶段，原因是 eulerpublisher 工具包中捆绑的 `bwa_test.sh` 脚本文件本身带有 Windows 换行符。

## 修复方向

### 方向 1（置信度: 高）
这是 eulerpublisher CI 工具的缺陷（`bwa_test.sh` 打包时未做换行符规范化），不是 PR 代码问题。需要由 eulerpublisher 维护者修复该测试脚本的换行符（将 CRLF 转换为 LF），或 CI 管理员在测试执行前对脚本做 `dos2unix` 处理。**Code Fixer 无需操作本仓库中的任何文件。**

## 需要进一步确认的点
- `bwa_test.sh` 位于 eulerpublisher pip 包的安装目录中，需确认该文件是在 eulerpublisher 打包时就携带了 CRLF，还是在 CI runner 上运行时被意外转换。建议检查 eulerpublisher 源码仓库中 `tests/container/app/bwa_test.sh` 的实际换行符格式。
- 确认其他应用镜像（非 bwa）的 `[Check]` 阶段是否也会命中同样的 CRLF 问题，以判断这是 bwa 专属测试脚本的孤立问题，还是 eulerpublisher 整体打包流程的缺陷。
