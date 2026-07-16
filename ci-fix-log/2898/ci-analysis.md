# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh

## 根因分析

### 直接错误
```
[Build] finished
[Push] finished
[Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
[Check] test failed
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上缺少 `shunit2`（Shell 单元测试框架），导致 [Check] 阶段的容器启动测试脚本无法执行。Docker 镜像构建和推送均已成功完成（Build/Push finished），失败仅发生在 CI 测试框架的检查阶段。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及对应的 README.md、image-info.yml、meta.yml 条目。Docker 镜像构建全部步骤（#1-#11）均执行成功并已推送到 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`。失败源于 CI runner 环境缺少 `shunit2` 依赖。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是 Shell 脚本的 xUnit 风格单元测试框架，需要在 CI runner 上通过包管理器（如 `dnf install shunit2` 或从 GitHub 安装）添加该依赖。

## 需要进一步确认的点
- CI runner 的 `eulerpublisher` 测试环境中 `shunit2` 的预期安装路径和安装方式
- 该 CI runner 是否最近被重建/更新导致 `shunit2` 丢失
- 同一批次的其他 PR 是否也因同样原因失败（验证是否为 runner 级别的系统性问题）
