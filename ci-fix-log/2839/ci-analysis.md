# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-09 09:40:24,013-INFO: [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13（CI runner 上的 eulerpublisher 测试框架脚本）
- 失败原因: CI runner 环境中的 `eulerpublisher` 测试脚本 `common_funs.sh` 第 13 行尝试加载 `shunit2` shell 单元测试框架，但该依赖未安装在 runner 上，导致 [Check] 阶段测试无法执行而失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 和 entrypoint.sh 在 [Build] 和 [Push] 阶段均成功完成：
- Docker 构建（`make -j "$(nproc)" && make install`）正常完成（#8 DONE 268.4s）
- 镜像导出与推送正常完成（#11 DONE 58.0s）
- 日志明确显示 `[Build] finished` 和 `[Push] finished`

失败发生在 CI 自身的测试基础设施层面——runner 缺少 `shunit2` 依赖，与 Dockerfile 或 entrypoint.sh 的内容无关。Code Fixer 无需处理。

## 修复方向

### 方向 1（置信度: 高）
无需修改 PR 代码。需要在 CI runner 环境中安装 `shunit2`（可通过 `dnf install shunit2` 或 `pip install shunit2`，具体取决于 eulerpublisher 期望的安装方式），然后重新触发 CI 流水线。

## 需要进一步确认的点
1. 确认 `shunit2` 在 openEuler 24.03-LTS-SP4 上的正确安装方式（RPM 包名 vs pip 包名）
2. 确认是否只有该 runner 缺少 `shunit2`，还是所有 x86_64 runner 均缺失（可通过查看同一 runner 上其他镜像的 [Check] 阶段日志来验证）
3. 确认 eulerpublisher 框架对 `shunit2` 的依赖声明是否完整（是否在 `setup.py`/`pyproject.toml` 中列为依赖）
