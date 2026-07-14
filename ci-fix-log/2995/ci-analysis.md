# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, /bin/sh^M, No such file or directory, CRLF

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段，执行 `bwa_test.sh` 测试脚本时
- 失败原因: eulerpublisher 包中安装的测试脚本 `bwa_test.sh` 包含 Windows 风格行尾（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh\r` 中的回车符 `\r`（显示为 `^M`）被系统当作解释器名的一部分，系统查找名为 `/bin/sh\r` 的解释器失败，报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile（`HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`）构建成功——日志中 Docker 构建阶段（步骤 #1 至 #8）全部通过，镜像已成功编译（bwa v0.7.18 编译仅产生两个编译警告，均非致命）并推送到 registry。失败发生在构建之后的镜像检查 [Check] 阶段，该阶段调用 eulerpublisher 包中预装于 CI runner 上的测试脚本 `bwa_test.sh`，该脚本自身的 CRLF 行尾问题与本次 PR 的代码改动无关。

## 修复方向

### 方向 1（置信度: 高）
eulerpublisher 包中的 `bwa_test.sh`（路径 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`）被以 Windows 行尾（CRLF）写入或安装到 CI runner。需由 CI 基础设施维护者做以下任一项：
- 在 eulerpublisher 源码仓库中将 `bwa_test.sh` 的行尾转换为 LF 后重新发布包
- 或在 CI 构建脚本中，在调用测试前对测试脚本执行 `dos2unix` 或 `sed -i 's/\r$//'` 去除回车符

**注意：Code Fixer 无需也无法处理此问题**——出问题的是 CI runner 上预安装的 eulerpublisher 包内的测试脚本，不在本次 PR 的仓库范围内。

## 需要进一步确认的点
- eulerpublisher 包中 `bwa_test.sh` 的源码是否确实以 CRLF 提交，还是由于 CI runner 上的 git 配置（如 `core.autocrlf=true`）在克隆/安装过程中引入了 CRLF
- 同一 CI runner 上其他镜像（如已有的 `bwa:0.7.18-oe2203sp3`）的检查是否也因同样的 CRLF 问题失败，还是仅 `bwa_test.sh` 这一个脚本受影响
