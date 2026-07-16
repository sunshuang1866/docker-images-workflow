# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 在 [Check] 阶段尝试执行容器功能测试时，`common_funs.sh` 脚本引用了 `shunit2` 但 CI runner 环境中未安装该 shell 测试框架。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 postgres 17.6 on openEuler 24.03-LTS-SP4 的 Dockerfile、entrypoint.sh、README.md 更新和 meta.yml 条目，不涉及 CI 测试框架或 runner 环境配置。

Docker 镜像的构建 (`make && make install` 全程成功，`#8 DONE 268.4s`) 和推送 (`#11 DONE 58.0s`，`[Build] finished`，`[Push] finished`) 均已完成，失败仅发生在构建完成后的 [Check] 阶段，因 CI runner 缺少 `shunit2` 导致容器功能测试无法启动。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 CI 基础设施问题——`eulerpublisher` 测试框架在 runner 上缺少 `shunit2` 依赖。需要在 CI runner 环境中安装 `shunit2`（如 `dnf install shunit2 -y` 或将 shunit2 shell 脚本放入测试框架的 `tests/` 目录），或由 CI 维护团队将 `shunit2` 纳入 runner 基础镜像。

## 需要进一步确认的点
- 确认 CI runner（`ecs-build-docker-x86_64-*`）是否已安装了 `shunit2`；若未安装，确认是否应纳入 runner 基础镜像预装依赖。
- 确认同一 CI runner 上其他 Docker 镜像的 Check 测试是否也因同一原因失败，以判断是本次 runner 偶发问题还是环境配置变更导致的系统性缺失。
