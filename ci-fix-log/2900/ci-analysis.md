# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI测试框架shunit2缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, .: shunit2, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 eulerpublisher 在执行 `[Check]` 阶段时，`common_funs.sh` 脚本尝试通过 `. shunit2` 引入 shunit2 测试库，但 shunit2 在 CI runner 环境中不可用（未安装或未被正确配置到 `PATH`），导致所有检查项未能执行，检查结果表为空。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件（meta.yml、README.md、image-info.yml），Docker 镜像构建和推送均已成功完成（`#10 DONE 41.6s`，`[Build] finished`，`[Push] finished`，镜像已成功推送到 `docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64`）。失败发生在构建完成之后的 `[Check]` 阶段，且错误为 CI runner 环境缺少 shunit2 测试框架，与 PR 的代码改动无直接因果关系。

## 修复方向

### 方向 1（置信度: 中）
这是 CI 基础设施问题，需在 CI runner 环境中安装 shunit2。在 openEuler 上可通过 `dnf install shunit2 -y` 安装。如果 shunit2 应当随 eulerpublisher 包一起部署（作为 eulerpublisher 的测试依赖），则应在 eulerpublisher 的打包/部署流程中补充该依赖。

### 方向 2（置信度: 低）
检查 eulerpublisher 测试脚本 `common_funs.sh` 第 13 行中 `shunit2` 的引用路径是否正确。如果 shunit2 确实已安装在 runner 上但路径拼写有误（例如应为 `shunit2.0` 或需要指定完整路径），则修正路径引用。此方向概率较低，因为 shunit2 在 openEuler 上的包名和类库名就是 `shunit2`。

## 需要进一步确认的点
1. 确认 CI runner（本次运行的 executor 节点）上 shunit2 是否已安装：`dnf list installed shunit2` 或 `rpm -q shunit2`。
2. 确认同一 CI 流水线中其他成功 PR 的 `[Check]` 阶段是否也引用了 `shunit2`——如果其他 PR 的 check 步骤不使用 shunit2，则可能是 httpd 镜像的测试定义触发了对 shunit2 的引用。
3. 确认 `common_funs.sh` 脚本中 `shunit2` 的引用是相对于哪个目录或是否依赖 `PATH` 环境变量。
4. 注意日志中存在一个非致命 Docker 构建警告：`LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 5)`，这是 Dockerfile 第 5 行 `ENV HTTPD_PREFIX /usr/local/apache2` 使用了旧式格式，仅为风格建议，非构建错误。
