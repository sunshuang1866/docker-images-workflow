# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: /bin/sh^M, bad interpreter, bwa_test.sh, CRLF

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher CI 工具内置测试脚本）
- 失败原因: 该测试脚本的 shebang 行末尾含有 Windows 风格回车符 `\r`（CR），导致系统将 `#!/bin/sh\r` 解释为解释器路径，查找 `/bin/sh^M` 失败。实际 Docker 镜像构建、编译 BWA 源码、推送镜像三个阶段均**完全成功**。

### 与 PR 变更的关联
**与 PR 变更无关。** PR #2995 新增的 Dockerfile 构建完全成功——编译安装（`yum install`、`make`）、镜像导出、推送均无错误。失败发生在 `eulerpublisher` 框架自带的 `bwa_test.sh` 测试脚本，该脚本不属于本 PR 的变更范围。

日志证据：
- Docker 构建 199 秒内无任何错误退出，成功生成并推送 manifest: `sha256:55a4a19ab905b82beb79afdffaaafa3f0663c82753f8966dc4837eafa0d67b2d`
- `[Build] finished` / `[Push] finished` 均为 INFO 级别，无异常
- 唯一 CRITICAL 日志来自 `bwa_test.sh` 脚本的 shebang 解析

## 修复方向

### 方向 1（置信度: 高）
`bwa_test.sh` 文件在 eulerpublisher 仓库或 CI 克隆过程中引入了 CRLF 换行符。应由 CI 平台管理员检查 eulerpublisher 仓库中 `bwa_test.sh` 的行尾格式，确保文件使用 Unix LF 换行。若文件本身是 LF 但 git 的 `core.autocrlf` 在 checkout 时转换了换行，需调整 CI 节点的 git 配置。

### 方向 2（置信度: 低）
不涉及本 PR 修复。PR 的 Dockerfile 及元数据变更均正确，无需修改。

## 需要进一步确认的点
1. eulerpublisher 仓库中 `tests/container/app/bwa_test.sh` 文件的实际行尾格式（LF 还是 CRLF）
2. CI 构建节点的 `git config core.autocrlf` 设置
3. 该测试脚本是否为本次 eulerpublisher 版本新增/更新所致（需比对 eulerpublisher 仓库历史）
