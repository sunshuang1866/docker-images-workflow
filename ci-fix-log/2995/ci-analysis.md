# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: bad interpreter, /bin/sh^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking .../bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 测试脚本，非 PR 代码）
- 失败原因: CI 工具链 `eulerpublisher` 中内置的 `bwa_test.sh` 测试脚本包含 Windows 风格换行符（CRLF，即 `\r\n`），其 shebang 行 `#!/bin/sh\r` 被操作系统解析为 `/bin/sh^M`（^M 即回车符 \r），内核找不到该名称的解释器，报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 证据如下：
1. Docker 镜像构建和推送均成功完成（日志中 `[Build] finished`、`[Push] finished`、`#8 DONE 8.4s`、镜像已推送并产生 sha256 manifest）。
2. 编译过程（make clean && make）仅产生无害的编译器 warning（bwt_gen.c 中未使用变量），无任何编译错误。
3. 失败发生在 CI [Check] 阶段——该阶段调用 `eulerpublisher` Python 包内置的 `bwa_test.sh` 脚本，脚本自身的 CRLF 换行问题与 PR 修改的 Dockerfile/meta.yml/README.md 完全无关。
4. PR 仅新增 4 个文件（Dockerfile、README.md 修改、image-info.yml 修改、meta.yml 修改），均不涉及 `eulerpublisher` 包或测试脚本。

## 修复方向

### 方向 1（置信度: 高）
`eulerpublisher` 包中的 `bwa_test.sh` 文件需要转换为 Unix 换行（LF）。这是 CI 基础设施层面的修复，应由 CI 运维人员执行 `dos2unix` 或等价操作处理 `eulerpublisher/tests/container/app/bwa_test.sh`，不能由 PR 作者在 Dockerfile 中修复。

## 需要进一步确认的点
- 确认 `eulerpublisher` 包中 `bwa_test.sh` 的来源——是 PyPI 发布的包本身就带 CRLF，还是 CI runner 上 `git clone` 该仓库时因 git 配置未设置 `core.autocrlf` 导致自动转换。如果是前者，需要联系 `eulerpublisher` 包维护者修复发布流程；如果是后者，需调整 CI runner 的 git 配置。
- 确认同一 `eulerpublisher` 版本在其他已通过 CI 的 bwa PR（如 22.03-lts-sp3）上是否也使用该脚本——如果是，说明该 CRLF 问题可能是近期引入的回归。

## 修复验证要求
无需验证——此失败为 CI 基础设施问题（infra-error），PR 代码本身无需修改，Code Fixer 无需处理。
