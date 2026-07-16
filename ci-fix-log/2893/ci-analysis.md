# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架未安装
- 新模式症状关键词: shunit2, file not found, common_funs.sh, line 13

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI `[Check]` 阶段，`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试运行器（runner）上未安装 `shunit2`（Shell 单元测试框架），导致容器镜像的构建后检查（check）测试脚本无法执行

### 与 PR 变更的关联
**与 PR 变更无关。** PR 的 Docker 镜像构建阶段全部成功：
- 所有 422 个编译目标均成功编译/链接（`[422/422] Linking target named`）
- `meson install` 完成，所有二进制文件和 man 手册已安装
- Docker 镜像层全部成功构建（`#10 DONE`, `#11 DONE`, `#12 DONE`）
- 镜像已成功导出并推送（`#13 exporting manifest list ... done`, `[Push] finished`）

失败仅发生在构建完成后的 `[Check]` 阶段，该阶段由 CI 编排工具 `eulerpublisher` 调用 `shunit2` 执行容器启动测试，但 `shunit2` 未安装在该 runner 上。这是 CI 基础设施问题，PR 引入的 Dockerfile 和配置文件本身没有错误。

## 修复方向

### 方向 1（置信度: 高）
**CI 管理员操作**：在 CI 的 aarch64 测试 runner 上安装 `shunit2` 测试框架。Code Fixer 无需处理，此 PR 的 Dockerfile 代码无需修改。

### 方向 2（置信度: 低）
如果 `shunit2` 安装后仍失败，则需重新触发 CI 获取完整 check 日志来判断容器镜像是否存在运行时问题。但当前日志中构建阶段无任何错误，容器运行时出问题的可能性较低。

## 需要进一步确认的点
- 确认 CI 的 aarch64 runner（`ecs-build-docker-aarch64-*`）上是否已安装 `shunit2` 包
- 确认同类其他 SP4 镜像（如 bind9 9.21.23-oe2403sp3）在同一个 CI runner 上的 `[Check]` 阶段是否也因同样原因失败——若是，则为 CI 环境系统性缺失 `shunit2`

## 修复验证要求
不适用（infra-error，无需 code-fixer 介入）。
