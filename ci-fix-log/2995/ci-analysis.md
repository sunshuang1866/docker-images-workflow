# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: `/bin/sh^M`, `bad interpreter`, `No such file or directory`, `bwa_test.sh`

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI `[Check]` 阶段，`eulerpublisher` 工具调用 `bwa_test.sh` 测试脚本时
- 失败原因: CI 工具 `eulerpublisher` 中的测试脚本 `bwa_test.sh` 包含 Windows 风格换行符（CRLF，`\r\n`），导致 shebang 行 `#!/bin/sh` 被系统解析为 `#!/bin/sh\r`，内核无法找到该解释器路径，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**与 PR 变更无关。** 

- Docker 镜像构建和推送阶段完全成功（`#7 DONE 199.0s`、`#8 DONE 8.4s`，`[Build] finished`、`[Push] finished` 均正常输出）。
- 失败仅在 `[Check]` 阶段发生，失败的脚本 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh` 位于 CI 工具 `eulerpublisher` 的安装目录中，**不属于本次 PR 提交的任何文件**。
- PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及修改了 README、image-info.yml、meta.yml 等元数据文件，未涉及任何测试脚本。

## 修复方向

### 方向 1（置信度: 高）
CI 运维团队检查 `eulerpublisher` 工具包中的 `bwa_test.sh` 文件，将其换行符从 CRLF (`\r\n`) 转换为 LF (`\n`)。可使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件后重新部署 `eulerpublisher` 包。

> 此问题对 Code Fixer Agent 不适用——属于 CI 基础设施问题，无需修改 PR 代码。Code Fixer 无需处理。

## 需要进一步确认的点
1. `bwa_test.sh` 是在 eulerpublisher 包的哪个版本引入 CRLF 换行符的？此前的 bwa 镜像 CI 检查（如 22.03-lts-sp3）是否使用了同一版本的 eulerpublisher？
2. 是否仅在当前 CI runner（`ecs-build-docker-x86-hk`）上出现了此问题，还是所有 runner 均受影响？
3. eulerpublisher 仓库中该脚本的原始换行格式是什么？是否在 Git 传输/部署过程中被转换？
