# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: /bin/sh^M, bad interpreter, No such file or directory, CRLF

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 测试基础设施中的 bwa 检查脚本）
- 失败原因: eulerpublisher 包中内置的 `bwa_test.sh` 测试脚本使用 Windows 风格换行符（CRLF），导致 shebang 行被解析为 `/bin/sh^M`，操作系统无法找到该解释器，测试执行失败。

### 与 PR 变更的关联
**与本次 PR 变更无关。** 该 PR 仅新增了 bwa 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像构建阶段已完全成功：源码下载、编译（gcc 编译 bwa 0.7.18 全量 .c 文件通过，仅有 2 个无害的 GCC warning）、镜像推送均正常完成（`#7 DONE 199.0s`，`[Build] finished`，`[Push] finished`）。失败发生在构建完成后的 CI [Check] 阶段，因 eulerpublisher 测试框架内置的 `bwa_test.sh` 脚本自身存在 CRLF 换行符问题，与 PR 的代码变更完全无关。

### 补充说明
Docker 构建日志全程无任何编译错误或构建失败迹象。唯一可见的编译输出为 bwt_gen.c 中的 2 个 `-Wunused-but-set-variable` 警告（`oldInverseSa0RelativeRank` 和 `bitsInWordMinusBitPerChar`），属于上游源码既有的无害警告，不影响构建结果。

## 修复方向

### 方向 1（置信度: 高）
`bwa_test.sh` 的 CRLF 换行符问题。该脚本属于 eulerpublisher CI 工具包（安装路径 `/etc/eulerpublisher/tests/container/app/`），需要在其源码仓库中将该文件的行尾序列从 CRLF 转换为 LF（Unix 风格），然后重新发布 eulerpublisher 包。这不是 PR 作者侧可以修复的问题。

## 需要进一步确认的点
- 确认 `eulerpublisher` 源码仓库中 `tests/container/app/bwa_test.sh` 文件的换行符格式，以及在 CI runner 上安装的 eulerpublisher 包版本是否过时。
- 确认同一个 CI runner 上其他镜像（如其他 HPC 镜像）的检查脚本是否也存在同样的 CRLF 问题，这对评估影响范围有帮助。

## 修复验证要求
不适用。本失败为 infra-error，与 PR 代码变更无关，无需 code-fixer 对 PR 文件做任何修改。
