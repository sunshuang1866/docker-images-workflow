# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试脚本CRLF行尾
- 新模式症状关键词: ^M, bad interpreter, No such file or directory, bwa_test.sh, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施的 eulerpublisher 包内测试脚本）
- 失败原因: CI 基础设施中 `eulerpublisher` 包自带的 `bwa_test.sh` 测试脚本使用了 Windows 行尾格式（CRLF），shebang 行 `#!/bin/sh` 末尾附带了回车符 `\r`（显示为 `^M`），导致内核查找解释器 `/bin/sh\r` 失败（No such file or directory）。Docker 镜像构建和推送均已完成（日志中清晰可见 `[Build] finished`、`[Push] finished`、`#8 DONE`），失败仅发生在 CI 后处理阶段的 [Check] 测试环节。

### 与 PR 变更的关联
**与 PR 无关。** PR 变更的 4 个文件（新增 Dockerfile、更新 README.md、image-info.yml、meta.yml）均内容正确，Docker 构建阶段成功完成：依赖安装（yum 17 个包）、源码下载（bwa v0.7.18）、编译（make -j）、二进制安装、构建工具清理、镜像导出推送全部通过。失败根源是 CI runner 上已安装的 `eulerpublisher` 包中 `bwa_test.sh` 脚本自身存在 CRLF 行尾问题，属于 CI 基础设施缺陷。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需要修复 `eulerpublisher` 包中的 `bwa_test.sh` 测试脚本，将文件行尾从 CRLF（Windows）转换为 LF（Unix）。这需要更新 `eulerpublisher` 包的源码仓库，确保该脚本使用 Unix 换行符。修复后 CI [Check] 阶段即可正常执行 bwa 容器的功能测试。

## 需要进一步确认的点
- 确认 `eulerpublisher` 包中 `bwa_test.sh` 是否为新增脚本（如果是随本次 bwa 24.03-lts-sp4 支持一起新增的，可能是在编辑时使用了 Windows 编辑器导致），或者是已有脚本的历史遗留问题
- 确认同一 `eulerpublisher` 包中其他应用的测试脚本（如 `tests/container/app/` 目录下其他 `*_test.sh`）是否也存在 CRLF 行尾问题
- 如果仅 `bwa_test.sh` 有该问题，需要追溯该文件的来源：是从 PR 仓库中某处复制而来，还是 eulerpublisher 包自身仓库中的独立文件
