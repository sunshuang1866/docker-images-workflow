# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Shell脚本CRLF换行
- 新模式症状关键词: ^M, bad interpreter, No such file or directory, /bin/sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 基础设施 — `eulerpublisher` 包中的测试脚本 `bwa_test.sh`（路径 `.../etc/eulerpublisher/tests/container/app/bwa_test.sh`）
- 失败原因: `bwa_test.sh` 文件包含 Windows 风格换行符（CRLF），shebang 行 `#!/bin/sh` 末尾附带了不可见的回车符 `\r`（在日志中显示为 `^M`），导致 Unix 内核无法识别 `/bin/sh\r` 这个解释器路径，抛出 "bad interpreter: No such file or directory" 错误

### Docker 构建状态
Docker 镜像构建和推送**均已成功**完成，日志中明确显示：
- `[Build] finished` — x86_64 架构镜像构建成功
- `[Push] finished` — x86_64 架构镜像推送成功
- 所有 17 个 RPM 包安装正常、BWA v0.7.18 源码编译正常、镜像导出和推送均无错误

失败仅发生在 [Check] 阶段，即 CI 尝试运行测试脚本 `bwa_test.sh` 验证已构建镜像时。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 修改的文件为：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新增 — 语法正确，构建成功）
- `HPC/bwa/README.md`（文档更新）
- `HPC/bwa/doc/image-info.yml`（文档更新）
- `HPC/bwa/meta.yml`（元数据更新）

这些文件中没有任何一个引入或涉及 `bwa_test.sh`。该测试脚本位于 CI 编排工具 `eulerpublisher` 的安装目录内，属于 CI 基础设施层面问题。

## 修复方向

### 方向 1（置信度: 高）
修复 `eulerpublisher` 包中 `bwa_test.sh` 文件的换行符格式，将 CRLF（`\r\n`）转换为 LF（`\n`）。该脚本在部署到 CI runner 时携带了 Windows 换行符，导致 Unix 内核无法解析 shebang 行。

**注意**: 此修复应在 `eulerpublisher` 仓库中进行，而非本 PR。本 PR 的代码变更无需修改。

## 需要进一步确认的点
1. `bwa_test.sh` 是 eulerpublisher 包中预置的测试脚本，还是由 CI 流水线从仓库中动态提取/生成的？如果是后者，需要检查生成机制或提取逻辑为何引入了 CRLF。
2. 其他已通过 CI 的 bwa 镜像（如 `0.7.18-oe2203sp3`）是否使用了同一个 `bwa_test.sh`？如果是，为什么之前的 bwa 版本未触发此问题——是否该脚本在近期被更新并引入了 CRLF？
3. aarch64 架构的下游构建 job 是否也失败了？日志仅显示了 x86_64 的构建结果，aarch64 的构建/检查日志未提供。如果 aarch64 也失败且错误不同，需要获取对应日志。
