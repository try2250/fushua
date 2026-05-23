# 小程序图标说明

## 缺失的图标文件

小程序需要以下图标文件（81x81像素，PNG格式）：

### TabBar图标
1. `practice.png` - 刷题图标（未选中，灰色）
2. `practice-active.png` - 刷题图标（选中，蓝色）
3. `assignment.png` - 作业图标（未选中，灰色）
4. `assignment-active.png` - 作业图标（选中，蓝色）
5. `mistake.png` - 错题本图标（未选中，灰色）
6. `mistake-active.png` - 错题本图标（选中，蓝色）
7. `profile.png` - 个人中心图标（未选中，灰色）
8. `profile-active.png` - 个人中心图标（选中，蓝色）

## 临时解决方案

由于我无法直接创建图片文件，你有两个选择：

### 方案1：使用文字图标（快速）
修改 `app.json`，使用文字代替图标：

```json
"tabBar": {
  "color": "#999999",
  "selectedColor": "#1890ff",
  "backgroundColor": "#ffffff",
  "borderStyle": "black",
  "list": [
    {
      "pagePath": "pages/tabbar/practice/practice",
      "text": "刷题"
    },
    {
      "pagePath": "pages/tabbar/assignments/assignments",
      "text": "作业"
    },
    {
      "pagePath": "pages/tabbar/mistakes/mistakes",
      "text": "错题本"
    },
    {
      "pagePath": "pages/tabbar/profile/profile",
      "text": "我的"
    }
  ]
}
```

### 方案2：创建简单图标（推荐）
1. 使用在线工具创建图标：https://www.iconfont.cn/
2. 或使用Photoshop/Figma创建81x81的PNG图标
3. 保存到 `miniprogram/images/` 目录

## 图标设计规范
- 尺寸：81x81像素
- 格式：PNG，支持透明背景
- 未选中状态：灰色 #999999
- 选中状态：蓝色 #1890ff
- 风格：简洁、扁平化

## 快速图标资源
可以从这些网站下载免费图标：
- https://www.iconfont.cn/ (阿里巴巴矢量图标库)
- https://www.flaticon.com/
- https://icons8.com/

搜索关键词：
- 刷题：book, study, practice
- 作业：homework, assignment, task
- 错题本：error, mistake, notebook
- 个人中心：user, profile, person
