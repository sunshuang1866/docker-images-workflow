# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh`:13
- 失败原因: CI 的 [Check] 阶段测试脚本 `common_funs.sh` 尝试通过 `. shunit2` 引入 shunit2 shell 测试框架，但 shunit2 在当前 aarch64 CI runner 上未安装或不在 PATH 中，导致测试阶段直接失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 `Others/bind9/9.21.23/24.03-lts-sp4/Dockerfile`、`named.conf`、更新了 README.md 和 meta.yml。

Docker 镜像构建成功：所有 422 个 C 编译目标编译通过、链接完成、`meson install` 安装完成、镜像导出和推送均已完成（`[Build] finished`、`[Push] finished`）。失败仅发生在 CI 自身的测试框架层（eulerpublisher 的 Check 阶段），`shunit2` 未安装在 aarch64 CI runner 上是基础设施问题，与 Dockerfile 或任何 PR 中的代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
CI 运维在 aarch64 runner 节点上安装 `shunit2` shell 测试框架。shunit2 是 eulerpublisher Check 阶段的运行时依赖，当前该 runner 缺失此依赖。可通过以下方式之一修复：
- 在 CI runner 上执行 `dnf install shunit2` 或 `pip install shunit2`
- 在 eulerpublisher 容器镜像的构建流程中补充安装 shunit2

**此问题无需 PR 作者或 Code Fixer 处理**，属于 CI 基础设施运维问题。

## 需要进一步确认的点
- 确认 amd64 runner 上是否也有同样的 `shunit2` 缺失问题（当前日志仅包含 aarch64 的构建和检查记录，如 amd64 runner 正常，则问题仅限于 aarch64 runner 的环境配置）。
- 确认 shunit2 在 openEuler 24.03-LTS-SP4 上的包名和可用性（可能是 `shunit2`、`shunit` 或 `shunit2-ng`）。
