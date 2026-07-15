# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符
- 新模式症状关键词: bad interpreter, ^M, /bin/sh, No such file or directory, CRLF, carriage return

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段，`eulerpublisher` 测试脚本 `bwa_test.sh`
- 失败原因: CI 测试基础设施中 `eulerpublisher/tests/container/app/bwa_test.sh` 脚本文件使用了 Windows 风格的 CRLF 换行符，导致 shebang 行 `#!/bin/sh` 末尾被附加了不可见的回车符（`\r` / `^M`），内核尝试定位 `/bin/sh\r` 作为解释器，该路径不存在，报 `bad interpreter: No such file or directory`。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 新增的 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 构建阶段完全成功（Docker 镜像构建、推送均已完成，日志中可见 `[Build] finished` 和 `[Push] finished`）。失败发生在 CI 框架 `eulerpublisher` 内置的镜像验证测试脚本中，该脚本的 CRLF 行尾问题是 CI 基础设施层面的缺陷，并非 PR 代码变更所致。

## 修复方向

### 方向 1（置信度: 中）
`eulerpublisher` 仓库中的 `tests/container/app/bwa_test.sh`（以及可能其他测试脚本）被以 CRLF 行尾格式提交。需要在 `eulerpublisher` 仓库中将该文件的行尾从 CRLF 转换为 LF（Unix 格式），并确保 `.gitattributes` 配置了 `*.sh text eol=lf` 以防止未来再次出现。此修复不在当前 PR 的 openEuler docker images 仓库范围内，需提交至 `eulerpublisher` 工具仓库。

### 方向 2（置信度: 低）
CI runner 环境的 `git clone` 操作中 `core.autocrlf` 配置异常，导致克隆 `eulerpublisher` 时将原本为 LF 的脚本错误转换为 CRLF。需检查 CI runner 的 git 全局配置。

## 需要进一步确认的点
1. `eulerpublisher` 仓库中 `tests/container/app/bwa_test.sh` 文件的当前行尾格式（LF 还是 CRLF），以确认是源文件问题还是克隆时转换所致。
2. bwa 已有的 `22.03-lts-sp3` 版本 CI 构建是否也因同一脚本失败——若 22.03 版本能通过测试，则 CRLF 可能是近期引入 `eulerpublisher` 的。
3. CI runner（`ecs-build-docker-x86-hk`）上的 `git config core.autocrlf` 值。
