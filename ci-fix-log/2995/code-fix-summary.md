# 修复摘要

## 修复的问题
无需代码修改 — 此CI失败为基础设施问题（infra-error），与PR代码无关。

## 修改的文件
无

## 修复逻辑
CI失败分析报告确认失败类型为 `infra-error`，根因是 CI 基础设施中 `eulerpublisher` 工具包的 `bwa_test.sh` 测试脚本使用了 Windows 风格（CRLF）换行符，导致 shebang 行 `/bin/sh^M` 解析为不存在的解释器路径 `/bin/sh\r`，脚本无法执行。

PR变更仅涉及：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新增 bwa 编译构建逻辑）
- `HPC/bwa/README.md`（文档更新）
- `HPC/bwa/doc/image-info.yml`（版本信息更新）
- `HPC/bwa/meta.yml`（元数据更新）

以上文件均不包含 shell 脚本，不涉及换行符问题。Docker 镜像的构建和推送阶段均成功完成，失败仅发生在 CI 后置 Check 阶段。

**应由 CI 基础设施维护者**在 `eulerpublisher` 仓库中将 `bwa_test.sh` 的换行符转换为 Unix 风格（LF），然后重新发布/部署该包到 CI 运行节点。修复后重新触发 CI 即可通过。

## 潜在风险
无