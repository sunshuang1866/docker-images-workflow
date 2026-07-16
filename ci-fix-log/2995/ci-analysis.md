# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: `bad interpreter`, `^M`, `No such file or directory`, `bwa_test.sh`, `CRLF`

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施中的测试脚本，位于 eulerpublisher 包内）
- 失败原因: `eulerpublisher` 包中自带的 `bwa_test.sh` 测试脚本使用 Windows 风格换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh\r` 中的 `\r`（显示为 `^M`）被 Shell 解释器误认为解释器路径的一部分，报告 `bad interpreter: No such file or directory`。Docker 镜像的构建和推送均已成功（`[Build] finished`、`[Push] finished`），失败仅发生在 CI [Check] 阶段执行该测试脚本时。

### 与 PR 变更的关联
PR 变更与此次失败**无关**。PR 仅新增了 bwa 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及相关元数据（README.md、image-info.yml、meta.yml）。Docker 镜像构建本身已成功完成（`#7 DONE 199.0s`），镜像成功推送到仓库。失败原因是 CI 基础设施（eulerpublisher 包）中 `bwa_test.sh` 文件本身携带了 CRLF 行尾，该文件不在 PR diff 范围内，PR 作者无法通过修改提交代码来修复。

## 修复方向

### 方向 1（置信度: 高）
由 CI 基础设施维护者修复 `eulerpublisher` 包中的 `tests/container/app/bwa_test.sh` 文件，将其行尾格式从 CRLF 转换为 LF（Unix 换行符）。可通过 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件并重新打包/更新 eulerpublisher 包。

## 需要进一步确认的点
1. `bwa_test.sh` 文件是否在所有 CI runner 节点上都存在 CRLF 问题，还是仅在本次构建使用的 runner 上被错误检出（如 Git 配置 `core.autocrlf` 导致）。
2. 同类其他应用镜像（已存在的 bwa 22.03-lts-sp3 等）的 CI 测试是否也曾遇到此问题——如果未遇到，可能本次 runner 的环境与历史构建不同，需排查 runner 的 Git 换行符配置。
3. 确认 eulerpublisher 包的来源（Git 仓库地址、安装方式），定位该测试脚本在源仓库中是否本来就包含 CRLF 行尾。
