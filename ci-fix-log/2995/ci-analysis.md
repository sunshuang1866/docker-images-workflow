# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, /bin/sh^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段，执行 `bwa_test.sh` 测试脚本时
- 失败原因: `eulerpublisher` 包自带的测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 含有 Windows 风格行尾（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh` 被解析为 `#!/bin/sh\r`。系统查找解释器 `/bin/sh\r`（注意末尾的 `^M` 即 `\r` 字符），该路径不存在，shell 报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
**与本次 PR 无关。** 具体证据：
1. **Docker 镜像构建完全成功**：日志显示所有 17 个依赖包安装正常，194 个 C 源文件编译通过（仅有 2 个 `-Wunused-but-set-variable` 无害警告），镜像构建并推送均完成（`[Build] finished`、`[Push] finished`）。
2. **失败发生在 CI 基础设施层面**：`bwa_test.sh` 位于 `/etc/eulerpublisher/tests/container/app/`，属于 CI 编排工具 `eulerpublisher` Python 包安装的文件，不来源于 PR 代码仓库。
3. **PR 仅新增了 Dockerfile 和更新了 3 个元数据文件**（README.md、image-info.yml、meta.yml），未涉及任何测试脚本。

## 修复方向

### 方向 1（置信度: 高）
修复 CI 基础设施中 `eulerpublisher` 包内的 `bwa_test.sh` 文件，将其行尾从 CRLF（Windows）转换为 LF（Unix）。可通过 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件后重新部署 eulerpublisher 包。

### 方向 2（置信度: 低）
若 CRLF 是在 git clone 或文件传输过程中引入的（而非源文件本身的问题），需检查 CI runner 上的 git 配置（`core.autocrlf`），确保 `eulerpublisher` 包的部署/更新流程不会引入行尾转换。

## 需要进一步确认的点
1. `bwa_test.sh` 在 eulerpublisher 包源仓库中是否原本就包含 CRLF 行尾，还是由 CI 运行时的文件传输/git checkout 引入。
2. 其他同类 HPC 镜像的测试脚本是否也存在相同问题（CRLF 行尾），如果是，需一并修复。
