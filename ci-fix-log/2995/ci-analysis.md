# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符错误
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, test.sh, CRLF

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 测试基础设施脚本）
- 失败原因: `eulerpublisher` Python 包中安装的 BWA 测试脚本 `bwa_test.sh` 包含 Windows 风格的 CRLF 换行符（`\r\n`），导致 shebang `#!/bin/sh` 被系统解释为 `#!/bin/sh\r`，Linux 内核无法找到 `/bin/sh\r` 这个解释器文件，抛出 `bad interpreter` 错误。

日志证据：Docker 镜像构建和推送均成功完成（`#7 DONE 199.0s`、`#8 DONE 8.4s`、`[Build] finished`、`[Push] finished`），失败仅发生在后续的 `[Check]` 阶段，且错误信息中的 `^M` 是 CRLF 换行符的典型表现。

### 与 PR 变更的关联
**无关**。本次 PR 仅新增了一个 BWA 开源软件的 Dockerfile 及配套元数据文件。Dockerfile 所描述的构建过程完全成功（编译、安装、清理均无报错，镜像已成功推送至仓库）。失败发生在 CI 基础设施的测试脚本 (`bwa_test.sh`) 中——该脚本由 `eulerpublisher` 包预装，负责对构建完成的镜像进行验收测试，其 CRLF 换行符问题与 PR 代码变更无任何关联。

## 修复方向

### 方向 1（置信度: 高）
修复 CI 基础设施中 `eulerpublisher` 包的 `bwa_test.sh` 测试脚本的换行符。具体方式：在 CI pipeline 初始化阶段或 `eulerpublisher` 包安装后，对该脚本执行 `dos2unix` 或 `sed -i 's/\r$//'` 转换，将 CRLF 换行符转为 Unix LF 格式。这不是对本仓库代码的修改，而是 CI 基础设施侧的修复。

### 方向 2（置信度: 低，若方向 1 不可行）
检查 `eulerpublisher` 包的 Git 仓库，确认 `bwa_test.sh` 是否因 Unix/Windows 混用 `git clone` 配置（如 `core.autocrlf=true` 在 Windows 上）导致文件被检出时自动转换了换行符。若为源仓库问题，应向 `eulerpublisher` 维护团队提交修复。

## 需要进一步确认的点
1. `bwa_test.sh` 是 `eulerpublisher` pip 包的内置文件还是从某个 Git 仓库动态拉取的？若是动态拉取，需确认该仓库的文件是否本身即包含 CRLF 换行符。
2. 同一 CI runner 上其他镜像的 `*_test.sh` 检查是否也受此问题影响？若仅 `bwa_test.sh` 有问题，说明是脚本文件本身被污染；若所有测试脚本均失败，则可能是 CI runner 的 `git` 全局配置问题。

## 修复验证要求
由于根因在 CI 基础设施侧而非本仓库代码，Code Fixer 自身无法直接实施修复。本报告供 CI 维护团队参考。若由 Code Fixer 处理，需确认 CI 维护团队已在 `eulerpublisher` 侧修复后重新触发构建验证。
