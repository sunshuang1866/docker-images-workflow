# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本含CRLF换行
- 新模式症状关键词: /bin/sh^M, bad interpreter, No such file or directory, bwa_test.sh, CRLF

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 工具 `eulerpublisher` 自带的测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（shebang 行）
- 失败原因: `bwa_test.sh` 文件使用了 Windows 风格的 CRLF 换行（`\r\n`），导致 shebang 行变为 `#!/bin/sh\r`。Linux 内核尝试查找解释器 `/bin/sh\r`（含回车符 `^M`），该文件不存在，触发 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**无关联。** 该 PR 仅新增了 bwa 0.7.18 的 Dockerfile（`HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`）及配套元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像构建阶段完全成功：yum 安装依赖 → 下载源码 → `make` 编译 → 打包 → 推送镜像，全过程 `#7 DONE 199.0s`，无任何编译错误或构建失败。失败发生在 Build & Push 完成之后的 `[Check]` 阶段，由 `eulerpublisher` 测试框架的自身缺陷（脚本文件换行格式错误）导致，与 PR 代码变更完全无关。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需要修复 `eulerpublisher` 包内 `tests/container/app/bwa_test.sh` 的换行格式：将文件从 CRLF 转换为 LF。可使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理。此修复不属于本 PR 范围，Code Fixer 无需处理。

## 需要进一步确认的点
- 确认 `bwa_test.sh` 在 `eulerpublisher` 包的哪个版本中被引入，检查该包的上游仓库中该文件是否已存在 CRLF 问题。
- 确认 CI runner（`ecs-build-docker-x86-hk`）上安装的 `eulerpublisher` 包版本，以定位需要修复的包版本。
- 确认此问题是否仅影响 `bwa_test.sh`，还是 `eulerpublisher/tests/container/app/` 目录下其他测试脚本也存在同样换行问题。
