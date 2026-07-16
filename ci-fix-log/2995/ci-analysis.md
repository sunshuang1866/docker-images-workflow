# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段，eulerpublisher 工具尝试运行 `bwa_test.sh` 测试脚本时
- 失败原因: `eulerpublisher` Python 包内自带的测试脚本 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh` 使用 Windows 风格的 CRLF 换行符（`\r\n`），导致 Linux 内核无法识别 shebang `#!/bin/sh`（实际被解析为 `#!/bin/sh\r`），报 "bad interpreter: No such file or directory"

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建和推送均已成功完成：
- 日志中 `#7 DONE 199.0s` 表明 Docker 构建步骤完全通过（yum 安装依赖 → 下载源码 → make 编译 → yum 清理均正常）
- 日志中 `#8 DONE 8.4s` 表明镜像推送成功
- `[Build] finished` 和 `[Push] finished` 确认构建与推送阶段均无错误

失败仅发生在 CI 基础架构的 [Check] 阶段——`eulerpublisher` 工具内置的 `bwa_test.sh` 测试脚本因文件格式（CRLF 换行符）问题无法被 Shell 解释器执行。该脚本位于 CI runner 的系统路径（`/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`），属于 CI 基础设施组件，不在本次 PR 提交的 4 个文件中。

PR 提交的 Dockerfile 语法和逻辑正确，bwa v0.7.18 在 openEuler 24.03-lts-sp4 上编译成功。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需将 `eulerpublisher` 包中的 `bwa_test.sh` 脚本从 CRLF 转换为 LF 换行符。可使用 `dos2unix` 或 `sed -i 's/\r$//'` 修复该脚本后重新发布 `eulerpublisher` 包，或在 CI runner 上就地修复该文件。

### 方向 2（置信度: 低）
若 `bwa_test.sh` 是最近新增的脚本且仓库中尚未有对应的测试用例，也可能是 `eulerpublisher` 期望在 PR 中附带一个 `bwa_test.sh` 但本次 PR 未提交。但从脚本路径（`/usr/etc/eulerpublisher/tests/container/app/`）来看，这是 eulerpublisher 包自身提供的通用测试脚本，概率极低。

## 需要进一步确认的点
1. `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh` 的内容——确认 CRLF 换行符是唯一问题，排除脚本内容本身的语法错误
2. 确认 `eulerpublisher` 包的版本和发布流程，以便修复后重新部署到 CI runner
3. 确认此脚本是随 `eulerpublisher` 包安装的还是通过其他方式部署到 CI runner 的
