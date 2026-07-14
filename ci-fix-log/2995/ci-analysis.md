# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CRLF行尾致脚本无法执行
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, CRLF, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `eulerpublisher` 包中的测试脚本 `bwa_test.sh`
- 失败原因: `eulerpublisher/tests/container/app/bwa_test.sh` 文件的 shebang 行（`#!/bin/sh`）包含 Windows 风格的 CRLF 行尾（`\r\n`），导致 Linux 系统将 shebang 解析为 `/bin/sh\r`（日志中显示为 `/bin/sh^M`），该解释器路径不存在，shell 拒绝执行该测试脚本

### 与 PR 变更的关联

**PR 变更本身没有问题。** 该 PR 新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及相关元数据文件（README.md、image-info.yml、meta.yml），Docker 构建阶段**全程成功**：

- yum 依赖安装成功（make、gcc、zlib-devel 及 14 个传递依赖全部安装并验证通过）
- 源码下载和解压成功（从 GitHub 拉取 bwa v0.7.18）
- bwa 编译成功（仅包含 2 个无害的 `-Wunused-but-set-variable` 编译器警告，链接阶段无错误）
- 镜像构建和推送成功（镜像已推送到 `****test/bwa:0.7.18-oe2403sp4-x86_64`）

失败发生在 CI 流水线的 **[Check] 后置检查阶段**，而非 Dockerfile 构建阶段。`bwa_test.sh` 属于 `eulerpublisher` 测试框架包（独立于 `openeuler-docker-images` 仓库），其 CRLF 行尾问题是 CI 测试基础设施的缺陷。PR 仅因首次为 bwa 引入 24.03-lts-sp4 平台而触发了该检查，从而暴露了此预存的基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**修改 `eulerpublisher` 仓库中的 `bwa_test.sh`**：将文件的 CRLF 行尾转换为 LF 行尾（Unix 风格）。这是根本修复，确保测试脚本在 Linux CI 环境中可正常执行。可以使用 `dos2unix` 工具或编辑器设置将行尾从 `\r\n` 改为 `\n`。

### 方向 2（置信度: 低）
**在 `openeuler-docker-images` 仓库中不做任何修改，等待 eulerpublisher 维护者修复**。PR 的 Dockerfile 本身完全正确，构建和推送均已成功，仅后置检查脚本存在格式问题。如果 CI 流水线允许跳过 Check 阶段或该阶段不影响最终结果判定，可考虑手动合入。

## 需要进一步确认的点

1. **`bwa_test.sh` 是否在 `eulerpublisher` 仓库中最近被修改过？** —— 需要检查 `eulerpublisher` 仓库的 Git 历史，确认该文件的 CRLF 是何时引入的（可能是近期提交中由 Windows 环境编辑导致）。
2. **其他 bwa 平台版本（如 22.03-lts-sp3）的 Check 是否也失败？** —— 如果 `bwa_test.sh` 是通用脚本，那么已有 bwa 镜像（如 `0.7.18-oe2203sp3`）的 CI 也应该因同样的 CRLF 问题而失败。如果它们正常通过，则说明 CRLF 是最近才引入的，或测试脚本对 sp4 平台有特殊分支逻辑。
3. **`eulerpublisher` 的打包/发布流程中是否缺少行尾检查（如 `.gitattributes` 或 CI lint）？** —— 这是防止类似问题再次发生的长期措施。

## 修复验证要求

若修复方向涉及 **修改 `eulerpublisher` 仓库中的 `bwa_test.sh` 行尾格式**，code-fixer 必须：
- 在修改前后使用 `file` 命令或 `dos2unix --info` 验证文件的行尾格式已从 "CRLF" 转换为 "LF"
- 验证修改后的脚本在 Linux 环境中可以正常执行（`/bin/sh bwa_test.sh` 不报 "bad interpreter" 错误）
- 确认 `eulerpublisher` 仓库的 `.gitattributes` 配置正确，防止后续提交再次引入 CRLF 行尾
