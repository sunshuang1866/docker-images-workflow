# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符
- 新模式症状关键词: bad interpreter, ^M, CRLF, bwa_test.sh, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI runner 上的 `eulerpublisher` 包内测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`
- 失败原因: `bwa_test.sh` 脚本使用了 Windows 换行符（CRLF），shebang 行 `#!/bin/sh` 末尾附带了回车符 `\r`（日志中显示为 `^M`），导致 `/bin/sh^M` 被当作解释器路径，触发 `bad interpreter: No such file or directory`

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了以下文件：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新 Dockerfile 用于 openEuler 24.03-LTS-SP4）
- `HPC/bwa/README.md`（文档更新）
- `HPC/bwa/doc/image-info.yml`（镜像信息更新）
- `HPC/bwa/meta.yml`（标签映射更新）

Docker 镜像构建完全成功（日志显示 `[Build] finished`、`[Push] finished`，编译和推送均无错误）。失败仅发生在 CI runner 内置的 `eulerpublisher` 测试脚本执行阶段，该脚本是 CI 基础设施的一部分，不包含在 PR 改动中。

## 修复方向

### 方向 1（置信度: 中）
CI 维护者需要修复 `eulerpublisher` 包中的 `bwa_test.sh` 文件，将其换行符从 CRLF（Windows 风格）转换为 LF（Unix 风格）。可通过 `dos2unix bwa_test.sh` 或 `sed -i 's/\r$//' bwa_test.sh` 处理。

### 方向 2（置信度: 低）
如果 `bwa_test.sh` 是 CI 从某个代码仓库动态拉取的（而非 eulerpublisher 包的内置文件），则需要检查该上游仓库中测试脚本的换行符设置，确保 `.gitattributes` 或编辑器配置不会在 checkout 时自动转换为 CRLF。

## 需要进一步确认的点
- 确认 `bwa_test.sh` 文件的来源：是 `eulerpublisher` RPM/Python 包内置的，还是 CI 运行时从其他仓库克隆的
- 确认是否仅有 `bwa_test.sh` 有此问题，还是同类新增的测试脚本（其他 HPC 镜像如 `cesm`、`seissol`）也有 CRLF 问题
- 如果该脚本是近期新增的，需回溯 git 历史确认是谁在何时以 CRLF 格式提交的
