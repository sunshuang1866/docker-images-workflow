# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, CRLF, shebang, bwa_test.sh

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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 工具 `eulerpublisher` 的 [Check] 阶段，文件 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（该脚本属于 eulerpublisher Python 包，非 PR 仓库内文件）
- 失败原因: `bwa_test.sh` 的 shebang 行使用了 Windows 风格 CRLF 行尾（`#!/bin/sh\r\n`），导致操作系统将 `\r` 视为解释器名的一部分，尝试查找 `/bin/sh\r`（即 `/bin/sh` + 回车符），因该名称的文件不存在而报 `bad interpreter: No such file or directory`

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 构建过程完全成功：

1. 所有 yum 依赖安装正常完成（gcc、make、zlib-devel 等 17 个包均安装成功）
2. bwa 0.7.18 源码从 GitHub 下载成功
3. `make clean && make -j "$(nproc)"` 编译成功（仅有 `bwt_gen.c` 中的 2 个编译警告，无错误）
4. 构建产物 `bwa` 二进制文件正常生成并移动到 `/usr/local/bwa/bin/`
5. Docker 镜像构建和推送均成功（`[Build] finished`、`[Push] finished`）

唯一失败发生在 CI 后置验证 [Check] 阶段，CI 工具 `eulerpublisher` 尝试运行 `bwa_test.sh` 对该镜像进行功能测试时，因该测试脚本自身文件格式问题（CRLF 行尾）无法被执行。该测试脚本位于 `eulerpublisher` Python 包的 `/etc/` 目录下，是 CI 基础设施的一部分，不是此次 PR 新增或修改的文件。

## 修复方向

### 方向 1（置信度: 高）
**修复 CI 基础设施中的 `bwa_test.sh` 文件行尾格式。** `eulerpublisher` 包中的 `bwa_test.sh` 需要从 CRLF 转换为 LF。这不是 PR 作者需要修改的，而是 CI 运维人员需要处理 `eulerpublisher` 包中该测试脚本的行尾问题。可以通过 `dos2unix` 或在打包/部署流程中增加行尾规范化步骤解决。

## 需要进一步确认的点
1. `bwa_test.sh` 文件在 `eulerpublisher` 源码仓库中的原始行尾格式是什么 —— 是提交时就包含 CRLF，还是 CI 流水线在某个环节（如 git clone、文件下载、包安装）中意外引入了 CRLF 转换
2. 是否存在其他同类镜像的测试脚本也有 CRLF 问题（如 `bwa_test.sh` 是否是新加入的测试脚本，其他已有测试是否也有类似隐患）
3. 如果 `bwa_test.sh` 是 eulerpublisher 包在本次部署/更新中才添加的，需追溯其来源仓库中是否已包含 CRLF
