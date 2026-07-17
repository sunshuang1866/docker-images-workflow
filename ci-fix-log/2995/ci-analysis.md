# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符错误
- 新模式症状关键词: bad interpreter, /bin/sh^M, CRLF, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

Docker 构建和推送阶段均已成功完成：
```
#8 DONE 8.4s
2026-07-10 11:58:05,860 - INFO - [Build] finished
2026-07-10 11:58:05,860 - INFO - [Push] finished
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 测试脚本，非 PR 变更文件）
- 失败原因: CI 基础设施 eulerpublisher 包中的 `bwa_test.sh` 测试脚本包含 Windows 风格换行符（CRLF），shebang 行 `#!/bin/sh` 末尾的 `\r`（显示为 `^M`）被内核误读为解释器路径的一部分（`/bin/sh\r`），导致脚本无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了以下文件：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新 Dockerfile）
- `HPC/bwa/README.md`（补充版本记录）
- `HPC/bwa/doc/image-info.yml`（补充镜像信息）
- `HPC/bwa/meta.yml`（新增 meta 条目）

Docker 镜像构建（含编译 BWA 0.7.18）和推送均已完成且成功，失败仅发生在 CI [Check] 阶段的测试脚本执行环节，根因是 eulerpublisher CI 工具包自带的 `bwa_test.sh` 测试脚本存在换行符格式问题。

## 修复方向

### 方向 1（置信度: 高）
修复 CI 基础设施中 eulerpublisher 包的 `bwa_test.sh` 测试脚本，将其从 CRLF（Windows）换行格式转换为 LF（Unix）换行格式。可通过 `dos2unix` 或 `sed -i 's/\r$//'` 处理。此修复属于 CI 基础设施层面，**无需修改该 PR 的任何代码**。

## 需要进一步确认的点
无需进一步确认。日志中错误信息明确指向测试脚本的换行符问题，Docker 构建过程完整无报错，根因清晰。

## 修复验证要求
无需验证。修复仅涉及 CI 基础设施中测试脚本的换行符格式转换，不影响 PR 代码。
