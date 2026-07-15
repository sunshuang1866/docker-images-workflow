# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试工具缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 在 [Check] 阶段执行镜像验证测试时，`common_funs.sh` 脚本第 13 行尝试 `source shunit2`，但 `shunit2` shell 单元测试工具未安装在 CI runner（aarch64 节点）上，导致测试脚本无法运行。

### 与 PR 变更的关联
**与 PR 无关**。该 PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（含 README.md、image-info.yml、meta.yml 配套更新），Docker 镜像的构建和推送阶段均成功完成（日志中 `[Build] finished`、`[Push] finished`、`#11 exporting to image` 全部正常）。失败仅发生在 CI 工具链自身的 [Check] 测试阶段，根因是 CI runner 缺少 `shunit2` 依赖，与 PR 代码变更无任何关联。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner（aarch64 节点）上安装 `shunit2` shell 测试框架。`shunit2` 通常可通过系统包管理器安装（如 `dnf install shunit2`）或从 GitHub 下载并放置到 `$PATH` 可访问的目录中。

### 方向 2（置信度: 低）
如果 `shunit2` 应作为 `eulerpublisher` 包的依赖自动安装但缺失，则需检查 `eulerpublisher` 包的安装完整性，确保其 RPM/deb 包的依赖声明中包含 `shunit2`。

## 需要进一步确认的点
1. `shunit2` 是否为 `eulerpublisher` RPM 包的依赖项？若为依赖但缺失，需修复 RPM 打包规范。
2. 同一 PR 的 x86_64 架构构建是否也以相同原因失败？（当前日志仅含 aarch64 构建日志）
3. 其他使用 openEuler 24.03-LTS-SP4 基础镜像的 PR 是否也遇到了相同的 `shunit2: No such file or directory` 问题——这将确认是 CI runner 上的全局缺失。
