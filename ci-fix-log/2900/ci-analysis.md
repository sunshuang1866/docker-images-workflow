# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

Check 结果表为空，无任何测试项目实际运行：
```
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: CI [Check] 阶段，`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上未安装 `shunit2` 测试框架，`common_funs.sh` 脚本尝试 `source` 加载 `shunit2` 时文件不存在，导致 [Check] 阶段无法执行容器启动/功能测试，直接报错退出。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、`httpd-foreground` 启动脚本及配套元数据文件。Docker 镜像构建和推送均已完成且成功：

- `#10 DONE 41.6s` — httpd configure/make/make install 成功
- `#11 DONE 0.1s` — 配置修改步骤成功
- `#12 DONE 0.0s` — COPY 成功
- `#13 DONE 0.1s` — chmod 成功
- `#14 DONE 31.3s` — 镜像导出、推送成功（`manifests sha256:b38237a...`）
- `[Build] finished` / `[Push] finished` — 构建流水线确认完成

失败仅发生在构建之后的 [Check] 测试阶段，且根因为 runner 缺少 `shunit2` 测试依赖，与本次 PR 的 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 的测试执行环境中安装 `shunit2` 测试框架，或在 `eulerpublisher` 工具的容器测试脚本中将 `shunit2` 作为依赖声明并自动安装。这不是 PR 代码层面可以修复的问题，需要 CI 基础设施团队介入，确保负责执行容器镜像健康检查的 runner 节点上已部署 `shunit2`。

## 需要进一步确认的点
1. 同一个 CI runner 上其他 PR 的 [Check] 阶段是否也失败了？如果是，说明该 runner 节点上 `shunit2` 是系统级缺失，影响面不只本 PR。
2. 本 PR 需要的 `shunit2` 是否应该随 `eulerpublisher` 包一起安装，还是需要单独的 CI 预置步骤。
3. 确认此前 SP4 相关的 PR（如同类 httpd 的 24.03-lts-sp2 Dockerfile）在该 runner 上的 [Check] 是否正常通过，以排除是新增 runner 节点未完成初始化的可能。

## 修复验证要求
不适用（infra-error，非代码修复）。
