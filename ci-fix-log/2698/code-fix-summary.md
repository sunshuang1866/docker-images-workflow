# 修复摘要

## 修复的问题
CI 基础设施问题：`eulerpublisher` 工具的 `parse_image_prefix` 函数从 Jenkins workspace（upstream master 分支）读取 `Database/image-list.yml`，而非 PR 克隆仓库，导致找不到 PR 新增的 `percona: percona` 条目，对根级文件 `Database/percona/README.md` 抛出 ValueError。PR 代码本身及 `image-list.yml` 变更均正确无误，无需修改源代码。

## 修改的文件
无

## 修复逻辑
此为 infra-error，非代码缺陷。`parse_image_prefix` 在处理版本子目录下的文件（如 `Database/percona/8.4.8/24.03-lts-sp3/Dockerfile`）时可通过路径推断镜像根目录，但处理根级文件（如 `Database/percona/README.md`）时必须依赖 `image-list.yml` 查找。CI 工作流从 workspace（master 分支）读取该文件，master 分支尚未合并此 PR，因此不包含 `percona` 条目。PR 在 `Database/image-list.yml` 中新增的 `percona: percona` 条目本身正确，CI 工具需从 PR 克隆仓库读取 `image-list.yml`，或将根级文件的校验放宽为警告。

## 潜在风险
无。未修改任何源代码。