# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: `^M`, `bad interpreter`, `No such file or directory`, `bwa_test.sh`

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 基础设施中的 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包内置的测试脚本）
- 失败原因: `bwa_test.sh` 测试脚本使用了 Windows 风格的 CRLF 行尾（`\r\n`），导致 shebang 行被解析为 `#!/bin/sh\r`，系统无法找到名为 `/bin/sh\r` 的解释器。Docker 镜像自身的构建（build + push）已完全成功，失败仅发生在 CI 的 [Check] 测试阶段。

### 与 PR 变更的关联

**与 PR 无关。** PR 仅新增了 4 个文件（Dockerfile、README.md 条目、image-info.yml、meta.yml），未修改任何 CI 测试脚本。Docker 构建过程（#1-#8，包括 `yum install`、源码编译、`make`、镜像导出和推送）全部成功完成。失败根因是 CI 基础设施中 `eulerpublisher` 包的 `bwa_test.sh` 文件携带了 CRLF 行尾（`^M`），这是镜像发布后 [Check] 阶段调用该脚本时触发的预存问题。

## 修复方向

### 方向 1（置信度: 高）
CI 运维人员需要将 `eulerpublisher` 包中的 `bwa_test.sh` 文件的行尾从 CRLF 转换为 LF。可在 CI runner 环境上执行 `dos2unix` 或 `sed -i 's/\r$//'` 修复该脚本，或联系 eulerpublisher 包的维护者在发布时确保脚本文件使用 Unix 行尾。

### 方向 2（置信度: 中）
若 `bwa_test.sh` 是从上游仓库通过 `git clone` 获取的（而非从 PyPI 包安装），则需要在 CI 的 git clone 步骤中配置 `.gitattributes` 或检查 `git config core.autocrlf` 设置，确保脚本文件以 LF 行尾 checkout。

## 需要进一步确认的点
- `bwa_test.sh` 是 `eulerpublisher` PyPI 包的内置文件，还是 CI 运行时从某个 Git 仓库动态 clone 获取的？这决定了修复应在包发布侧还是在 CI 流水线侧。
- 其他镜像（非 bwa）的 [Check] 测试是否也受同一 `eulerpublisher` 包中其他 CRLF 测试脚本的影响。
