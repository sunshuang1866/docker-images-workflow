# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: CI runner 上 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 运行环境中缺少 `shunit2`（Shell 单元测试框架），`common_funs.sh` 在第 13 行尝试加载 `shunit2` 时报 `No such file or directory`，导致 `[Check]` 容器验证阶段失败。

### 构建阶段均已成功
日志明确显示 Docker 镜像构建和推送流程全部正常完成：

- 步骤 1/5（安装依赖 + 下载 Go 1.25.6）: `#7 DONE 67.8s`
- 步骤 2/5（touch 文件时间戳）: `#8 DONE 40.5s`
- 步骤 3/5（创建 GOPATH + 移除编译工具）: `#9 DONE 1.5s`
- 步骤 4/5（WORKDIR）: `#10 DONE 0.0s`
- 镜像导出 & 推送: `#11 DONE 41.9s`
- 构建完成信息: `[Build] finished`、`[Push] finished`

失败仅发生在 `[Check]` 阶段，CI 编排工具 `eulerpublisher` 尝试对已推送的镜像执行测试验证时，因 `shunit2` 框架缺失而崩溃。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（34 行），以及对应的 README.md、image-info.yml、meta.yml 元数据更新。这些变更不涉及 CI 测试框架的配置或依赖安装逻辑。`shunit2` 缺失是 CI runner 自身环境问题，非 PR 代码引入。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner（aarch64 节点 `ecs-build-docker-aarch64-01-sp` 或同类节点）上安装 `shunit2`。该工具是 `eulerpublisher` 容器测试套件的运行时依赖，需确保在所有执行 `[Check]` 阶段的 CI runner 上可用。安装后重新触发 CI 即可验证修复效果。

### 方向 2（可选）
若 `shunit2` 已在 CI runner 上安装但不在脚本的搜索路径内，可在 `common_funs.sh` 中将 `shunit2` 的 source 路径改为绝对路径（如 `/usr/share/shunit2/shunit2`）或通过环境变量 `SHUNIT2_HOME` 指定。但这属于 CI 基础设施配置问题，不应由 PR 提交方修复。

## 需要进一步确认的点
1. 该 aarch64 CI runner 上其他成功构建的镜像是否同样经过 `[Check]` 测试阶段——若其他镜像跳过 Check 则说明此 runner 历来缺少 `shunit2`，问题范围可能仅限于该 runner。
2. `shunit2` 在 CI runner 上是以 RPM 包（openEuler 中包名可能为 `shunit2`）安装还是以源码/脚本形式部署，确认安装方式后由 CI 管理员执行。

## 修复验证要求
无需 code-fixer 执行额外验证。此问题为 CI 基础设施配置问题，非代码层面修复。若 CI 管理员完成 `shunit2` 安装后，重新触发 PR #2898 的 CI 流水线，观察 `[Check]` 阶段是否通过即可。
