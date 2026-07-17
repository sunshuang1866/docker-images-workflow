# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39「CI工具依赖缺失」同类但错误不同）
- 新模式标题: 测试框架依赖缺失
- 新模式症状关键词: `shunit2: file not found`, `common_funs.sh`, `source`, `[Check] test failed`

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh`:13
- 失败原因: CI runner 的 eulerpublisher 测试框架中 `common_funs.sh` 尝试 `source shunit2`（Shell 单元测试框架），但该 CI 节点上 `shunit2` 文件不存在，导致 `[Check]` 阶段的容器健康检查测试无法启动。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf 及更新元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像的构建和推送阶段均已成功完成：

- 构建阶段：422/422 编译目标全部通过，并完成 `meson install`（日志: `#9 DONE 41.4s`）
- 推送阶段：`openeulertest/bind9:9.21.23-oe2403sp4-aarch64` 推送成功（日志: `[Build] finished`、`[Push] finished`）
- 失败仅发生在构建后 `[Check]` 阶段，因 CI runner 缺少 `shunit2` 测试框架依赖

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题，Code Fixer 无需处理此 PR。需要 CI 运维在对应的 runner 节点上安装 `shunit2` 测试框架。若该 runner 之前曾正常工作，可能是近期 runner 镜像更新/重装导致 `shunit2` 丢失，恢复安装即可。

### 方向 2（置信度: 中）
若 `shunit2` 应该是 eulerpublisher 自带依赖而非系统包，则需检查 `eulerpublisher` 包的安装完整性——该 CI 节点上 eulerpublisher 的 `tests/container/common/` 目录可能缺少 `shunit2` 文件，需重新部署或更新 eulerpublisher 包。

## 需要进一步确认的点
1. 此日志仅覆盖 aarch64 架构构建（镜像 tag 为 `9.21.23-oe2403sp4-aarch64`），需要确认 x86_64 架构构建 job 的日志是否存在其他问题。
2. 确认该 CI runner 上 `shunit2` 是否曾存在（如路径 `/usr/local/etc/eulerpublisher/tests/container/common/shunit2`），判断是初次缺失还是 accidental removal。
3. 检查同一时间段内其他 PR 的 CI 是否也出现同类 `shunit2: file not found` 错误，以排除 runner 个体故障 vs 全局 CI 环境退化。
