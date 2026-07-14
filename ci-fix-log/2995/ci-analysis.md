# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符异常
- 新模式症状关键词: bad interpreter, ^M, /bin/sh^M, No such file or directory, test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:161]-INFO: [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 安装包中的测试脚本）
- 失败原因: CI 的 eulerpublisher 包中内置的 `bwa_test.sh` 测试脚本使用了 Windows 风格 CRLF 换行符（`\r\n`），导致 shebang 行 `#!/bin/sh` 被解析为 `#!/bin/sh\r`，系统无法找到 `/bin/sh\r` 这个解释器，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联

**本次 PR 变更与失败无关。** PR 仅新增了 bwa 0.7.18 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像构建阶段（包括 yum 依赖安装、bwa 源码编译、镜像推送）全部成功完成（`#7 DONE 199.0s`，镜像构建并推送成功）。

失败发生在 CI 流水线的 CHECK 验证阶段，由 eulerpublisher 框架调用预置测试脚本 `bwa_test.sh` 来验证构建出的镜像。该测试脚本是 CI 基础设施的一部分（随 eulerpublisher 包安装于 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`），其 CRLF 换行符问题是 CI 环境的既有缺陷，与本次 PR 的代码变更无任何关联。

## 修复方向

### 方向 1（置信度: 高）
CI 运维/基础设施团队需将 eulerpublisher 包中 `bwa_test.sh` 文件的换行符从 CRLF（`\r\n`）转换为 LF（`\n`）。这是 CI runner 上的文件格式问题，不属于 Dockerfile 或 PR 代码层面可修复的范围。Code Fixer 无需处理。

## 需要进一步确认的点

1. 确认 `bwa_test.sh` 是否也在其他 bwa 版本的 CHECK 阶段被调用——如果是同一脚本，则说明该脚本在近期被 eulerpublisher 包更新时引入了 CRLF 换行符问题，影响面可能不止 PR #2995。
2. 确认 eulerpublisher 包的版本和升级记录，判断 `bwa_test.sh` 是何时被加入/修改的。
3. 确认其他已存在的 bwa 镜像（如 `0.7.18-oe2203sp3`）在 CI 重新构建时是否也会触发同样的 CHECK 失败。
