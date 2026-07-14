# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符错误
- 新模式症状关键词: bad interpreter, /bin/sh^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施内的测试脚本）
- 失败原因: CI 编排工具 `eulerpublisher` 打包的 `bwa_test.sh` 测试脚本使用了 Windows 风格换行符（CRLF），shebang 行 `#!/bin/sh\r` 被 shell 解析为解释器路径 `/bin/sh^M`，该路径不存在，导致测试脚本无法执行。Docker 镜像构建和推送均成功完成。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 新增的 bwa 0.7.18 Dockerfile（`HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`）在 CI 中构建完全成功：依赖安装、源码编译、镜像导出、推送到 registry 均无错误（`#7 DONE 199.0s`，`#8 DONE 8.4s`，`[Build] finished`，`[Push] finished`）。失败发生在 CI 后处理阶段——`eulerpublisher` 工具执行镜像验证测试时，其自带的 `bwa_test.sh` 因 CRLF 换行符导致 shebang 解析异常，这是一个纯 CI 基础设施缺陷。

## 修复方向

### 方向 1（置信度: 高）
修复 `eulerpublisher` 包中 `tests/container/app/bwa_test.sh` 文件的换行符格式，将 CRLF 转换为 LF。可使用 `dos2unix` 或在包构建流程中确保测试脚本以 Unix 换行符发布。此修复需要在 `eulerpublisher` 项目仓库中进行，修改后重新发布 eulerpublisher 包即可。

## 需要进一步确认的点
- 确认 `bwa_test.sh` 在 `eulerpublisher` 源码仓中是否原本就是 CRLF 格式，还是在打包/分发过程中被转换。
- 确认是否有其他镜像的测试脚本也存在同样的 CRLF 问题，建议对 `eulerpublisher` 的 `tests/` 目录做一次全面扫描。
