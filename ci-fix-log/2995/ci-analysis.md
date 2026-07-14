# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符错误
- 新模式症状关键词: ^M, bad interpreter, No such file or directory, CRLF, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 框架 eulerpublisher 包内的测试脚本 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（shebang 行）
- 失败原因: `bwa_test.sh` 文件使用了 Windows 风格换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh` 被内核解析为 `#!/bin/sh\r`（日志中显示为 `/bin/sh^M`），系统找不到名为 `/bin/sh^M` 的解释器，报 "bad interpreter: No such file or directory"

### 与 PR 变更的关联
**PR 变更本身没有问题**：
- Docker 镜像构建成功（`#7 DONE 199.0s`），gcc/make 编译 bwa 0.7.18 全程无错误，仅有 2 个无害的 `-Wunused-but-set-variable` 编译警告
- 镜像推送成功（`[Push] finished`）
- 失败发生在 CI 框架的 `[Check]` 阶段，该阶段调用 eulerpublisher 包内的 `bwa_test.sh` 测试脚本。该脚本不属于本次 PR 的变更文件（PR 仅修改 `HPC/bwa/` 下的 Dockerfile、README.md、image-info.yml、meta.yml），属于 CI 基础设施文件，其换行符问题与 PR 代码无关

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施的 `bwa_test.sh` 文件被以 CRLF（Windows 换行符）格式写入了 Git 仓库或 eulerpublisher 发布包。需要将 `bwa_test.sh` 文件的换行符从 CRLF 转换为 LF（Unix 格式）。如果该文件在 eulerpublisher 源码仓库中，则需确保 git 配置或 `.gitattributes` 正确设置 `*.sh` 文件的换行符处理规则；如果该文件由其他工具动态生成，则需检查生成工具的换行符配置。

## 需要进一步确认的点
1. `bwa_test.sh` 的来源——是被 eulerpublisher 发布包携带的静态文件，还是由某个上游仓库在 CI 运行时动态生成/克隆获得？
2. eulerpublisher 仓库的 `.gitattributes` 或 CI runner 的 git 全局配置是否设置了 `core.autocrlf`，导致 `.sh` 文件被自动转换为 CRLF？

## 修复验证要求
若修复涉及修改 eulerpublisher 仓库中的文件换行符，code-fixer 需验证修改后 `bwa_test.sh` 的 shebang 行不再携带 `\r`（可用 `file bwa_test.sh` 或 `xxd bwa_test.sh | head` 确认换行符为 LF）。
