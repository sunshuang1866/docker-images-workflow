# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试脚本 CRLF 行尾
- 新模式症状关键词: `^M`, `bad interpreter`, `No such file or directory`, `/bin/sh^M`, CRLF, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454-INFO: [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（即 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`）
- 失败原因: `eulerpublisher` 包中自带的 `bwa_test.sh` 测试脚本包含 Windows 风格行尾（CRLF，即 `\r\n`），shebang `#!/bin/sh` 末尾携带回车符 `\r`（显示为 `^M`），导致 Linux 内核将解释器路径解析为 `/bin/sh\r`，该路径不存在，shell 报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
**与 PR 代码变更无关。**PR #2995 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及配套元数据文件。CI 日志显示 Docker 镜像构建（`#7 DONE 199.0s`）和推送（`[Push] finished`）均成功完成。失败发生在构建后的 `[Check]` 测试阶段，根因是 CI 基础设施 `eulerpublisher` 包自带测试脚本 `bwa_test.sh` 存在 CRLF 行尾问题，属于 CI 工具缺陷，与本次 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 中）
CI 管理员需修复 `eulerpublisher` 包中 `bwa_test.sh` 文件的换行符：将 CRLF (`\r\n`) 转换为 LF (`\n`)。可通过 `dos2unix` 或 `sed -i 's/\r$//'` 命令处理，并重新打包/部署 eulerpublisher。注意：此问题可能在所有包含 `bwa_test.sh` 的 bwa 镜像 CI 检查中复现，影响面不限于本 PR。

## 需要进一步确认的点
1. 确认 `eulerpublisher` 包的源码仓库中 `bwa_test.sh` 是否确实包含 CRLF 行尾，还是仅在部署到 CI runner 的副本中被污染。
2. 检查 `eulerpublisher` 包中其他 `*_test.sh` 脚本是否也存在同样的 CRLF 问题，避免逐个暴露。
3. 确认 bwa 镜像在 22.03-lts-sp3 等其他 OS 版本的 CI 检查是否也出现过同样错误（日志中未体现），以判断是否为本次 24.03-lts-sp4 部署新引入的 runner 环境特有。
