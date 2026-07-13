# CI 失败分析报告

## 基本信息
- PR: #3135 — chore(oneapi-basekit): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构不匹配（meta缺失arch约束）
- 新模式症状关键词: does not have a compatible architecture, x86_64, aarch64, intel-basekit

## 根因分析

### 直接错误
```
#11 75.93 Error: 
#11 75.93  Problem 1: cannot install the best candidate for the job
#11 75.93   - package intel-basekit-2025.3.2-19.x86_64 from oneAPI does not have a compatible architecture
#11 75.93   - nothing provides intel-oneapi-base-toolkit >= 2025.3.2 needed by intel-basekit-2025.3.2-19.x86_64 from oneAPI
#11 75.93  Problem 2: cannot install the best candidate for the job
#11 75.93   - package intel-opencl-23.43.27642.52-803.el9_3.x86_64 from intel-graphics-9.3-unified does not have a compatible architecture
#11 75.93  Problem 3: cannot install the best candidate for the job
#11 75.93   - package intel-level-zero-gpu-1.3.27642.52-803.el9_3.x86_64 from intel-graphics-9.3-unified does not have a compatible architecture
```

### 根因定位
- 失败位置: `AI/oneapi-basekit/2024.2.0/24.03-lts-sp4/Dockerfile:30`（`yum install` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-01-sp`）上构建该 Dockerfile，但 Intel oneAPI / GPU 仓库（配置为 RHEL x86_64 源）仅提供 x86_64 架构的 RPM 包（如 `intel-basekit-2025.3.2-19.x86_64`、`intel-opencl-...x86_64`），yum 在 aarch64 上无法安装这些包，报"does not have a compatible architecture"。

### 与 PR 变更的关联
**PR 变更直接触发了此失败。** 原因有二：

1. **meta.yml 缺少 `arch` 约束**：PR 新增的 `meta.yml` 条目 `2024.2.0-oe2403sp4` 未指定 `arch` 字段。对比已有的 `2024.2.0-oe2403lts` 条目明确设置了 `arch: x86_64`，新条目缺少该约束导致 CI 调度器将此镜像同时派发到 aarch64 runner 上构建。

2. **Dockerfile 本身仅支持 x86_64**：Intel oneAPI Basekit 的 RPM 仓库（`yum.repos.intel.com`）和 Intel GPU 仓库（`repositories.intel.com/gpu/rhel/`）均为 RHEL x86_64 源，不提供 aarch64 包。该 Dockerfile 在 aarch64 上从原理上无法构建成功。

## 修复方向

### 方向 1（置信度: 高）
在 `meta.yml` 的 `2024.2.0-oe2403sp4` 条目中补充 `arch: x86_64`，与已有的 `2024.2.0-oe2403lts` 条目保持一致，使 CI 仅调度 x86_64 runner 构建该镜像。

## 需要进一步确认的点
- 确认 `meta.yml` 中已有的 `2024.2.0-oe2403lts` 条目（含 `arch: x86_64`）确实只在 x86_64 runner 上构建成功，以验证补充 `arch: x86_64` 后新条目能正常通过。
- 确认 Intel 仓库未来是否计划提供 aarch64 包——若有，则长期方案可能不同，但目前应保持与已有 `24.03-lts` 变体一致的架构约束。
