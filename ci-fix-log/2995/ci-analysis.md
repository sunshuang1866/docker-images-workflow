# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符错误
- 新模式症状关键词: bad interpreter, No such file or directory, ^M, CRLF, bwa_test.sh, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `eulerpublisher` 工具内置测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施文件，非 PR 代码，路径源自 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`）
- 失败原因: CI 工具 `eulerpublisher` 中用于验证 BWA 镜像的测试脚本 `bwa_test.sh` 采用了 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh\r\n` 被内核误解析为寻找 `/bin/sh\r` 解释器，该路径不存在，触发 `bad interpreter` 错误。

### 与 PR 变更的关联
**与 PR 代码变更无关。**

PR 仅新增/修改了以下文件：
1. `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新增）
2. `HPC/bwa/README.md`（添加镜像 tag 说明）
3. `HPC/bwa/doc/image-info.yml`（添加镜像条目）
4. `HPC/bwa/meta.yml`（添加 meta 条目）

Docker 镜像构建本身**已成功完成**（`[Build] finished`、`[Push] finished`，所有 RUN 步骤均通过）。失败仅发生在 CI 的 `[Check]` 阶段——该阶段调用 `eulerpublisher` 工具预装的系统级测试脚本 `bwa_test.sh`，该脚本本身存在 CRLF 换行符缺陷。

## 修复方向

### 方向 1（置信度: 高）
`eulerpublisher` 工具包中的 `bwa_test.sh` 测试脚本使用了 Windows 换行符（CRLF）。CI 基础设施维护者需将 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 转换为 Unix 换行符（LF），例如在生成/部署该脚本时执行 `dos2unix` 或 `sed -i 's/\r$//'`。

### 方向 2（置信度: 低）
如果 `bwa_test.sh` 是从仓库中的某个模板文件动态生成的，需检查模板源文件的换行符是否为 LF。

## 需要进一步确认的点
1. `bwa_test.sh` 是 `eulerpublisher` Python 包安装时写入的静态文件，还是由 CI 流程从仓库中动态复制/生成的？这决定修复应在 `eulerpublisher` 项目中还是在本仓库中进行。
2. 本日志仅覆盖 x86-64 构建 job（`multiarch/openeuler/x86-64/openeuler-docker-images`），若 PR 仍处于 CI 失败状态，需获取 aarch64 架构对应 job 的日志以确认是否存在其他问题。
3. 该 `bwa_test.sh` CRLF 问题是否影响其他已有的 BWA 镜像版本（如 `0.7.18-oe2203sp3`）的 CI 检查，还是仅影响此次新增的 sp4 版本。如果仅影响 sp4，可能意味着测试脚本是最近才添加/更新的。

## 修复验证要求
本失败为 infra-error，Code Fixer 无需修改 PR 代码。若 CI 团队修复了 `bwa_test.sh` 换行符问题，仅需重新触发 CI 流水线验证即可。Code Fixer 不需要执行任何源代码修改。
