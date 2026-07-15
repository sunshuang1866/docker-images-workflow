# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾符
- 新模式症状关键词: bad interpreter, ^M, /bin/sh^M, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 的 `[Check]` 阶段，运行测试脚本 `bwa_test.sh` 时
- 失败原因: eulerpublisher 包中的测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 包含 Windows 风格的 CRLF 行尾符（`\r\n`），导致 shell 将 shebang 解释为 `/bin/sh^M`（`^M` 是回车符 `\r`），系统找不到该解释器，脚本无法执行。Docker 镜像的构建（`[Build]`）和推送（`[Push]`）阶段均已成功完成。

### 与 PR 变更的关联
**无关联。** PR 仅新增了 bwa 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件。Docker 构建阶段日志清晰显示：
- yum 安装依赖成功（17 个包全部安装完毕：`Complete!`）
- 源码下载和解压成功（所有 `.c` / `.h` 文件已列出）
- C 编译成功（所有 `.o` 文件编译通过，仅有两个上游 GCC 警告：`-Wunused-but-set-variable` 在 `bwt_gen.c:879` 和 `bwt_gen.c:953`）
- 链接生成二进制 `bwa` 成功
- 清理构建依赖成功（17 个包全部移除：`Complete!`）
- 镜像导出和推送成功（`[Build] finished`、`[Push] finished`）

失败仅发生在 eulerpublisher 工具运行 `bwa_test.sh` 的 `[Check]` 阶段，该脚本不属于 PR 变更文件。

## 修复方向

### 方向 1（置信度: 中）
`bwa_test.sh` 文件的行尾格式错误（CRLF 而非 LF）。需检查 eulerpublisher 源码仓库中 `tests/container/app/bwa_test.sh` 的行尾格式，将其从 CRLF 转为 LF。此修复应在 eulerpublisher 仓库侧完成，与当前 PR 的 Dockerfile 变更无关。

## 需要进一步确认的点
1. 确认 `bwa_test.sh` 脚本的来源——是否来自 eulerpublisher 的 Python 包安装路径，还是从某处克隆后拷贝到 `/etc/eulerpublisher/tests/container/app/` 下。
2. 检查同一 CI 流水线中已有的 bwa 22.03-lts-sp3 镜像是否也会触发同一测试脚本、并因此失败。如果此前 bwa 22.03-lts-sp3 的 CI 从未运行过 `[Check]` 阶段（或从未触发 `bwa_test.sh`），说明此问题是本次才暴露的 latent infra bug，而非 PR 引发的新问题。
3. 若 eulerpublisher 仓库中还有类似格式问题的测试脚本（其他镜像的 `*_test.sh`），需要一并修复。
