# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:161]-INFO: [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上已安装的 eulerpublisher 工具包内 `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（由 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh` 解析得到）
- 失败原因: eulerpublisher 工具包自带的 `bwa_test.sh` 测试脚本使用了 Windows 风格换行符（CRLF），shell（`/bin/sh`）将行尾 `\r`（显示为 `^M`）误读为解释器路径的一部分，导致 `bad interpreter: No such file or directory` 错误。

### 与 PR 变更的关联
**与 PR 变更无关**。该 PR 仅新增了以下文件：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新增 Docker 构建定义）
- `HPC/bwa/README.md`（补充版本标签说明）
- `HPC/bwa/doc/image-info.yml`（补充镜像信息）
- `HPC/bwa/meta.yml`（注册新版本路径）

Docker 镜像的构建阶段（`[Build]`）和推送阶段（`[Push]`）均完全成功：
- Docker build 7 个步骤全部完成，bwa 源码编译链接成功
- 镜像已成功导出并推送到 `docker.io/****test/bwa:0.7.18-oe2403sp4-x86_64`
- 失败发生在 CI 工具链自身的 `[Check]` 测试阶段，即 eulerpublisher 包中 `bwa_test.sh` 脚本因换行符格式问题无法执行

## 修复方向

### 方向 1（置信度: 高）
由 CI 基础设施维护者修复 eulerpublisher 工具包中 `tests/container/app/bwa_test.sh` 文件的换行符格式，将其从 CRLF（Windows）转换为 LF（Unix）。可以使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件后重新打包发布 eulerpublisher。

Code Fixer **无需处理此问题**——该失败为 infra-error，与 PR 代码变更完全无关，重跑 CI 或等待 eulerpublisher 工具包修复后 CI 即可通过。

## 需要进一步确认的点
1. 确认 eulerpublisher 工具包中还有多少其他测试脚本存在相同的 CRLF 问题（`grep -rl $'\r' /etc/eulerpublisher/tests/`）
2. 确认 eulerpublisher 工具包的发布流程中是否存在跨平台文件传输导致换行符自动转换的问题
