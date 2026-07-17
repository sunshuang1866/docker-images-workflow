# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: /bin/sh^M: bad interpreter, No such file or directory, CRLF, carriage return

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段 — eulerpublisher 包内测试脚本 `bwa_test.sh`
- 失败原因: CI 基础设施中的 `bwa_test.sh` 测试脚本包含 Windows 风格行尾（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh\r` 被内核解析为解释器路径 `/bin/sh\r`（含回车符），系统找不到该文件，抛出 `bad interpreter` 错误。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了以下文件：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新的 Docker 构建文件）
- 更新了 `README.md`、`doc/image-info.yml`、`meta.yml`

Docker 镜像构建和推送均已成功完成（日志中 `[Build] finished`、`[Push] finished` 均正常输出，BuildKit `#7 DONE 199.0s`、`#8 DONE 8.4s`）。失败仅发生在 CI 框架的 [Check] 后处理阶段，该阶段调用了 `eulerpublisher` Python 包中预置的 `bwa_test.sh`，该脚本本身带有 Windows 行尾（CRLF），属于 CI 基础设施缺陷，非 PR 代码引起。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需要对 `eulerpublisher` 包中的 `tests/container/app/bwa_test.sh` 执行行尾转换，将 CRLF 转为 LF：
- 使用 `dos2unix` 或 `sed -i 's/\r$//'` 修复该文件
- 重新打包/发布 eulerpublisher 包，或在 CI 流水线中增加预检查步骤

此修复不涉及 PR 代码变更，Code Fixer 无需处理。

## 需要进一步确认的点
- `eulerpublisher` 包中 `bwa_test.sh` 的来源（是打包时从哪个仓库/分支引入的），确认上游是否已修复
- 检查 CI runner 的 git 配置（`core.autocrlf`），排除因 git 自动转换引入 CRLF 的可能性
- 确认同批次其他 bwa 相关镜像（如 22.03-lts-sp3 版本）的 CI 构建是否也出现相同问题——如果之前成功而本次失败，说明 eulerpublisher 包最近更新引入了该问题

## 修复验证要求
无。此失败为 CI 基础设施问题（infra-error），与 PR 代码无关，Code Fixer 无需提交代码修复。
