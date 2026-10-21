# 化学书房主页：维护说明

主页目标：`https://github.com/FelixJiashengFu`。

本目录对应公开同名仓库 `FelixJiashengFu/FelixJiashengFu` 的默认 `main` 分支，根目录的 `README.md` 显示在个人主页。

## 已准备的内容

- 书卷风格的中文 / 英文横幅，苯环与展开的书本线稿。
- 四个可点击的化学项目入口，以及四个数学、物理学习库链接。仅链接已确认公开的仓库。
- 深色和浅色各一套 SVG。横幅和项目卡片文字已转为路径，不依赖访客电脑上的中文字体。
- 使用 GitHub API 生成的真实贡献统计，以及 Platane/snk 生成的真实贡献贪吃蛇动画。初始文件已经生成，发布后无需等待首个工作流才有图。
- 工作流每天 10:17 UTC 自动更新两套贡献图和统计卡；也支持在 Actions 页手动运行。GitHub 的定时任务可能延迟，长期没有活动的公开仓库可能被 GitHub 暂停定时运行。

## 更新内容

修改介绍与仓库链接：编辑 `README.md`。修改自动生成的统计卡：编辑 `scripts/update-stats.py`。修改贪吃蛇颜色：编辑 `.github/workflows/refresh-profile.yml` 的 `color_snake` 和五个 `color_dots` 值。

`scripts/build-artwork.py` 是横幅、项目卡和工具栏的可编辑生成源码；需要 macOS 自带的 Georgia、Arial、宋体字体与 Python `fonttools` 库，运行后会重新生成静态 SVG 和 README。日常自动更新只运行 `update-stats.py`，无需这些字体或第三方 Python 库。

工作流只使用 GitHub 自动提供的 `GITHUB_TOKEN`，无需添加个人密钥。它需要该仓库的 `contents: write` 权限来保存 `assets/` 中的新 SVG；没有发布包、修改其他仓库或发送消息的步骤。

如果更新失败，在仓库的 Actions 页查看 `Refresh the chemistry study` 的日志。现有图片仍会保留；修复后可用 Run workflow 重新生成。统计不包含任何私有仓库名称。

GitHub README 支持的排版由平台决定，页面外层、头像、系统贡献格和置顶项目区不能通过 README 自定义。本设计作用于个人主页的 README 展示区。手机上卡片和图像会按可用宽度缩小。

## 来源

- [GitHub：个人主页 README 规则](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme)
- [Platane/snk：贡献图贪吃蛇](https://github.com/Platane/snk)，动画由该项目生成，未将其源代码复制入本仓库。
- 统计来源：GitHub REST 公共用户资料与 GraphQL `contributionCalendar`。柱高为对应月份贡献数，首尾月份可能不完整；统计范围为 GitHub 返回的过去一年。卡片底部标注实际日期范围和刷新日期。
