# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, /bin/sh^M, No such file or directory

## 根因分析

### 直接错误
```
[Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher CI 工具内置的 bwa 镜像验证脚本）
- 失败原因: 测试脚本 `bwa_test.sh` 使用 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh` 末尾携带不可见的 `\r`（carriage return），操作系统将解释器路径解析为 `/bin/sh\r`，该路径不存在，脚本启动失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了以下文件/修改：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新增，19 行）
- `HPC/bwa/README.md`（新增一行版本标注）
- `HPC/bwa/doc/image-info.yml`（新增一行 tag 条目）
- `HPC/bwa/meta.yml`（添加新版本的 path 条目）

Docker 镜像构建（`#7 DONE 199.0s`，`[Build] finished`）和推送（`[Push] finished`）均已成功完成。失败仅发生在 CI 管道后处理阶段 `[Check]`，该阶段**未使用 PR 中的任何代码**，而是调用 eulerpublisher 包内置的测试脚本。该脚本的 CRLF 行尾问题是 eulerpublisher CI 工具自身的问题，与 PR 修改无关。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施维护者需要修复 eulerpublisher 包内的 `bwa_test.sh` 文件，将其行尾格式从 CRLF 转换为 LF（Unix 风格）。可通过 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件后重新打包/部署 eulerpublisher。**此修复不在 PR #2995 范围内，无需修改 Dockerfile 或任何 PR 中的文件。**

## 需要进一步确认的点
1. `bwa_test.sh` 文件在 eulerpublisher 代码仓库中的具体位置及该文件最近一次提交者——确认是何时引入的 CRLF 行尾问题。
2. 同仓库中是否还有其他 `.sh` 测试脚本也存在同样的 CRLF 行尾问题——如果是批量引入的，可能需要统一修复。
3. 确认 eulerpublisher 的版本号——本次 CI 运行使用的是哪个版本的 eulerpublisher，是否有更新的版本已修复此问题。
4. 日志仅显示 x86_64 架构的构建信息，若 aarch64 架构的构建也存在同样问题，需一并修复。
