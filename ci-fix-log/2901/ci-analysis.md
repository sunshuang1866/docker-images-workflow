# CI 失败分析报告

## 基本信息
- PR: #2901 — chore(kselftests-virtme): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式06
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#14 [9/9] COPY entrypoint.sh tap2json.py /
#14 ERROR: failed to calculate checksum of ref zduodss111m97onxnon4gcv9r::gi2gwp2l5udptclkwg9r8l1gg: "/entrypoint.sh": not found
------
 > [9/9] COPY entrypoint.sh tap2json.py /
------
Dockerfile:99
--------------------
  97 |     ENV GCC_COLORS error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01
  98 |     
  99 | >>> COPY entrypoint.sh tap2json.py /
 100 |     
 101 |     ENTRYPOINT ["/entrypoint.sh"]
--------------------
ERROR: failed to solve: failed to compute cache key: failed to calculate checksum of ref zduodss111m97onxnon4gcv9r::gi2gwp2l5udptclkwg9r8l1gg: "/entrypoint.sh": not found
```

### 根因定位
- 失败位置: `Others/kselftests-virtme/1.27/24.03-lts-sp4/Dockerfile:99`
- 失败原因: 新增的 Dockerfile 中 `COPY entrypoint.sh tap2json.py /` 引用了目录下不存在的文件。PR 仅提交了 Dockerfile 本身，未将 `entrypoint.sh` 和 `tap2json.py` 两个辅助脚本复制到新版本目录中（`1.27/24.03-lts-sp4/`），导致 Docker BuildKit 在构建上下文中找不到这两个文件，计算 checksum 失败。

### 与 PR 变更的关联
PR 新增了 `Others/kselftests-virtme/1.27/24.03-lts-sp4/Dockerfile`（Dockerfile 第 99 行含 `COPY entrypoint.sh tap2json.py /`），但 PR diff 中未包含 `entrypoint.sh` 和 `tap2json.py` 文件。这两个脚本文件存在于同镜像的其他版本目录（如 `1.27/22.03-lts-sp4/`）中，需要被复制到新目录 `1.27/24.03-lts-sp4/` 下。此问题完全由本次 PR 的遗漏引起。

## 修复方向

### 方向 1（置信度: 高）
从已存在的同级目录 `Others/kselftests-virtme/1.27/22.03-lts-sp4/` 中复制 `entrypoint.sh` 和 `tap2json.py` 到新目录 `Others/kselftests-virtme/1.27/24.03-lts-sp4/`，确保 Dockerfile 第 99 行 `COPY` 指令能正确找到这两个文件。同时修正 README.md 和 doc/image-info.yml 中 1.27-oe2403sp4 标签的描述文字，将"openEuler 22.03-LTS-sp4"改为"openEuler 24.03-LTS-sp4"。

## 需要进一步确认的点
- 确认 `Others/kselftests-virtme/1.27/22.03-lts-sp4/entrypoint.sh` 和 `tap2json.py` 是否需要为新版本做适配修改（通常情况下无需修改，直接复制即可）
- 确认 README.md 和 doc/image-info.yml 中 `1.27-oe2403sp4` 行描述的"22.03"是否为笔误（日志中该行明确写的是"Virtme-ng 1.27 on openEuler 22.03-LTS-sp4"但应描述 24.03）

## 修复验证要求
修复后确保新目录下包含以下文件，且 Docker 构建可成功完成 COPY 步骤：
- `Others/kselftests-virtme/1.27/24.03-lts-sp4/Dockerfile`
- `Others/kselftests-virtme/1.27/24.03-lts-sp4/entrypoint.sh`
- `Others/kselftests-virtme/1.27/24.03-lts-sp4/tap2json.py`
