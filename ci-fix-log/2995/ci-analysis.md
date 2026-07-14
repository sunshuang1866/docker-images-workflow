# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: `^M`, `bad interpreter`, `No such file or directory`, `test.sh`

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh:1`（shebang 行 `#!/bin/sh`）
- 失败原因: eulerpublisher 测试包中的 `bwa_test.sh` 脚本使用了 **Windows 风格换行符（CRLF）**，shebang 行 `#!/bin/sh` 末尾携带回车符 `\r`（日志中显示为 `^M`），被系统解析为 `#!/bin/sh\r`。内核尝试执行解释器 `/bin/sh\r`（含回车符的路径），该文件不存在，报 "bad interpreter: No such file or directory"。**Docker 镜像构建和推送均已成功**（`[Build] finished` → `[Push] finished`），失败仅发生在 CI 的 `[Check]` 阶段调用预置测试脚本时。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增 4 个文件的变更：
1. `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新增，Docker 镜像构建成功）
2. `HPC/bwa/README.md`（文档更新）
3. `HPC/bwa/doc/image-info.yml`（镜像信息更新）
4. `HPC/bwa/meta.yml`（元数据更新）

Docker 镜像在 #7 步骤中完整构建成功（199.0 秒），编译过程仅有 GCC 的两个 `-Wunused-but-set-variable` 警告，无任何编译错误。镜像导出和推送均成功（#8 DONE 8.4s）。失败发生在 CI 的 `[Check]` 阶段——调用 eulerpublisher 包中预置的 `bwa_test.sh` 脚本对构建好的镜像进行验证时，因脚本自身 CRLF 换行问题导致 shell 无法解析 shebang 行。eulerpublisher 包及其测试脚本均不在此 PR 变更范围内。

## 修复方向

### 方向 1（置信度: 高）
**修复 eulerpublisher 包中 `bwa_test.sh` 的换行符。** 该文件位于 eulerpublisher 项目的 `tests/container/app/bwa_test.sh`，当前使用 CRLF（Windows）换行，需转换为 LF（Unix）换行。这不是本仓库（openeuler-docker-images）的代码修复范围，属于 eulerpublisher 项目的基础设施问题，应由 eulerpublisher 维护者处理。本仓库的 PR 自身无需任何修改，Docker 镜像构建完全正确。

## 需要进一步确认的点
1. 确认 eulerpublisher 仓库中 `tests/container/app/bwa_test.sh` 是否确实存在 CRLF 换行（可能是 Git 提交时 `core.autocrlf` 配置不当或 `.gitattributes` 缺失所致）。
2. 确认 eulerpublisher 测试包中是否只有 `bwa_test.sh` 受影响，还是其他测试脚本也有相同的 CRLF 问题。
3. 检查 eulerpublisher 的发布/打包流程（该测试脚本通过 `eulerpublisher` Python 包安装到 `/etc/eulerpublisher/tests/`），确认 CRLF 是在哪个环节引入的。
