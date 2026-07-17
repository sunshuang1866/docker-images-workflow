# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: `bad interpreter`, `/bin/sh^M`, `No such file or directory`, `bwa_test.sh`, `CRLF`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI 基础设施的 eulerpublisher 测试脚本 `eulerpublisher/tests/container/app/bwa_test.sh`（由 `app.py:173` 调用），实际解析路径为 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`
- 失败原因: 该测试脚本文件包含 Windows 风格 CRLF 换行符（`\r\n`），导致 shebang 行 `#!/bin/sh` 被内核解析为 `#!/bin/sh\r`，尝试以 `/bin/sh^M` 为解释器执行，因该路径不存在而报 "bad interpreter: No such file or directory"

### 与 PR 变更的关联
**与 PR 代码变更无关**。证据如下：

1. **Docker 构建完全成功**：日志显示 bwa 源码全部编译通过（gcc 编译所有 .c 文件成功，链接生成 bwa 二进制），镜像构建、导出和推送均成功（`[Build] finished`、`[Push] finished`），镜像已推送到 `docker.io/****test/bwa:0.7.18-oe2403sp4-x86_64`。
2. **失败发生在 CI Check 阶段**：构建和推送完成后，CI 框架的 Check 步骤尝试执行 `bwa_test.sh` 来验证镜像，因测试脚本自身 CRLF 换行问题而崩溃。
3. **PR 仅包含项目文件**：本次 PR 仅新增/修改 `Dockerfile`、`README.md`、`image-info.yml`、`meta.yml` 四个文件，均不涉及 CI 测试脚本。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施（eulerpublisher 包）中的 `bwa_test.sh` 测试脚本被提交或部署时携带了 CRLF 换行符。需要在 **eulerpublisher 仓库** 中将该文件的换行符从 CRLF 转换为 LF（例如使用 `dos2unix` 或 `sed -i 's/\r$//'`），然后重新部署或发布新版本的 eulerpublisher 包。

### 方向 2（置信度: 低）
如果该 `bwa_test.sh` 脚本是新创建的，可能是编写者在 Windows 环境创建后直接提交。除修复换行符外，还需检查 eulerpublisher 仓库的其他新增测试脚本是否存在同类问题。

## 需要进一步确认的点
1. **eulerpublisher 仓库中 `bwa_test.sh` 的实际内容**：需要确认该文件是否存在、其换行符格式，以及是否是首次添加。
2. **其他 bwa 相关 PR 是否也受影响**：如果是 eulerpublisher 测试脚本的通用问题，那么所有涉及 bwa 镜像的 PR 都会在同一 Check 阶段失败。
3. **CI 节点上的 eulerpublisher 包版本**：确认当前部署的 eulerpublisher 版本，判断是否需要升级包来修复。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。本次失败为 infra-error，与 PR 代码无关，无需验证正则匹配。
