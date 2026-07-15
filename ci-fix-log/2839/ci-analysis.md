# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI检查工具shunit2缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed, eulerpublisher

## 根因分析

### 直接错误
```
#8 DONE 268.4s
euler_builder_20260709_093422 removed
[Build] finished
[Push] finished
[Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
[Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 的 `[Check]` 阶段在执行 `common_funs.sh` 第 13 行时尝试引用 `shunit2`，但 CI runner 环境中未安装 `shunit2`（shell 单元测试框架），导致检查脚本初始化失败，检查表格为空（无任何检查项执行），最终触发 `Finished: FAILURE`。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 构建阶段（`#8`）完全成功，镜像已成功构建并推送至 registry（`[Build] finished` + `[Push] finished`）。失败发生在 CI 工具 `eulerpublisher` 的 `[Check]` 后处理阶段，属于 CI 基础设施层面缺少 `shunit2` 依赖。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2`：
- `shunit2` 是 shell 脚本单元测试框架，`common_funs.sh` 需要它才能执行镜像健康检查
- 可通过 `dnf install shunit2` 或等效方式在 CI runner 上安装该工具
- 此修复与 `openeuler-docker-images` 仓库代码无关，由 CI 运维团队处理

### 方向 2（置信度: 低）
若 `shunit2` 无法安装到 CI runner 环境，可在 `eulerpublisher` 测试配置中为 postgres 17.6 镜像的 `[Check]` 阶段提供备选检查方式（如直接 `docker run` + `pg_isready` 检查），绕过对 `shunit2` 的依赖。但此为下游工具的修改，不在 `openeuler-docker-images` 仓库范围内。

## 需要进一步确认的点
1. 确认 CI runner 环境（Jenkins/容器编排平台）是否应预置 `shunit2`，或是否本次构建恰好分配到了一台缺少此依赖的 runner
2. 确认 postgres 的其他版本（如 17.6-oe2403sp2）在相同 CI 环境下的 `[Check]` 阶段是否也出现同样的 `shunit2` 缺失错误——如果是，说明是整个 CI 环境的问题；如果否，说明可能与平台/runner 调度有关
3. 虽然 BuildKit `LegacyKeyValueFormat` 警告（Dockerfile 第 26、30 行 `ENV key value` 格式）非失败根因，但建议后续 PR 将 `ENV PGDATA /var/lib/pgsql/data` 和 `ENV PATH ${PATH}:/usr/local/pgsql/bin` 改为 `ENV key=value` 格式以符合最佳实践
