# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾符
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段，`/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包自带的测试脚本）
- 失败原因: `bwa_test.sh` 测试脚本文件中存在 Windows 风格的行尾符（CRLF，即 `\r\n`），导致 shebang 行 `/bin/sh` 被 Shell 解析为 `/bin/sh^M`（`^M` 即回车符 `\r`），系统无法找到解释器，报 `bad interpreter: No such file or directory`

### 与 PR 变更的关联
**与 PR 代码变更无关**。日志清晰显示：
1. Docker 镜像构建全部成功（包括 `yum install`、源码编译 `make`、镜像导出和推送均完成，所有步骤返回 `DONE`）
2. `[Build] finished` 和 `[Push] finished` 日志均输出
3. 失败仅发生在 CI 的 [Check] 阶段——`eulerpublisher` 工具在调用 `bwa_test.sh` 测试已构建镜像时，因测试脚本自身包含 CRLF 行尾符而无法执行

PR 新增的 Dockerfile、README.md、image-info.yml、meta.yml 均不含 `bwa_test.sh`，且 Docker 构建过程完全成功，因此本次失败属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施的 `eulerpublisher` 包中 `tests/container/app/bwa_test.sh` 文件被以 CRLF 行尾符保存。需要修复该文件的换行符为 Unix 风格（LF），例如对该文件执行 `dos2unix` 或在提交至 eulerpublisher 仓库时用 `.gitattributes` 强制 LF。此修复不在本 PR 仓库范围内，需由 CI 基础设施维护者在 `eulerpublisher` 仓库中进行。

## 需要进一步确认的点
- 确认 `eulerpublisher` 包中 `bwa_test.sh` 的来源：是作为固定脚本随包安装，还是从 `openeuler-docker-images` 仓库动态生成。若为后者，需检查生成逻辑是否引入了 CRLF。
- 若该测试脚本是近期为 sp4 支持新增的，应确认上游 `eulerpublisher` 仓库中该文件的换行符是否已为 CRLF。

## 修复验证要求
无需在本 PR 仓库中验证。修复在 `eulerpublisher` 仓库完成并重新发布 RPM 包后，重新触发 CI 即可验证。
