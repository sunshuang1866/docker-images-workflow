# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架shunit2缺失
- 新模式症状关键词: shunit2: file not found, source, eulerpublisher, Check, common_funs.sh

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 编排工具 `eulerpublisher` 在 `[Check]` 阶段执行容器测试时，`common_funs.sh` 尝试 `source shunit2`，但 `shunit2`（Shell 单元测试框架）未安装在 CI runner 上，导致测试脚本无法加载。

### 与 PR 变更的关联
**与 PR 无关**。Docker 镜像构建（meson 编译 422 个目标，全部成功）和推送（push to docker.io）均已完成：

```
#9 DONE 41.4s       ← meson compile + install 成功
#13 exporting to image
#13 pushing layers 15.6s done    ← push 成功
[Build] finished
[Push] finished
```

失败仅发生在 `eulerpublisher` 工具的后置 `[Check]` 阶段，该阶段尝试用 `shunit2` 框架运行容器测试，但 CI runner 环境中缺少 `shunit2` 依赖。PR 新增的 Dockerfile、named.conf 及元数据文件与 CI 工具链的测试框架依赖无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 包（如 `dnf install shunit2` 或 `pip install shunit2`），使 `eulerpublisher` 的 `[Check]` 阶段能够正常加载测试框架并执行容器测试。此修复为 CI 基础设施层面，无需修改 PR 中的任何代码。

### 方向 2（置信度: 低）
若确认 `shunit2` 在当前 CI runner 镜像中无法安装或不应预装，可将 `eulerpublisher` 的 `common_funs.sh` 改为从项目仓库自带 `shunit2` 或使用备选测试框架（如 `bats`）。但此方向需改动 CI 工具代码，成本较高且超出本 PR 范围。

## 需要进一步确认的点
1. **amd64 构建状态**：当前日志仅展示 aarch64 架构的构建过程（push tag 为 `9.21.23-oe2403sp4-aarch64`），需确认 x86-64 架构的构建 job 是否独立运行且成功。若同一 CI run 包含独立的 amd64 job，需获取其日志以确认无其他错误。
2. **shunit2 是否为 runner 标准依赖**：需确认该 CI runner 环境中 `shunit2` 是否为预期预装的包，以及同类型的其他成功 PR 的 Check 阶段是否也依赖 `shunit2`（可能该依赖在近期 CI 基础设施变更中丢失）。
3. **同类 PR 对比**：参考历史模式 `模式39`（`eulerpublisher` 缺少 `distroless` 模块），类似的 CI 工具链依赖缺失问题在此仓库中已有先例，建议检查 CI 基础设施的依赖清单完整性。
