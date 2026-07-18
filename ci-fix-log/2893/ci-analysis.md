# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI 环境的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI runner 的 `[Check]` 阶段在执行容器镜像检查测试脚本时，`common_funs.sh` 尝试通过 `.` (source) 加载 `shunit2` 测试框架，但该框架在 CI 环境中未安装/不在 `PATH` 中，导致检查脚本无法运行。

### 与 PR 变更的关联

与 PR 变更**无关**。证据如下：

1. **Docker 构建完全成功**：日志显示 `meson compile` 完成全部 422 个编译目标、`meson install` 完成所有二进制文件安装，Docker build 的 6 个步骤全部 `DONE`（#9 DONE 41.4s, #10 DONE 0.2s, #11 DONE 0.0s, #12 DONE 0.1s）。
2. **镜像推送成功**：`#13 pushing layers 15.6s done`，`[Push] finished`，镜像 `openeulertest/bind9:9.21.23-oe2403sp4-aarch64` 已成功推送至 registry。
3. **失败仅发生在 Check 阶段**：`eulerpublisher` 的 `[Build]` 和 `[Push]` 均报告 `finished`，仅 `[Check]` 阶段因 `shunit2` 缺失而 `CRITICAL`。
4. **PR 未修改任何 CI 配置或测试脚本**：PR 仅引入 bind9 的 Dockerfile、named.conf、README 表项、meta.yml 条目和 image-info.yml 表项。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。这属于 CI 基础设施维护，非代码层面问题。PR 代码本身无需修改。

## 需要进一步确认的点
- `shunit2` 是否应预装在 CI 所使用的 `eulerpublisher` 容器/环境中？如果是，需要确认该 runner 镜像是否被误更新/回退导致该依赖丢失。
- 是否存在其他同类 PR 在相同时间窗口（2026-07-10 前后）因同一 `shunit2` 缺失而失败？若是，可确认为 CI 基础设施的全局故障而非本 PR 特有问题。
