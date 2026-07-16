# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, /bin/sh^M

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段，尝试执行 eulerpublisher 内置测试脚本 `bwa_test.sh` 时
- 失败原因: eulerpublisher 工具包中自带的 `bwa_test.sh` 测试脚本文件使用 Windows 风格换行符（CRLF），shebang 行 `#!/bin/sh` 末尾附带了不可见的回车符 `\r`（日志中显示为 `^M`），导致内核将解释器路径解析为 `/bin/sh\r`，查找不到该文件，脚本无法执行

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 bwa 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像的构建和推送阶段全部成功（`#7 DONE 199.0s`，`#8 DONE 8.4s`，`[Build] finished`，`[Push] finished`）。失败发生在 CI 流水线的 [Check] 测试阶段，该阶段调用 eulerpublisher 工具包预置的 `bwa_test.sh`，该测试脚本自身因 CRLF 换行符损坏而无法执行。这是一个 CI 基础设施层面的缺陷。

## 修复方向

### 方向 1（置信度: 高）
CI 运维团队需要修复 eulerpublisher Python 包中自带的 `tests/container/app/bwa_test.sh` 文件，将文件换行符从 DOS/Windows 风格（CRLF）转换为 Unix 风格（LF）。可以使用 `dos2unix` 或 `sed -i 's/\r$//'` 命令处理该文件并重新打包发布 eulerpublisher 到 CI runner。

### 方向 2（置信度: 低）
如果 eulerpublisher 的 bwa_test.sh 是从某个上游 Git 仓库动态拉取生成到 `/usr/local/etc/eulerpublisher/tests/` 目录的，则需要追溯到该上游仓库，修复源文件中的换行符问题。

## 需要进一步确认的点
1. 确认 eulerpublisher 包中 `bwa_test.sh` 文件的来源——是 pip 安装时静态打包的，还是在 CI 运行时从某仓库动态克隆的
2. 确认同一 eulerpublisher 版本的 `tests/container/app/` 目录下是否还有其他测试脚本存在同样的 CRLF 问题（如 `bwa_test.sh` 被发现，其他脚本可能也被污染）
3. 确认本 PR 的 aarch64 架构构建 job 是否也因同一原因失败（本日志仅为 x86_64 job）
