# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（变体）
- 新模式标题: -
- 新模式症状关键词: -

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具 (`eulerpublisher`) 在扫描 PR 变更文件时，将根级 `README.md` 纳入路径校验，但因 `README.md` 不匹配镜像目录的路径模式（如 `{category}/{image}/{version}/{os-version}/Dockerfile`），校验返回 `FAILURE`。

### 与 PR 变更的关联
PR 仅修改了两个根级文档文件（`README.md`、`README.en.md`），更新了镜像 Tags 列表（新增 25.09、24.03-lts-sp3、24.03-lts-sp2 条目，将 latest 标签从 sp2 改为 sp3）。这些是纯文档变更，不涉及任何 Dockerfile、meta.yml 或镜像构建逻辑。CI 工具将根级 README.md 误纳入 appstore 镜像路径校验流程，属于 CI 工具逻辑缺陷（infra-error），与 PR 改动本身无关。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher` 的 appstore 预检阶段需要将根级仓库文档（`README.md`、`README.en.md`）加入白名单，跳过路径格式校验。根级 README 不属于镜像目录层级，不应被镜像路径规范检查覆盖。

### 方向 2（置信度: 低）
PR 新增了 `25.09`、`24.03-lts-sp3` 等 tag 条目，但对应的 Docker 镜像目录可能尚未创建（PR 仅改了 README），appstore 规范检查要求 README 中列出的 tag 必须有对应的镜像构建目录。若此推断成立，则 PR 需要同步创建对应版本的 Docker 镜像目录文件（Dockerfile、meta.yml 等）。但从日志看 CI 报的是"Path Error"而非"missing directory"或"inconsistent"，方向 1 更符合错误特征。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中路径校验逻辑的具体实现——确认其是否对所有变更文件无条件执行 `{image-version}/{os-version}/Dockerfile` 格式校验，以及是否有根级文件的白名单机制。
- README 中新增的 tag URL（`openEuler-25.09`、`openEuler-24.03-LTS-SP3`）对应的 Docker 镜像在 `repo.openeuler.org` 是否确实存在，这是 CI 可能需要检查但当前并未检查的内容。

## 修复验证要求
（不适用——infra-error 无需 code-fixer 修改 PR 代码）
