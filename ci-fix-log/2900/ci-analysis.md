# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架shunit2缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: CI `[Check]` 阶段的测试框架初始化阶段（`common_funs.sh:13`）
- 失败原因: CI runner 环境中缺少 `shunit2`（shell 单元测试框架），`common_funs.sh` 尝试 `source shunit2` 时文件不存在，导致所有检查测试项无法加载执行，检查结果表完全为空。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、httpd-foreground 脚本、meta.yml 条目及 README 文档。Docker 镜像构建和推送阶段均成功完成（`[Build] finished`、`[Push] finished`，镜像 sha256 正常生成并推送至 registry），失败完全发生在 CI 测试框架自身的初始化阶段。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题。CI runner 上缺少 `shunit2` 测试框架。需在 CI runner 环境中安装 `shunit2`，或确保 `common_funs.sh` 中 `source` 的路径指向 `shunit2` 的正确安装位置。

### 方向 2（置信度: 低）
如果该 CI runner 是全新部署的或专用于 openEuler 24.03-LTS-SP4 构建，可能遗漏了测试框架的预装步骤。需检查该 runner 的初始化脚本是否包含 `shunit2` 安装。

## 需要进一步确认的点
- 同一 CI runner 节点上，其他镜像的 `[Check]` 测试是否也失败（以此判断是节点级别还是镜像级别的问题）。
- `shunit2` 预期安装路径及 `common_funs.sh` 中 `source` 的完整路径解析逻辑。
- 该 `[Check]` 阶段是否有对 httpd 镜像特定的集成测试定义（检查结果表为空意味着所有检查项均未注册，仅 `shunit2` 缺失就足以导致此表现）。
