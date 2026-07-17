# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符
- 新模式症状关键词: `/bin/sh^M`, `bad interpreter`, `No such file or directory`, CRLF, carriage return

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 侧 eulerpublisher 包内的测试脚本）
- 失败原因: CI 测试框架 `eulerpublisher` 中的 `bwa_test.sh` 脚本文件使用了 DOS/Windows 换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh` 末尾带上不可见的回车字符 `\r`（显示为 `^M`），内核尝试查找名为 `/bin/sh^M` 的解释器失败，报告 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联

**与 PR 变更无关。** 详细证据如下：

1. **Docker 构建完全成功**：日志显式打印了 `[Build] finished` 和 `[Push] finished`，BuildKit `#7 DONE 199.0s` 和 `#8 DONE 8.4s` 确认镜像已成功构建并推送至 `docker.io/****test/bwa:0.7.18-oe2403sp4-x86_64`。

2. **构建过程无编译错误**：bwa 源码 `make -j "$(nproc)"` 编译过程中仅有 2 条 `-Wunused-but-set-variable` 编译警告（`bwt_gen.c:879` 和 `bwt_gen.c:953`），不影响编译成功完成——最终 `gcc ... -o bwa` 链接步骤正常完成。

3. **PR 仅新增 4 个文件**（Dockerfile、README.md、image-info.yml、meta.yml），不涉及任何 CI 测试脚本的修改或新增。

4. **失败发生在 [Check] 测试阶段**：该阶段的 `bwa_test.sh` 是 eulerpublisher CI 框架安装在运行器上的 Python 包内置测试脚本（路径位于 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/`），**完全不由本次 PR 的代码控制**。该脚本文件被错误地以 CRLF 换行符保存，导致 `sh` 无法解析其 shebang 行。

## 修复方向

### 方向 1（置信度: 高）
该问题是 CI 基础设施（eulerpublisher 包中的测试脚本）的配置错误，**无需 PR 作者对 Dockerfile 做任何修改**。需由 CI 维护者将 `bwa_test.sh` 文件的换行符从 DOS（CRLF）转换为 Unix（LF），可在 eulerpublisher 源码仓库中执行 `dos2unix` 或类似工具后重新发布该 Python 包。

## 需要进一步确认的点

- 该 `bwa_test.sh` 是在 eulerpublisher 的哪个版本中引入的？其内容在提交到 eulerpublisher 仓库时是否已被 Git 的 `core.autocrlf` 破坏？
- 是否有其他应用的测试脚本（如 `nginx_test.sh`、`redis_test.sh` 等）也存在同样的 CRLF 换行问题，需要一并修复？
- eulerpublisher 仓库的 `.gitattributes` 配置是否已正确设置 `*.sh text eol=lf` 以防止同类问题复现？

## 修复验证要求

无。该问题属于 CI 基础设施侧（eulerpublisher Python 包的测试脚本换行符），code-fixer 无需对本次 PR 的任何文件进行修改。
