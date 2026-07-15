# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符错误
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, CRLF, bwa_test.sh

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI eulerpublisher 工具内置测试脚本）
- 失败原因: CI 基础设施中 eulerpublisher 工具自带的 `bwa_test.sh` 测试脚本包含 Windows 风格换行符（CRLF，即 `\r\n`），导致 shebang 行 `#!/bin/sh\r` 中的 `\r`（显示为 `^M`）被内核当作解释器路径的一部分，内核无法找到 `/bin/sh\r` 这个不存在的解释器，脚本执行失败。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建（Build）和推送（Push）阶段均已成功完成：
- `#7 DONE 199.0s` — Docker build 所有步骤（yum 安装依赖、curl 下载源码、make 编译、清理）均通过，仅有 `bwt_gen.c` 的两个编译 warning（未使用变量），不影响构建。
- `[Build] finished` / `[Push] finished` — 镜像已成功构建并推送到 `****test/bwa:0.7.18-oe2403sp4-x86_64`。
- 失败仅发生在 CI 流水线的 [Check] 后置测试阶段，且根因是 CI 服务器上 eulerpublisher 工具自带的 `bwa_test.sh` 文件存在 CRLF 换行符问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是一个纯 CI 基础设施问题，需要由 CI 平台运维人员修复：
- 登录 CI runner 节点（`ecs-build-docker-x86-hk`），定位文件 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`
- 使用 `dos2unix` 或 `sed -i 's/\r//'` 将文件换行符从 CRLF 转换为 LF
- 如果该 file 是由 eulerpublisher pip 包安装的，则需从源头修复 eulerpublisher 包内的该文件并重新发布

## 需要进一步确认的点
- 确认该 `bwa_test.sh` 文件是 eulerpublisher 包安装时自带的，还是由其他 CI 步骤动态生成的
- 确认其他使用 bwa 镜像的 PR 是否也因同一测试脚本而失败（如果是，说明该文件已被污染一段时间）
- 确认 aarch64 架构的 build job 是否存在同样的测试脚本问题

