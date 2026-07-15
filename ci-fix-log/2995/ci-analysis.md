# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符错误
- 新模式症状关键词: `^M`, `bad interpreter`, `_test.sh`, `bwa`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher CI 工具包自带的测试脚本）
- 失败原因: `bwa_test.sh` 文件存在 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh\r` 包含回车符 `\r`（显示为 `^M`），内核无法找到 `/bin/sh\r` 作为解释器，脚本执行失败。

### 与 PR 变更的关联
- **与 PR 变更无关**。PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 以及配套的 README、image-info.yml、meta.yml 文件。
- **Docker 镜像构建成功**：日志中 `#7 DONE 199.0s` 表明 Dockerfile 中所有步骤（yum 安装依赖、curl 下载源码、make 编译、镜像导出推送）均全部通过，镜像已成功推送到 `docker.io/****test/bwa:0.7.18-oe2403sp4-x86_64`。
- **失败发生在 CI 基础设施层**：`[Build] finished` 和 `[Push] finished` 之后，CI 进入 `[Check]` 阶段，调用 eulerpublisher 工具包内的 `bwa_test.sh` 对镜像做功能验证，但因该脚本文件换行符问题导致解释器无法识别而失败。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题，**Code Fixer 无需处理本仓库代码**。需由 CI 平台维护方修复 eulerpublisher 包中的 `bwa_test.sh` 文件，将其换行符从 CRLF 转换为 LF（使用 `dos2unix` 或 `sed -i 's/\r$//'`），确保 shebang 行不含回车符。

## 需要进一步确认的点
1. 确认 `bwa_test.sh` 在当前 CI 节点上实际换行符格式（`file /etc/eulerpublisher/tests/container/app/bwa_test.sh` 或 `xxd` 查看前 10 字节）。
2. 确认 eulerpublisher 包是从哪个源安装的（Git 仓库 clone 还是 pip 安装），该源中 `bwa_test.sh` 是否以 CRLF 提交。
3. 排查同一 eulerpublisher 包中其他 `*_test.sh` 脚本是否也存在相同的 CRLF 问题，以避免后续其他镜像的 [Check] 阶段同样失败。
