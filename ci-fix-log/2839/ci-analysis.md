# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2缺失检查失败
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 的 [Check] 阶段中，测试框架脚本 `common_funs.sh` 尝试加载 `shunit2`（Shell 单元测试框架），但 `shunit2` 在 CI runner 环境中不可用，导致检查步骤直接失败。

### 上下文分析
- Docker 镜像构建（[Build]）阶段完全成功：`make install` 执行完毕，所有 postgres 组件正常安装，镜像导出并推送成功（`#11 DONE 58.0s`）。
- Docker 仅有 2 个非致命 LegacyKeyValueFormat 警告（`ENV key=value` 格式建议），不影响构建。
- 失败仅发生在构建后的 [Check] 阶段——CI 框架试图用 `shunit2` 运行容器健康检查测试时，因 `shunit2` 未安装而直接报错退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 此次 PR 仅新增了 postgres 17.6 的 Dockerfile、entrypoint.sh、README.md 更新和 meta.yml 条目。所有新增/变更内容均未涉及 `shunit2` 的安装或 CI 测试配置。Dockerfile 中的依赖安装（`yum install ...`）也已正确包含 `shadow-utils`（参考历史模式05）。构建阶段的完整成功进一步证实 PR 代码本身没有问题。

## 修复方向

### 方向 1（置信度: 中）
CI runner 环境缺少 `shunit2` Shell 测试框架。需在 CI runner 的测试环境初始化脚本中安装 `shunit2`（例如通过 `dnf install shunit2` 或手动部署 `shunit2` 脚本到 runner 的 `PATH` 中），使 `common_funs.sh` 能正确加载该框架。

### 方向 2（置信度: 低）
若 `shunit2` 已安装在 CI runner 上但路径配置有误，检查 `common_funs.sh` 中第 13 行对 `shunit2` 的引用路径是否正确，或 runner 的 `PATH` 环境变量是否包含 `shunit2` 所在目录。

## 需要进一步确认的点
1. 该 CI runner（`ecs-build-docker-aarch64-01-sp` 或同类节点）上是否应预装 `shunit2`？是否近期做过 runner 环境变更导致 `shunit2` 被移除？
2. 其他同类 PR（如其他 postgres 版本的类似新镜像提交）在同一时间段是否也出现了相同的 `shunit2` 缺失错误？若否，则可能是该特定 runner 节点的环境问题。
3. `shunit2` 的标准安装路径在 openEuler 上是什么包名（`shunit2` vs `shunit2-ng`？）——需确认 dnf 仓库中是否提供该包。

## 修复验证要求
无。此失败属于 CI 基础设施问题，与 PR 代码变更无关，Code Fixer 无需对 Dockerfile 或 entrypoint.sh 进行任何修改。
