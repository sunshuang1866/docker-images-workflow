# CI 失败分析报告

## 基本信息
- PR: #3201 — 增加maca-sdk镜像
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: COPR仓库下载中断
- 新模式症状关键词: Curl error (18), Transferred a partial file, No more mirrors to try, COPR, eur.openeuler.openatom.cn, dnf install

## 根因分析

### 直接错误
```
#10 421.4 [MIRROR] mccl-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mccl-3.7.0.38-1.aarch64.rpm [transfer closed with 43044896 bytes remaining to read]
#10 803.6 [MIRROR] mcblas-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mcblas-3.7.0.38-1.aarch64.rpm [transfer closed with 27524468 bytes remaining to read]
#10 836.8 [MIRROR] mcblaslt-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mcblaslt-3.7.0.38-1.aarch64.rpm [transfer closed with 399936528 bytes remaining to read]
#10 956.6 [MIRROR] mccl-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mccl-3.7.0.38-1.aarch64.rpm [transfer closed with 34752742 bytes remaining to read]
#10 956.6 [FAILED] mccl-3.7.0.38-1.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#10 956.6 Error: Error downloading packages:
```

### 根因定位
- 失败位置: `AI/maca-sdk/3.7/24.03-lts-sp3/Dockerfile:13-21`（`dnf install -y --allowerasing maca-sdk-aarch64` 步骤）
- 失败原因: CI 构建环境与 COPR 仓库 `eur.openeuler.openatom.cn` 之间的网络连接极不稳定——下载速度仅约 24 kB/s，大文件（45MB~849MB）在传输途中连接被远端关闭（Curl error 18），尽管 dnf 已配置 `retries=10`、`timeout=600`，所有重试均以相同方式失败，最终 58 个 RPM 包中多个大文件下载失败导致 `dnf install` 退出码 1。

### 与 PR 变更的关联
**与 PR 代码改动无直接关系。** 该 PR 新增的 Dockerfile、EUR.repo、meta.yml 和 image-list.yml 条目本身语法正确，`dnf makecache` 阶段也成功创建了元数据缓存并解析了 58 个包的依赖关系。失败发生在从第三方 COPR 仓库实际下载 RPM 包阶段，属于 CI 基础设施与外部仓库之间的网络可靠性问题。

需要注意的一个潜在次要问题：`EUR.repo` 中 baseurl 路径为 `openeuler-24.03_LTS_SP2-$basearch`，而 Dockerfile 基础镜像是 `openeuler/openeuler:24.03-lts-sp3`（SP2 vs SP3 版本不一致），不过该差异不影响下载行为（元数据缓存和包列表均正确获取，仅实际传输阶段失败）。

## 修复方向

### 方向 1（置信度: 中）
**更换 RPM 包获取方式，绕过不可靠的 COPR 仓库。** 将 RPM 包预下载到本地并随 Dockerfile 目录一起提交到仓库（类似模式06中 env2yaml 二进制的处理方式），或在 Dockerfile 中改为从更可靠的内网/镜像源获取。需确认是否有 openEuler 官方镜像站或华为云镜像站托管了 maca-sdk RPM 包。

### 方向 2（置信度: 低）
**降低单次 RUN 的包下载量，拆分 dnf install 为多次小批量安装。** 将 `maca-sdk-aarch64` 的 58 个依赖拆分为多个 `dnf install` 调用，优先安装小文件包，大文件包单独安装并增加重试次数。这不能解决根因（网络不可靠），但可能提高成功率。

### 方向 3（置信度: 低）
**联系 maca-sdk COPR 仓库维护方改善服务端连接稳定性。** 当前仓库下载速度极低（24 kB/s），远端频繁主动关闭连接。如果 COPR 服务端有速率限制或连接数限制，协调调整可从根本上解决。

## 需要进一步确认的点
1. `eur.openeuler.openatom.cn` COPR 仓库在 CI 构建节点的网络可达性和带宽情况——需要确认是临时性网络波动还是持续性问题
2. maca-sdk 3.7.0.38 是否有其他可用的 RPM 镜像源（如 openEuler 官方仓库、华为云镜像站等）
3. SP2 vs SP3 的 baseurl 不一致是否需要修正——当前 `EUR.repo` 引用 SP2 路径，但基础镜像是 SP3，需确认 SP2 的 RPM 包是否与 SP3 系统兼容，或是否应切换到 SP3 对应的 repo 路径
4. 日志中 RUN 命令带有 `echo -e "minrate=100\ntimeout=600\nretries=10\nmax_parallel_downloads=4" >> /etc/dnf/dnf.conf` 前缀，但 PR diff 中并不包含此行——需确认是否为 CI 编排层注入或已有后续补丁

## 修复验证要求
- 确认 maca-sdk RPM 包有可用的备用下载源后再修改 Dockerfile，不能假设网络问题会自动恢复
- 如更换下载源，验证新源在 CI 构建环境中可达且下载速度稳定（尤其是 aarch64 架构下的大文件包如 mcflashattn 849MB、mcblaslt 400MB）
