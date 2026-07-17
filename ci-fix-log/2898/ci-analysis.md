# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39「CI工具依赖缺失」部分相似）
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 的 [Check] 阶段依赖 `shunit2`（shell 单元测试框架）来执行容器镜像启动验证，但 `shunit2` 未安装在当前 CI runner 上，导致 `common_funs.sh` 脚本第 13 行 source `shunit2` 时失败。

### 与 PR 变更的关联
**与 PR 无关。** 证据如下：
1. Docker 镜像构建（#7~#11）**全部成功**：[Build] finished、[Push] finished、镜像已推送到 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`。
2. 失败仅发生在 CI 编排工具 `eulerpublisher` 的 [Check] 阶段，在该阶段中 CI runner 自身的测试脚本 `common_funs.sh` 因缺少 `shunit2` 而崩溃。
3. PR 变更仅涉及新增 `Others/go/1.25.6/24.03-lts-sp4/Dockerfile`、更新 `README.md`、`doc/image-info.yml` 和 `meta.yml`，不涉及任何 CI 基础设施配置或测试脚本的修改。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境上安装 `shunit2` 包（如通过 `dnf install shunit2` 或 `pip install shunit2`），使 `common_funs.sh` 第 13 行的 source 命令能够成功加载该框架。此修复与 PR 代码完全无关，为纯 CI 基础设施配置问题。

## 需要进一步确认的点
- 确认该 CI runner 上 `shunit2` 是否曾经可用但因环境变更而丢失。
- 确认同一 runner 上其他镜像的 [Check] 阶段是否也因同样原因失败（如果是，说明是系统性的 CI 环境问题）。
- 确认 `shunit2` 在 openEuler 24.03-LTS-SP4 仓库中的包名（`shunit2` 或 `shunit2-ng`）。
