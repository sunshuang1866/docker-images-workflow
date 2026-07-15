# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: bad interpreter, ^M, bwa_test.sh, No such file or directory

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: eulerpublisher CI [Check] 阶段，`bwa_test.sh` 测试脚本
- 失败原因: CI 测试脚本 `bwa_test.sh` 的 shebang 行使用 Windows 风格换行符（CRLF，即 `\r\n`），导致 `#!/bin/sh` 被系统解析为 `#!/bin/sh\r`，`/bin/sh\r` 不是有效的解释器路径，Shell 报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**与 PR 代码变更无直接关联。** PR 仅新增了 bwa 0.7.18 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及对应元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像构建阶段**完全成功**：所有 7 个构建步骤（依赖安装、源码下载、编译、清理）均通过，镜像构建成功并推送到 registry（`#8 DONE 8.4s`，`[Build] finished`，`[Push] finished`）。失败仅发生在构建完成后的 `[Check]` 验证阶段——CI 框架的测试脚本 `bwa_test.sh` 自身存在换行符格式问题，与任何 PR 代码无关。

## 修复方向

### 方向 1（置信度: 高）
修复 `eulerpublisher` 包中 `tests/container/app/bwa_test.sh` 文件的换行符格式，将 CRLF 转换为 LF。可使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理该脚本文件。此修复应在 `eulerpublisher` 仓库中提交，无需修改当前 PR 的任何代码文件（Dockerfile、meta.yml 等）。

## 需要进一步确认的点
- 确认 `bwa_test.sh` 的实际来源：是 `eulerpublisher` 仓库内文件（`git clone` 获取），还是 CI 运行时从外部动态下载。若是后者，需检查下载源文件的换行符格式。
- 如果是 `eulerpublisher` 仓库中的静态文件，确认是否有其他应用的测试脚本也存在相同 CRLF 问题（可批量检查 `tests/container/app/` 目录下所有 `.sh` 文件的换行符格式）。
