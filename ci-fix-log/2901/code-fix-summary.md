# 修复摘要

## 修复的问题
Dockerfile 第 99 行 `COPY entrypoint.sh tap2json.py /` 因构建上下文缺少这两个辅助脚本文件而失败；同时修复 README.md 和 doc/image-info.yml 中 1.27-oe2403sp4 标签的版本描述笔误。

## 修改的文件
- `Others/kselftests-virtme/1.27/24.03-lts-sp4/entrypoint.sh`: 从同级目录 `1.27/22.03-lts-sp4/` 复制，提供 Docker 镜像入口脚本
- `Others/kselftests-virtme/1.27/24.03-lts-sp4/tap2json.py`: 从同级目录 `1.27/22.03-lts-sp4/` 复制，提供 TAP 转 JSON 工具
- `Others/kselftests-virtme/README.md`: `1.27-oe2403sp4` 行描述从 "openEuler 22.03-LTS-sp4" 修正为 "openEuler 24.03-LTS-sp4"
- `Others/kselftests-virtme/doc/image-info.yml`: `1.27-oe2403sp4` 行描述从 "openEuler 22.03-LTS-sp4" 修正为 "openEuler 24.03-LTS-sp4"

## 修复逻辑
CI 失败的直接原因是 Docker BuildKit 在计算 COPY 指令的 checksum 时找不到 `entrypoint.sh` 和 `tap2json.py` 两个文件。PR 仅提交了 Dockerfile 本身，遗漏了这两个辅助脚本。由于 `1.27/22.03-lts-sp4/` 目录中已有相同功能的文件且内容无需为新版本适配，直接从该目录复制即可满足构建要求。

README.md 和 doc/image-info.yml 中 `1.27-oe2403sp4` 标签的描述写成了 "22.03-LTS-sp4"，属于 PR 作者从 `22.03` 版本复制模板时未更新版本号的笔误，已修正为 "24.03-LTS-sp4"。

## 潜在风险
- `entrypoint.sh` 和 `tap2json.py` 的内容与原 `22.03-lts-sp4` 版本完全相同，无适配风险
- 两处描述修正仅涉及文档展示文字，不影响构建或运行逻辑