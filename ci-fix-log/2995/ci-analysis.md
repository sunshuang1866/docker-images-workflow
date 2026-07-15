# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本Windows换行符
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包内置测试脚本）
- 失败原因: CI 检查阶段的测试脚本 `bwa_test.sh` 含有 Windows 换行符（CRLF，日志中显示为 `^M`），导致 shebang 行 `#!/bin/sh` 被内核解析为 `#!/bin/sh\r`，系统找不到 `/bin/sh\r` 这个解释器，报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
**此次失败与 PR 变更无关。** Docker 镜像构建阶段完全成功：
- `#7 DONE 199.0s` — Dockerfile 中所有步骤（yum 安装依赖、下载源码、编译 bwa、卸载构建工具）均正常完成
- `#8 DONE 8.4s` — 镜像导出并推送至 `****test/bwa:0.7.18-oe2403sp4-x86_64` 成功
- `[Build] finished` / `[Push] finished` — eulerpublisher 确认构建和推送完成

失败仅发生在构建完成后的 `[Check]` 阶段，且根因是 eulerpublisher 工具包自带的 `bwa_test.sh` 测试脚本存在 Windows 换行符（CRLF），属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
CI 维护人员需要对 eulerpublisher 包中的 `tests/container/app/bwa_test.sh` 文件进行换行符转换（CRLF → LF），可使用 `dos2unix` 或在安装包构建阶段用 `sed` 处理。该修复不涉及本 PR 的任何代码变更。

## 需要进一步确认的点
- 确认 eulerpublisher 包中 `bwa_test.sh` 的源文件是否在仓库中有 Windows 换行符问题，或是安装/部署过程中被意外转换
- 确认该测试脚本在其他镜像（如非 bwa 镜像）的 CI 检查中是否也会触发同样的错误（如果是，说明是 eulerpublisher 包的通用缺陷）
