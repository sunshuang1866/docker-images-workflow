# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: `bad interpreter, ^M, No such file or directory, bwa_test.sh`

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段，执行 `bwa_test.sh` 测试脚本时
- 失败原因: CI 基础设施（eulerpublisher 包）中的测试脚本 `bwa_test.sh` 第一行 shebang 末尾包含 Windows 回车符 `\r`（日志中显示为 `^M`），导致内核尝试查找名为 `/bin/sh\r` 的解释器，该路径不存在，脚本无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 的 Diff 仅涉及：
- 新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（bwa 的 openEuler 24.03-LTS-SP4 构建定义）
- 更新 `HPC/bwa/README.md`、`HPC/bwa/doc/image-info.yml`、`HPC/bwa/meta.yml`（注册新镜像标签）

Docker 镜像的构建和推送阶段均已成功完成：
- `#7 DONE 199.0s` — Docker 构建成功（yum 安装依赖、curl 下载源码、make 编译、yum 卸载构建工具均正常）
- `#8 DONE 8.4s` — 镜像推送成功
- `[Build] finished` / `[Push] finished` 均输出成功

失败发生在 CI 编排工具 `eulerpublisher` 的测试脚本执行阶段，属于基础设施层面的文件格式问题（脚本被提交或部署时使用了 CRLF 行尾而非 LF），与本次 PR 新增的 Dockerfile 及元数据文件无关。

## 修复方向

### 方向 1（置信度: 高）
将 eulerpublisher 仓库中的 `tests/container/app/bwa_test.sh` 文件的行尾从 CRLF 转换为 LF（Unix 格式）。可使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件后重新提交到 eulerpublisher 仓库。PR 作者无需对本仓库（openeuler-docker-images）做任何修改。

## 需要进一步确认的点
- 确认 eulerpublisher 仓库中 `bwa_test.sh` 文件是否确实以 CRLF 行尾提交，以及是否有其他测试脚本存在同样的问题。
- 本日志仅包含 x86-64 架构的构建，aarch64 架构的构建日志未提供。虽然 build + push 阶段成功，无法完全排除 aarch64 存在其他问题，但当前 x86-64 侧的失败根因已明确为 infra-error。
