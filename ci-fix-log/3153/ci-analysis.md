# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根级文档误触appstore校验
- 新模式症状关键词: Path Error, expected path should be, README.md, appstore, eulerpublisher/update/container/app/update.py

## 根因分析

### 直接错误
```
|  README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md    | [Path Error] The expected path should be /README.md |   FAILURE    |
2026-07-12 15:33:13,075-[...]/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py`（CI appstore 发布规范校验工具）
- 失败原因: CI 的 appstore 发布规范校验工具检测到 PR 变更了根目录下的 `README.md` 和 `README.en.md`，随后对这些根级文档文件执行了路径格式校验。该校验预期文件应遵循 `{category}/{image}/{version}/{os-version}/` 的多级目录结构（如 `AI/xxx/x.x.x/24.03-lts-sp4/Dockerfile`），而根级文件不匹配任何应用镜像路径模板，导致校验以 [Path Error] 失败。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 中"可用镜像 Tags"列表的两行内容（新增 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2 三个标签，调整 latest 指向），属于纯文档变更。PR 的代码变更本身无误，失败源于 CI 基础设施的 appstore 路径校验工具对根级文档文件进行了不应有的路径格式检查——该检查本应仅针对应用镜像的子目录（`Bigdata/`、`AI/` 等场景目录下的 Dockerfile/meta.yml 等）。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 发布规范校验工具（`eulerpublisher/update/container/app/update.py`）在扫描变更文件时，未排除根目录下的纯文档文件（`README.md`、`README.en.md` 等），导致文档类 PR 被误判为"不符合 appstore 路径规范"。应在校验逻辑中对根级非应用镜像文件进行白名单豁免（如以路径前缀或文件扩展名过滤），使文档变更不触发 appstore 目录结构校验。

### 方向 2（置信度: 低）
校验工具 `update.py:273` 附近的路径匹配逻辑可能对根级文件的"期望路径"计算有误，`README.md` 的实际路径与期望路径 `/README.md` 若存在前导 `/`、相对路径 vs 绝对路径的比对差异，也会导致误报。需检查 `update.py` 中路径正规化（normalization）逻辑是否对根级文件做了正确处理。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中文件变更检测与路径校验的具体逻辑（特别是 `Difference` 列表如何生成、哪些文件类型被纳入 appstore 规范检查）。
2. 该 CI 校验工具是否需要扫描仓库根级 README 文件——如果根级文件本不应纳入 appstore 校验范围，则需确认过滤逻辑缺失是既定行为还是回归缺陷。
3. 是否有其他纯文档类 PR 也曾触发相同错误（可帮助判断是否为已知 CI 工具缺陷）。

## 修复验证要求
此问题为 CI 基础设施（appstore 校验工具）的行为缺陷，不涉及 Dockerfile 或应用镜像构建代码的修改。修复后需以 root 级文档变更的 PR（如仅修改 README.md）重新触发 CI，确认 appstore 路径校验不再误报。
