# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: ^M, bad interpreter, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施文件，非 PR 提交内容）
- 失败原因: CI 测试基础设施中的 `bwa_test.sh` 脚本使用了 Windows 风格的换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh\r` 中的 `\r`（在日志中显示为 `^M`）被视为解释器路径的一部分，内核尝试查找 `/bin/sh\r` 而失败。Docker 镜像的构建（Build）和推送（Push）阶段均成功完成，失败仅发生在 CI 的 [Check] 测试阶段。

### 与 PR 变更的关联
**无关联。** 本次 PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 并更新了相关元数据文件（README.md、image-info.yml、meta.yml）。日志中 Docker 镜像构建的所有步骤（`#1` 到 `#7`）均成功完成，镜像已成功构建并推送（`[Build] finished`，`[Push] finished`）。失败发生在 CI 编排工具 `eulerpublisher` 的内置测试验证阶段，`bwa_test.sh` 是 `eulerpublisher` Python 包的一部分（安装路径 `/etc/eulerpublisher/tests/container/app/`），不在本仓库的 PR 变更范围内。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施团队需要修复 `eulerpublisher` 包中的 `tests/container/app/bwa_test.sh` 脚本行尾格式，将其从 CRLF 转换为 LF。该脚本在安装部署到 `/etc/eulerpublisher/tests/container/app/` 时引入了 Windows 风格换行符，导致 Linux 内核无法正确识别 shebang 解释器。修复后需重新发布 `eulerpublisher` 包（或更新 CI runner 上的安装副本）。**此问题与 PR 代码无关，Code Fixer 无需对 PR 做任何修改。**

## 需要进一步确认的点
- `bwa_test.sh` 是否是本次 PR 对应的镜像版本新增的测试脚本（即 `eulerpublisher` 是否为支持 openEuler 24.03-LTS-SP4 的 BWA 才新增了该测试文件，且提交该脚本时使用了 CRLF 行尾）。若是，则需要追溯到 `eulerpublisher` 仓库中该脚本的提交，修正其行尾格式。
- 若 `bwa_test.sh` 是已存在的脚本，则需排查 CI runner 环境是否因某些操作（如从 Windows 环境同步文件、Git 配置 `core.autocrlf` 不当）意外引入了 CRLF 转换。
