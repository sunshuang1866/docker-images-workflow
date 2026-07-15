# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2依赖缺失
- 新模式症状关键词: shunit2, file not found, eulerpublisher, Check test failed

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
- 失败位置: CI 基础设施的 Check 阶段（`eulerpublisher` 工具容器的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`）
- 失败原因: CI 执行环境（eulerpublisher 容器镜像）中缺少 `shunit2` shell 单元测试框架，导致 `common_funs.sh` 通过 `. shunit2` source 该框架时失败。Docker 镜像的构建和推送阶段均已完成并成功。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 变更仅为新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套配置、元数据文件。日志显示：

1. **meson 构建成功**：422 个编译目标全部完成，最终 "Linking target named" 成功。
2. **meson install 成功**：所有二进制文件和 man 手册页均已安装到 `/usr` 目录（`#9 DONE 41.4s`）。
3. **Docker 镜像构建成功**：所有 6 个构建步骤均 `DONE`。
4. **镜像推送成功**：`[Push] finished`，推送到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`。
5. **失败发生在 eulerpublisher 的 Check 阶段**：该阶段是一个独立的测试编排步骤，依赖 CI 基础设施中预装的 `shunit2` 框架，而非 PR 引入的任何代码。

## 修复方向

### 方向 1（置信度: 高）
此失败为 infra-error，与 PR 代码无关，无法也无需通过修改 PR 文件修复。需要在 CI 基础设施侧解决：
- 在 eulerpublisher 容器镜像的构建中安装 `shunit2` 包（openEuler 中通常为 `shunit2` RPM 包）。
- 或将 `shunit2` 脚本放到 `common_funs.sh` 可访问的路径（如 `$PATH` 或 `common_funs.sh` 同级目录）。

## 需要进一步确认的点
- 该 CI runner/eulerpublisher 容器镜像是否在其他 PR 的 Check 阶段也已出现同类 `shunit2` 找不到的问题（即这是一个系统性问题还是当前 runner 的个案）。
- `shunit2` 框架是否应从 eulerpublisher 源码仓库中携带而非依赖系统安装。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
无需。此失败为 infra-error，不涉及任何代码或正则修改。
