# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: README路径校验误报
- 新模式症状关键词: Path Error, expected path should be, README.md, appstore

## 根因分析

### 直接错误
```
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
```
以及：
```
2026-06-30 11:28:09,089-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
```

### 根因定位
- 失败位置: CI 的 appstore 发布规范预检工具 `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 规范检查工具对 PR 中变更的根目录 README 文件（`README.md`、`README.en.md`）执行路径校验时，要求文件路径为 `/README.md`。然而 `README.md` 文件本身即位于仓库根目录 `/README.md`，却仍被判定为 FAILURE。同时 `README.en.md`（英文版 README）也被要求匹配 `/README.md` 路径，但该文件是 repo 中已存在的独立英文文档。这表明 CI 校验工具存在路径规范化缺陷，未能正确处理仓库根目录级别的纯文档文件——无论是路径匹配逻辑（`README.md` 匹配自身却失败）还是对多语言变体文件（`README.en.md`）的支持均有问题。

### 与 PR 变更的关联
PR 变更**与 CI 失败无实质关联**。本次 PR 仅修改了 `README.md` 和 `README.en.md` 中的镜像 Tags 列表（更新 `24.03-lts-sp2` → `24.03-lts-sp3` 作为 latest、新增 `25.09`、拆分 sp3/sp2 条目），属于纯文档内容更新。CI 失败的原因是 appstore 规范检查工具对根目录文档文件的路径校验逻辑存在缺陷，而非 PR 内容有误。任何修改仓库根目录 README 文件的 PR 均会触发相同的误报。

## 修复方向

### 方向 1（置信度: 中）
CI 预检工具 `eulerpublisher/update/container/app/update.py` 中的路径校验逻辑需要修复：应将仓库根目录的 `README.md` 和 `README.en.md` 加入白名单/豁免列表，允许这些纯文档文件在 PR 中被修改而不触发 appstore 路径规范报错。此类文件不属于任何应用镜像的最小目录单元，不应参与镜像发布路径校验。

### 方向 2（置信度: 中）
CI 工具可能存在路径前缀归一化问题：`update.py:273` 在校验文件路径时，传入的路径可能是 `README.md`（无前导 `/`），而期望值定义为 `/README.md`（有前导 `/`），导致字符串精确匹配失败。需检查 diff 解析逻辑输出的路径格式与期望路径格式是否一致（均带或不带前导 `/`）。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 中 `specification errors` 的具体校验逻辑——是文件路径白名单匹配、正则匹配还是前缀匹配；
2. 校验工具中文件路径的获取方式（`git diff --name-only` 输出的路径格式 vs 校验规则中定义的路径格式）；
3. 该 CI 工具是否预期运行在此类只包含文档变更的 PR 上，还是本应在触发层被跳过；
4. `README.en.md` 的预期校验路径——是否应视为 `/README.md` 的等价文件还是应有独立的 `/README.en.md` 校验规则；
5. 上游 eulerpublisher 仓库中该工具的近期更新记录，确认是否为新引入的回归问题。
