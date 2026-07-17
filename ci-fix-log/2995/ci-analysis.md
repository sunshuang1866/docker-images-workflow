# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符错误
- 新模式症状关键词: ^M, bad interpreter, No such file or directory, /bin/sh^M, CRLF

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI eulerpublisher 工具内置测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`
- 失败原因: 该测试脚本文件包含 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh` 末尾携带不可见回车符 (`\r`，即 `^M`)。系统尝试查找 `/bin/sh\r` 作为解释器，因该路径不存在而报 `bad interpreter` 错误。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 仅新增了以下文件：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新 Dockerfile）
- `HPC/bwa/README.md`（添加版本条目）
- `HPC/bwa/doc/image-info.yml`（添加版本条目）
- `HPC/bwa/meta.yml`（添加版本条目）

Docker 镜像构建、推送阶段全部成功（日志中 `#7 DONE 199.0s`、`#8 DONE 8.4s`、`[Build] finished`、`[Push] finished`），bwa 源码在 openEuler 24.03-LTS-SP4 上编译通过且无任何错误。失败仅发生在 CI 基础设施的 post-build 检查阶段，原因是 eulerpublisher 工具包内置的 `bwa_test.sh` 脚本文件本身携带了 Windows 换行符。

## 修复方向

### 方向 1（置信度: 高）
由 CI 运维人员修复 eulerpublisher 包中的 `bwa_test.sh` 文件：将其行尾格式从 CRLF 转换为 LF（Unix 换行符），例如通过 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件后重新安装或更新 eulerpublisher 包。这不是本 PR 代码可修复的问题。

## 需要进一步确认的点
- 确认 eulerpublisher 包中 `bwa_test.sh` 文件的实际换行符格式（`file` 命令或 `cat -A` 查看是否存在 `^M`）。
- 确认该测试脚本是否同时存在于 aarch64 构建节点上（若 aarch64 构建 job 也有同样的检查步骤，预计也会触发相同错误）。
- 若 eulerpublisher 包由 Git 仓库管理，需确认其仓库中该文件的行尾设置（`.gitattributes` 或编辑器配置）是否正确。

## 修复验证要求
无需 code-fixer 参与。此问题为 CI 基础设施（eulerpublisher 工具包内置测试脚本的换行符格式问题），应由 CI 运维侧修复，不属于 PR 代码变更范畴。
