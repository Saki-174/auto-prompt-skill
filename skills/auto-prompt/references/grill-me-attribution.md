# 澄清机制来源

核验日期：2026-10-04。来源仓库：mattpocock/skills。
固定提交：`24fe0ef7737efae15c87225755e9f6f5965e4888`。

- [grill-me 入口](https://github.com/mattpocock/skills/blob/24fe0ef7737efae15c87225755e9f6f5965e4888/skills/productivity/grill-me/SKILL.md) 当前仅委托给 grilling。
- [grilling 机制](https://github.com/mattpocock/skills/blob/24fe0ef7737efae15c87225755e9f6f5965e4888/skills/productivity/grilling/SKILL.md) 使用决策依赖、按前置条件分轮提问、推荐答案及回答后重新评估。
- [MIT 许可](https://github.com/mattpocock/skills/blob/24fe0ef7737efae15c87225755e9f6f5965e4888/LICENSE)。

本项目对需求澄清机制做局部改编：每轮通常一题、最多两题，只问影响目标/范围/交付/验收的歧义；允许未知与先出草案；提供当前宿主工具探测和文字回退。未复制上游整套技能，也不要求安装该仓库。

上游入口依赖宿主 Skill 调用能力，grilling 还要求子代理事实探索；这两个机制不作为本项目依赖。未引入外部模型、服务、包管理器或账号授权。复用部分保留以下上游许可；其余项目代码仍按本项目 ISC 许可。

MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
