# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本含CRLF行尾
- 新模式症状关键词: ^M, bad interpreter, No such file or directory, CRLF, bwa_test.sh, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段执行 `bwa_test.sh` 时
- 失败原因: eulerpublisher CI 工具安装的 `bwa_test.sh` 测试脚本使用了 Windows 风格行尾（CRLF），其 shebang 行 `#!/bin/sh\r` 中多余的 `\r`（日志显示为 `^M`）导致系统尝试查找解释器 `/bin/sh\r`（不存在），触发 "bad interpreter" 错误。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建和推送均已成功完成（日志中明确显示 `[Build] finished` 和 `[Push] finished`），所有 7 个构建步骤全部通过。失败仅发生在 CI 后处理阶段的 [Check] 步骤，原因是 eulerpublisher Python 包自带的 `bwa_test.sh` 脚本文件含有 CRLF 行尾——该文件属于 CI 基础设施组件，非 PR 提交的文件。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需要修复 eulerpublisher 包中 `tests/container/app/bwa_test.sh` 文件的行尾格式，将 CRLF 转换为 LF（Unix 风格）。可使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件后重新发布 eulerpublisher 包。

### 方向 2（置信度: 中）
若方向 1 不可行（如无法立即更新 eulerpublisher 包），可在 CI 流程中增加预处理步骤：在调用 `bwa_test.sh` 前用 `sed -i 's/\r$//'` 自动修复文件行尾。但这是临时绕过方案，不应作为长期修复。

## 需要进一步确认的点
1. 确认 eulerpublisher 包中 `bwa_test.sh` 是否由 CI 流程自动生成（若从 Git 仓库克隆，需检查源仓库中该文件的行尾格式）
2. 确认同一 eulerpublisher 包中的其他 `*_test.sh` 文件是否也存在 CRLF 问题（若存在，说明是打包/发布流程的系统性问题）
3. 确认该问题是否仅影响 bwa 镜像的 CI 检查，还是所有使用该版本 eulerpublisher 的镜像检查都会受影响
