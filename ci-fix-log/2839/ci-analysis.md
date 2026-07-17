# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 流水线的 [Check] 阶段（镜像功能测试）执行 `common_funs.sh` 时，尝试 source 引入 `shunit2` 单元测试框架，但 `shunit2` 未安装在当前 CI runner 环境中，导致测试脚本无法运行。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 和 entrypoint.sh 在构建阶段（编译 PostgreSQL 源码 + Docker 镜像构建 + 推送到 registry）均已成功完成：
- PostgreSQL 17.6 源码编译通过（`make -j "$(nproc)" && make install` 全部成功）
- Docker 镜像构建成功（`#11 exporting to image` 完成，manifest 已推送）
- 构建日志中无编译错误、链接错误或镜像构建错误

失败仅发生在构建成功之后的 [Check] 阶段，该阶段由 `eulerpublisher` 编排工具运行容器功能测试，因测试框架 `shunit2` 缺失而无法执行。此为 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 上安装 `shunit2`（`yum install shunit2` 或从源码部署），确保 `common_funs.sh` 第 13 行的 `source shunit2` 能正常找到该框架。

### 方向 2（可选，置信度: 低）
如果 `shunit2` 是新版本的 `common_funs.sh` 引入的依赖但尚未在 CI 环境 rollout，可能需要回退 `eulerpublisher` 测试框架的版本到支持旧脚本的版本。

## 需要进一步确认的点
1. 同一 CI runner 上其他镜像的 [Check] 测试是否也因 `shunit2` 缺失失败？如果是，说明是全局 CI 环境问题，与本次 PR 无关。
2. `shunit2` 是否为 CI runner 标准依赖清单中的包？如果已列入但缺失，可能是 runner 镜像构建问题。
3. `common_funs.sh` 是否为近期更新的文件？如果是新增的 `shunit2` 依赖而 CI runner 尚未更新，则属于测试框架部署滞后。
