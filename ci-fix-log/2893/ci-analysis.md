# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39 `CI工具依赖缺失` 同类但症状不同）
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试编排工具 `eulerpublisher` 的 `common_funs.sh` 脚本在第 13 行尝试 source `shunit2`（Shell 单元测试框架），但 `shunit2` 文件在 CI runner 上不存在，导致 [Check] 阶段无法执行容器健康检查而失败

### 与 PR 变更的关联
**此失败与 PR 变更完全无关。** 证据如下：
1. Docker 镜像构建阶段全部成功（422/422 编译步骤通过，`meson setup`、`meson compile`、`meson install` 均正常完成）
2. Docker 镜像推送阶段成功（manifest 成功推送到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`）
3. 失败仅发生在 CI 自身的 [Check] 后置验证阶段，原因是 CI runner 宿主机缺少 `shunit2` Shell 测试框架
4. PR 仅新增 Dockerfile、named.conf 及更新元数据文件，未引入任何可能影响 CI 工具链的变更

## 修复方向

### 方向 1（置信度: 高）
**此问题无需修改 PR 代码。** CI runner 环境缺少 `shunit2` 依赖，需由 CI 基础设施维护方处理。具体操作：
- 在 CI runner 镜像或构建节点上安装 `shunit2`（如 `dnf install shunit2` 或手动部署 shunit2 脚本到 `/usr/local/etc/eulerpublisher/tests/common/` 目录）
- 或在 `eulerpublisher` 工具部署流程中补充 `shunit2` 依赖的自动安装步骤

## 需要进一步确认的点
1. 确认该 CI runner 节点上其他镜像的 [Check] 步骤是否同样失败——若普遍失败，则进一步证实为 CI 基础设施全局问题
2. 确认 x86_64（amd64）架构的构建 job 是否也存在相同问题（当前日志仅展示了 aarch64 的构建）
3. 确认 `shunit2` 在 CI 环境中的预期安装路径和安装方式
