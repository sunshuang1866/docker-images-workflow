# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Windows换行符污染测试脚本
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, /bin/sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段，测试脚本 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`
- 失败原因: CI 测试脚本 `bwa_test.sh` 文件包含 Windows 换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh` 被解释为 `#!/bin/sh\r`（末尾带 `^M` 回车符），Linux 内核无法找到名为 `/bin/sh\r` 的解释器，报 "bad interpreter: No such file or directory"。**Docker 构建和推送均已完成且成功**（`[Build] finished`, `[Push] finished`），仅 [Check] 测试阶段失败。

### 与 PR 变更的关联
**无关。** PR 变更仅包括：
1. 新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` — Docker 构建成功完成（编译通过，二进制生成，推送成功）
2. 更新 `HPC/bwa/README.md` — 新增 tag 描述
3. 更新 `HPC/bwa/doc/image-info.yml` — 新增镜像版本信息
4. 更新 `HPC/bwa/meta.yml` — 新增 tag 到路径映射

PR 未创建或修改 CI 测试脚本 `bwa_test.sh`（该文件位于 CI runner 的 `eulerpublisher` Python 包目录中，不属于本仓库）。Docker 镜像构建的所有步骤（依赖安装、源码下载、编译、清理）均在日志中显示成功。

## 修复方向

### 方向 1（置信度: 中）
**CI 基础设施修复**：CI runner 上的 `bwa_test.sh` 测试脚本文件存在 Windows 换行符（CRLF），需要运维人员在 CI 环境中将文件换行符转换为 Unix 格式（LF），例如执行 `dos2unix` 或 `sed -i 's/\r$//'` 修复。该问题与本次 PR 代码变更无关，Code Fixer 无需进行任何代码修改。

## 需要进一步确认的点
- 无法直接确认 `bwa_test.sh` 文件的具体内容和换行符污染范围（仅能从报错推断 shebang 行受污染）
- 需确认同一 CI runner 上其他镜像的测试脚本是否也存在类似换行符问题，以判断是偶发污染还是系统性问题
- 需确认 `bwa_test.sh` 测试脚本的来源——通过 git 同步还是 CI 预安装，便于从源头修复换行符问题
