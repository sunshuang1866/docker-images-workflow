# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符问题
- 新模式症状关键词: `bad interpreter`, `^M`, `No such file or directory`, `/bin/sh^M`, DOS line endings, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 工具 eulerpublisher 内置测试脚本）
- 失败原因: CI 基础设施工具 `eulerpublisher` 中的 `bwa_test.sh` 测试脚本文件包含了 Windows 风格的换行符（CRLF，即 `\r\n`）。Linux shell 解析 shebang 行 `#!/bin/sh` 时将末尾的 `\r`（显示为 `^M`）也当作解释器路径的一部分，导致系统尝试查找 `/bin/sh^M` 这个不存在的文件，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联

**与 PR 无关。** PR #2995 仅新增了 bwa 0.7.18 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（`HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`）及相关元数据更新（README.md、image-info.yml、meta.yml）。Docker 镜像的构建和推送均已完成且成功（日志中可见 `#7 DONE 199.0s`、`[Build] finished`、`[Push] finished`）。

失败发生在 CI 流水线的 `[Check]` 阶段，该阶段调用 `eulerpublisher` 包内置的 `bwa_test.sh` 测试脚本。该测试脚本是 CI 基础设施的一部分，不属于本次 PR 的变更内容，其 Windows 换行符问题是 CI 环境的既有缺陷。

## 修复方向

### 方向 1（置信度: 高）
修复 CI 基础设施中 `eulerpublisher` 包的 `bwa_test.sh` 文件，将其换行符从 DOS/Windows 格式（CRLF）转换为 Unix 格式（LF）。可以通过 `dos2unix` 命令或在 CI runner 上执行 `sed -i 's/\r$//' bwa_test.sh` 完成。此修复应在 `eulerpublisher` 包的安装阶段进行，而非在 PR 中修改 Dockerfile。

### 方向 2（置信度: 中）
如果 `eulerpublisher` 包的测试脚本是从某个上游仓库克隆生成的（日志显示 `Cloning into 'eulerpublisher'...`），需要检查上游仓库中 `tests/container/app/bwa_test.sh` 文件的换行符格式，在上游修复后再重新部署到 CI 环境。

## 需要进一步确认的点

1. `eulerpublisher` 包中 `bwa_test.sh` 的来源——是从某个 Git 仓库克隆还是作为 Python 包安装的？需要确认其版本和分发渠道。
2. 该测试脚本是否对所有 bwa 标签（包括已存在且通过测试的 `0.7.18-oe2203sp3`）都存在此问题，还是仅对新标签触发。如果旧标签也能通过测试，则问题可能不在脚本本身，而在于 CI 执行新版本时的文件复制/克隆环节引入了换行符转换。
