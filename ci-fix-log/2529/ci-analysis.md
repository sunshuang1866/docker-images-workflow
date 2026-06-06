# CI 失败分析报告

## 基本信息
- PR: #2529 — 【自动升级】milvus容器镜像升级至3.0-beta版本.
- 失败类型: lint-error（Copyright/SPDX 声明缺失）
- 置信度: 中
- 知识库匹配: 模式17
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-06 00:40:02,608 [WARNING] : the copyright in repo is not pass, notice:
  openeuler-docker-images/Database/milvus/README.md、openeuler-docker-images/Database/milvus/doc/image-info.yml
  文件Copyright校验不通过,
  openeuler-docker-images/Database/milvus/meta.yml、openeuler-docker-images/Database/milvus/3.0-beta/24.03-lts-sp3/Dockerfile
  文件缺失Copyright声明,
  Copyright path：缺少项目级Copyright声明文件

check result: ACL=[{"name": "check_sca", "result": 0}, {"name": "check_package_license", "result": 1}]
```

### 根因定位
- 失败位置: 4 个文件均缺失 Copyright 和 SPDX-License-Identifier 声明头
  - `Database/milvus/3.0-beta/24.03-lts-sp3/Dockerfile`（新增文件）
  - `Database/milvus/README.md`（修改文件，新增行无 Copyright）
  - `Database/milvus/doc/image-info.yml`（修改文件，新增行无 Copyright）
  - `Database/milvus/meta.yml`（修改文件，新增行无 Copyright）
- 失败原因: PR 新增/修改的 4 个文件均未包含 Copyright 和 SPDX-License-Identifier 声明头，CI `check_package_license` 检查返回 `result: 1`（未通过）。

### 与 PR 变更的关联
PR 为 milvus 3.0-beta 新增了完整的 Dockerfile，并对 README.md、image-info.yml、meta.yml 各新增了一行条目。所有 4 个文件均未按 openEuler 容器镜像仓规范添加 Copyright 和 SPDX 头，直接触发了 license 检查失败。

## 修复方向

### 方向 1（置信度: 高）
为 4 个受影响文件添加 Copyright 和 SPDX-License-Identifier 声明头：

- `Dockerfile`（新增文件）顶部添加：
  ```dockerfile
  # Copyright (c) Huawei Technologies Co., Ltd. 2024-2024. All rights reserved.
  # SPDX-License-Identifier: MulanPSL-2.0
  ```

- `README.md`（修改文件）新增的表格行前后添加 Copyright 注释。

- `image-info.yml`（修改文件）新增的表格行前后添加 Copyright 注释。

- `meta.yml`（修改文件）新增的条目前后添加 Copyright 注释。

### 方向 2（置信度: 低）
下游 x86-64 构建 job（#1386）和 aarch64 构建 job（#1361）的详细日志未提供。Copyright 修复后若构建仍失败，需排查 Dockerfile 本身的构建逻辑（如 `golang.google.cn` 下载连通性、`rustup.rs` 网络可达性、milvus `make build-cpp` / `make build-go` 编译错误等）。

## 需要进一步确认的点
1. **下游构建 job 日志缺失** — x86-64（#1386）和 aarch64（#1361）的实际 Docker 构建日志未在本次分析中提供。无法确认 Copyright 问题是否就是导致下游 job 标记为 FAILURE 的唯一原因，还是仅触发 WARNING 且下游存在独立的编译/构建失败。
2. **`check_package_license` 的 `result: 1` 语义** — 需确认该返回码对应的具体行为：是仅 WARNING 不阻断流水线，还是直接导致流水线标记失败。
3. **历史知识库中存在自引用** — 模式17 的历史案例中已包含了 PR #2529 本身，表明可能已有复用分析结论，需确认该 PR 是否正在被重复处理。
