# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符不兼容
- 新模式症状关键词: `bad interpreter`, `^M`, `No such file or directory`, `bwa_test.sh`

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI 工具链 `eulerpublisher` 内置的测试脚本 `bwa_test.sh`（路径: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`）
- 失败原因: CI 测试框架 `eulerpublisher` 中 bwa 的测试脚本 `bwa_test.sh` 包含 Windows 风格换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh\r` 中的 `\r`（`^M`）被 kernel 解释为解释器路径的一部分，系统无法找到 `/bin/sh\r` 作为合法解释器，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
**与 PR 代码变更无关**。该 PR 新增的 Dockerfile 构建完全成功：
- 依赖安装（yum install make gcc zlib-devel）→ 通过
- 源码下载（GitHub bwa v0.7.18）→ 通过
- 编译（make）→ 通过（仅有无关紧要的编译 Warning: `oldInverseSa0RelativeRank` / `bitsInWordMinusBitPerChar` unused，不影响成功）
- 镜像构建 + 推送（[Build] finished + [Push] finished）→ 通过

失败发生在镜像构建成功后的 CI 后置 [Check] 阶段，即 eulerpublisher 框架运行 `bwa_test.sh` 对已推送的镜像做验收测试时，因测试脚本自身换行符问题而失败。**PR 的 Dockerfile、meta.yml、README.md、image-info.yml 均无问题**。

## 修复方向

### 方向 1（置信度: 高）
CI 维护方需将 `eulerpublisher` 测试套件中的 `bwa_test.sh` 脚本换行符从 CRLF（`\r\n`）转换为 LF（`\n`）。可能的原因是该脚本在上游 eulerpublisher 仓库中被以 Windows 换行格式提交。可用 `dos2unix` 或 `sed -i 's/\r$//'` 修复该脚本后重新部署到 CI runner 上。

**注意**: 此问题与 PR 代码变更完全无关，属于 CI 基础设施配置问题。Code Fixer 无需修改任何 PR 文件。若 CI 测试脚本由 eulerpublisher 项目维护，应在其仓库中修复后发布新版本。

## 需要进一步确认的点
1. `eulerpublisher` 测试套件中 `bwa_test.sh` 的来源——是随 `eulerpublisher` 包发布的内置脚本还是 CI runner 上单独维护的脚本？
2. 该 `bwa_test.sh` 是否为本次 PR 才触发的全新脚本（之前没有 bwa 镜像的 openEuler 24.03-LTS-SP4 测试用例），换行符问题是否仅影响这一个文件？
3. 确认 CI 下游其他架构（aarch64）的构建 job 是否也因同样原因失败——当前日志仅覆盖 x86_64 的构建和测试。
