# 修复摘要

## 修复的问题
为4个缺失Copyright+SPDX声明的文件添加版权头，并修复Dockerfile中`make -j$nproc`的Shell语法错误。

## 修改的文件
- `Database/etcd/3.8.0-alpha.0/24.03-lts-sp3/Dockerfile`: 添加Copyright+SPDX头；修复`make -j$nproc`为`make -j$(nproc)`
- `Database/etcd/README.md`: 添加Copyright+SPDX头
- `Database/etcd/doc/image-info.yml`: 添加Copyright+SPDX头
- `Database/etcd/meta.yml`: 添加Copyright+SPDX头

## 修复逻辑
1. **模式17（Copyright缺失）**：CI的`check_package_license`检查要求文件包含Copyright和SPDX-License-Identifier声明。参照项目中neo4j等已有Dockerfile的版权头格式（`# Copyright (C) YYYY Holder` / `# SPDX-License-Identifier: SPDX-ID`），为4个文件添加了统一的版权声明头。SPDX标识使用`Apache-2.0`，与etcd项目的许可证一致。
2. **模式13（Shell语法错误）**：`make -j$nproc`中`$nproc`在Shell中会展开为空字符串，导致`make -j`（无限制并行）。修正为`make -j$(nproc)`使用命令替换语法，正确获取CPU核心数。

## 潜在风险
无。修改仅涉及添加版权声明头和一个已确认的Shell语法修正，不改变任何业务逻辑或构建行为。