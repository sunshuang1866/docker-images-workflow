# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施文件，非 PR 代码）
- 失败原因: CI 基础设施的 `bwa_test.sh` 测试脚本包含 Windows 风格行尾（CRLF），shebang 行 `#!/bin/sh\r` 中的 `\r`（显示为 `^M`）导致内核无法找到合法解释器 `/bin/sh\r`，测试脚本无法启动

### 与 PR 变更的关联
**与 PR 变更无关。** 日志明确显示：
1. Docker 镜像构建成功（`#7 DONE 199.0s`，全部编译通过，无任何错误）
2. 镜像推送成功（`[Push] finished`）
3. 失败发生在 CI 的 `[Check]` 后处理阶段，错误指向 `eulerpublisher` 包内置的测试脚本 `bwa_test.sh` 存在 CRLF 行尾问题

PR 新增的 Dockerfile（`HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`）构建过程完全正常，bwa 0.7.18 源码编译成功，二进制产出正常，yum 安装和卸载均无异常。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 CI 基础设施问题，需要 CI 维护者修复 `eulerpublisher` 包中 `bwa_test.sh` 的 CRLF 行尾。可通过以下方式之一修复：
- 在 CI runner 上对 `bwa_test.sh` 执行 `dos2unix` 或 `sed -i 's/\r$//'` 
- 修复 `eulerpublisher` 包发布流程，确保测试脚本以 LF 行尾打包

## 需要进一步确认的点
1. 确认 `eulerpublisher` 包中 `bwa_test.sh` 的源文件是否确实包含 CRLF 行尾（可登录 CI runner 检查）
2. 确认其他已通过 CI 的 bwa 镜像（如 22.03-lts-sp3）在相同 CI 环境中是否也能复现此问题——若也能复现，则说明这是 CI runner 环境近期发生变化导致的回归，而非本次 PR 引入
3. 如果该 CI runner 此前成功运行过其他 bwa 测试，排查 runner 软件环境（`eulerpublisher` 包版本）是否被升级

## 修复验证要求
无需针对此 PR 进行额外验证。CI 基础设施修复后，重新触发此 PR 的 CI 流水线即可验证通过。
