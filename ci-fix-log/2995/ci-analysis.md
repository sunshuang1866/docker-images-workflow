# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: `bad interpreter, ^M, /bin/sh^M, bwa_test.sh`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI Check 阶段——`/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包中的测试脚本）
- 失败原因: `bwa_test.sh` 文件的 shebang 行（`#!/bin/sh`）末尾带有 Windows 回车符（`\r`，日志中显示为 `^M`），导致 Linux 内核将解释器路径解析为 `/bin/sh\r`（含回车字符），该路径不存在，因此报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**与 PR 无关。** PR 的 Docker 镜像构建全部成功（#7 DONE 199.0s， [Build] finished，[Push] finished），镜像已正确构建并推送至 `****test/bwa:0.7.18-oe2403sp4-x86_64`。失败发生在 CI 基础设施的 eulerpublisher 工具链中——`bwa_test.sh` 测试脚本以 CRLF（Windows）换行符存储在 eulerpublisher 软件包中，与本次 PR 新增的 Dockerfile 以及任何代码变更均无直接关联。

PR 仅新增了 4 个文件（Dockerfile、README.md 更新、image-info.yml 更新、meta.yml 更新），这些文件的 Docker 构建阶段均未出现错误。

## 修复方向

### 方向 1（置信度: 高）
将 eulerpublisher 软件包中 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（以及同目录下其他可能存在相同问题的测试脚本）的换行符从 CRLF（`\r\n`）转换为 LF（`\n`）。修复操作需在 eulerpublisher 上游仓库中进行，而非在本 PR 仓库中。

验证方法：使用 `dos2unix` 或 `sed -i 's/\r$//'` 转换该文件后重新打包 eulerpublisher，确保 CI 节点上安装的新版本不再包含 CRLF。

## 需要进一步确认的点
1. `bwa_test.sh` 是否在 eulerpublisher 仓库中被最近提交引入且带有 CRLF？还是该文件已存在一段时间但之前未被触发执行（例如之前没有 bwa 的 24.03-lts-sp4 镜像需要检查，因此该脚本从未被执行过）？
2. eulerpublisher 仓库中是否还有其他应用的测试脚本也存在同样的 CRLF 问题（如 `bwa_test.sh` 同目录下的 `*.sh` 文件）？
3. 若该脚本来自 Git 仓库（eulerpublisher），需确认该仓库的 `.gitattributes` 是否配置了 `text=auto` 或对 `*.sh` 文件强制执行 LF 换行符。
