# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39同类，但具体缺失组件不同）
- 新模式标题: CI 测试工具缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 运行器环境 — `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行器上未安装 `shunit2`（Shell 单元测试框架），导致容器镜像的 `[Check]` 验证阶段无法执行测试脚本，`common_funs.sh` 中 `source` 或调用 `shunit2` 时找不到该命令。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建（Step #1–#11）和推送均已成功完成：

- 日志明确显示 `[Build] finished` 和 `[Push] finished`
- 镜像 `openeulertest/go:1.25.6-oe2403sp4-aarch64` 已成功构建并推送到 `docker.io`
- 失败仅发生在构建完成后的 `[Check]` 测试阶段，原因是 CI runner 缺少 `shunit2` 工具

PR 仅新增了一个 Go 1.25.6 的 Dockerfile、更新了 README.md、image-info.yml 和 meta.yml，均为纯配置/文档类变更，不涉及任何构建逻辑修改。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 工具。openEuler 24.03-LTS-SP4 可通过以下方式安装：

```
dnf install -y shunit2
```

或由 CI 运维团队在 runner 镜像中将 `shunit2` 预装到 `/usr/local/etc/eulerpublisher/tests/container/common/` 可发现的路径下。

## 需要进一步确认的点
- 同一 CI runner 上其他镜像（非本次 PR 的镜像）的 `[Check]` 测试是否也因同样原因失败？如果是，说明这是 CI 环境的普遍问题而非本次 PR 独有。
- 确认 `shunit2` 的确切安装路径要求——`common_funs.sh:13` 是通过 `PATH` 查找还是引用了硬编码路径。
