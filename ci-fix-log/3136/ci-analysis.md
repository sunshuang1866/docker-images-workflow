# CI 失败分析报告

## 基本信息
- PR: #3136 — chore(oneapi-runtime): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构不匹配
- 新模式症状关键词: does not have a compatible architecture, x86_64 on aarch64, oneAPI, yum install

## 根因分析

### 直接错误
```
#11 76.67 Error: 
#11 76.67  Problem 1: cannot install the best candidate for the job
#11 76.67   - package intel-oneapi-runtime-ccl-2022.1.0-142.x86_64 from oneAPI does not have a compatible architecture
#11 76.67   - nothing provides intel-oneapi-runtime-mpi needed by intel-oneapi-runtime-ccl-2022.1.0-142.x86_64 from oneAPI
#11 76.67  Problem 2: cannot install the best candidate for the job
#11 76.67   - package intel-oneapi-runtime-compilers-2024-2024.2.2-78.x86_64 from oneAPI does not have a compatible architecture
...（共 18 个 Problem，所有包均为 .x86_64，在 aarch64 上不可安装）
```

### 根因定位
- 失败位置: `AI/oneapi-runtime/2024.2.0/24.03-lts-sp4/Dockerfile:30`
- 失败原因: 新增 Dockerfile 对应的 `meta.yml` 条目未设置 `arch: x86_64`，导致 CI 在 aarch64 节点上也尝试构建该镜像。而 Intel oneAPI 仓库和 Intel GPU 驱动仓库均只提供 x86_64 架构的 RPM 包，在 aarch64 上 yum 无法安装，报 "does not have a compatible architecture"。

### 与 PR 变更的关联

**PR 直接导致此失败。** PR 在 `AI/oneapi-runtime/meta.yml` 中新增了 `2024.2.0-oe2403sp4` 条目，但遗漏了 `arch: x86_64` 字段。对比同文件中已有的条目：

```yaml
2024.2.0-oe2403lts:
  path: 2024.2.0/24.03-lts/Dockerfile
  arch: x86_64          # <-- 已有条目限定了架构
2024.2.0-oe2403sp4:
  path: 2024.2.0/24.03-lts-sp4/Dockerfile
                         # <-- 新增条目缺少 arch 限制
```

CI 构建日志显示构建运行在 `ecs-build-docker-aarch64-01-sp (docker-build-aarch64)` 节点上，该节点是 aarch64 架构。由于 meta.yml 未限制架构，CI 尝试在 aarch64 上安装仅支持 x86_64 的 Intel oneAPI/GPGPU 包，导致失败。

Intel oneAPI 及 Intel GPU 驱动包本质上只发布 x86_64 架构版本（从其包名中的 `x86_64` 后缀和依赖 `ld-linux-x86-64.so.2` 等 x86_64 动态链接器可确认），无法在 aarch64/openEuler 上安装。

## 修复方向

### 方向 1（置信度: 高）
在 `AI/oneapi-runtime/meta.yml` 中为新增的 `2024.2.0-oe2403sp4` 条目添加 `arch: x86_64`，与已有的 `2024.2.0-oe2403lts` 条目保持一致，使 CI 仅对 x86_64 架构构建该镜像。

## 需要进一步确认的点
- 无需进一步确认，日志证据充分，根因明确。

