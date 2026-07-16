# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺少shunit2
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
[Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 后置测试阶段（`[Check]`）中，`eulerpublisher` 工具的测试框架脚本 `common_funs.sh` 尝试通过 `source` 加载 `shunit2`（Shell 单元测试库），但该库未安装在 CI runner 上，导致测试初始化失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（45 行）、配置文件 `named.conf`（14 行），以及更新 `README.md`、`image-info.yml`、`meta.yml` 中的表项。日志显示 Docker 构建（422 个编译目标全部通过）和镜像推送均已成功完成。失败发生在构建完成之后的 `[Check]` 阶段——`eulerpublisher` 工具的容器测试框架因缺少 `shunit2` 依赖而崩溃，属于 CI 基础设施问题，与本次 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
CI 管理员应在 runner 节点上安装 `shunit2` 测试框架。在 openEuler 环境中可通过包管理器安装：
- `yum install shunit2` 或 `dnf install shunit2`
- 若包仓库无此包，可将 `shunit2` 脚本下载到 CI runner 的 `/usr/local/etc/eulerpublisher/tests/` 路径下或修改 `common_funs.sh` 中的 `source` 路径指向 `shunit2` 实际位置。

### 方向 2（置信度: 中）
如果 `shunit2` 应由 `eulerpublisher` 包自身作为依赖拉取或 vendoring 管理，则需要在 `eulerpublisher` 的打包/部署流水线中补充该依赖，而非在 runner 上单独安装。

## 需要进一步确认的点
- 确认 CI runner 节点上是否曾安装过 `shunit2`（是否为近期环境变更导致该依赖丢失）
- 确认其他使用 `[Check]` 阶段测试的 PR（如同期其他镜像的 PR）是否也存在相同的 `shunit2: file not found` 失败，以判断这是个别 runner 问题还是全局 CI 基建问题
- 确认 x86_64 架构的构建 job 日志是否也显示了同样的 `[Check]` 阶段失败（当前日志仅展示了 aarch64 的完整构建流程）

## 修复验证要求
无需验证——此为 `infra-error`，修复在 CI 基建层面，与代码无关。若后续 CI 管理员修复了 `shunit2` 的安装问题，重新触发 CI 即可验证。
