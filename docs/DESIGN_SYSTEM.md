# 天眼寻珍·苍穹 - UI/UX 设计系统

## 1. 设计系统概览

### 设计原则
- **专业可信**: 适合政府、研究机构使用的严谨界面
- **数据可视化优先**: 地图和图表是核心，界面为其服务
- **效率至上**: 减少操作步骤，快速完成分析任务
- **科技感**: 现代化的视觉语言，体现技术先进性

---

## 2. 色彩系统

### 主色调（Primary）
```css
/* 农业绿 - 主品牌色 */
--primary-50: #f0fdf4;
--primary-100: #dcfce7;
--primary-200: #bbf7d0;
--primary-300: #86efac;
--primary-400: #4ade80;
--primary-500: #22c55e;  /* 主色 */
--primary-600: #16a34a;
--primary-700: #15803d;
--primary-800: #166534;
--primary-900: #14532d;
```

### 次要色（Secondary）
```css
/* 科技蓝 - 辅助色 */
--secondary-50: #eff6ff;
--secondary-100: #dbeafe;
--secondary-200: #bfdbfe;
--secondary-300: #93c5fd;
--secondary-400: #60a5fa;
--secondary-500: #3b82f6;  /* 次要色 */
--secondary-600: #2563eb;
--secondary-700: #1d4ed8;
--secondary-800: #1e40af;
--secondary-900: #1e3a8a;
```

### 中性色（Neutral）
```css
/* 深色模式为主 */
--gray-50: #f9fafb;
--gray-100: #f3f4f6;
--gray-200: #e5e7eb;
--gray-300: #d1d5db;
--gray-400: #9ca3af;
--gray-500: #6b7280;
--gray-600: #4b5563;
--gray-700: #374151;
--gray-800: #1f2937;
--gray-900: #111827;
--gray-950: #030712;
```

### 语义色
```css
/* 成功 */
--success: #10b981;
--success-bg: #d1fae5;
--success-text: #065f46;

/* 警告 */
--warning: #f59e0b;
--warning-bg: #fef3c7;
--warning-text: #92400e;

/* 错误 */
--error: #ef4444;
--error-bg: #fee2e2;
--error-text: #991b1b;

/* 信息 */
--info: #3b82f6;
--info-bg: #dbeafe;
--info-text: #1e40af;
```

### 背景色方案
```css
/* 深色主题（推荐） */
--bg-primary: #0f172a;      /* 主背景 - slate-900 */
--bg-secondary: #1e293b;    /* 次要背景 - slate-800 */
--bg-tertiary: #334155;     /* 第三层背景 - slate-700 */
--bg-card: #1e293b;         /* 卡片背景 */
--bg-hover: #334155;        /* 悬停背景 */

/* 浅色主题（可选） */
--bg-light-primary: #ffffff;
--bg-light-secondary: #f8fafc;
--bg-light-tertiary: #f1f5f9;
```

### 应用示例
```css
/* 主要操作按钮 */
.btn-primary {
  background: var(--primary-600);
  color: white;
}

/* 次要操作按钮 */
.btn-secondary {
  background: var(--secondary-600);
  color: white;
}

/* 卡片 */
.card {
  background: var(--bg-card);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* 地图控件 */
.map-control {
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

---

## 3. 字体系统

### 字体家族
```css
/* 主字体 - 中文优先 */
--font-sans: "PingFang SC", "Microsoft YaHei", "Segoe UI", "Roboto", 
             -apple-system, BlinkMacSystemFont, sans-serif;

/* 等宽字体 - 用于数据、代码 */
--font-mono: "SF Mono", "Monaco", "Consolas", "Liberation Mono", 
             "Courier New", monospace;

/* 数字字体 - 用于大数字展示 */
--font-numeric: "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
```

### 字号体系
```css
/* 移动端基准: 14px, 桌面端基准: 16px */

/* 超大标题 - 页面主标题 */
--text-5xl: 3rem;      /* 48px */
--text-4xl: 2.25rem;   /* 36px */
--text-3xl: 1.875rem;  /* 30px */

/* 标题 */
--text-2xl: 1.5rem;    /* 24px */
--text-xl: 1.25rem;    /* 20px */
--text-lg: 1.125rem;   /* 18px */

/* 正文 */
--text-base: 1rem;     /* 16px */
--text-sm: 0.875rem;   /* 14px */
--text-xs: 0.75rem;    /* 12px */

/* 微小文字 - 标签、提示 */
--text-2xs: 0.625rem;  /* 10px */
```

### 字重
```css
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### 行高
```css
--leading-tight: 1.25;   /* 标题 */
--leading-normal: 1.5;   /* 正文 */
--leading-relaxed: 1.75; /* 长文本 */
```

### 应用示例
```css
/* 页面主标题 */
h1 {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  color: #f8fafc; /* slate-50 */
}

/* 卡片标题 */
h2 {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: #e2e8f0; /* slate-200 */
}

/* 正文 */
p {
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  color: #cbd5e1; /* slate-300 */
}

/* 数据标签 */
.data-label {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: #94a3b8; /* slate-400 */
}

/* 大数字展示 */
.metric-value {
  font-family: var(--font-numeric);
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  line-height: 1;
}
```

---

## 4. 间距系统

### 间距标尺（基于 4px）
```css
--space-0: 0;
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-5: 1.25rem;  /* 20px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
--space-10: 2.5rem;  /* 40px */
--space-12: 3rem;    /* 48px */
--space-16: 4rem;    /* 64px */
--space-20: 5rem;    /* 80px */
```

### 应用规则
```css
/* 卡片内边距 */
.card { padding: var(--space-6); }

/* 卡片之间间距 */
.card + .card { margin-top: var(--space-4); }

/* 表单字段间距 */
.form-field + .form-field { margin-top: var(--space-4); }

/* 按钮内边距 */
.btn { padding: var(--space-3) var(--space-6); }

/* 章节间距 */
section + section { margin-top: var(--space-12); }
```

---

## 5. 圆角系统

```css
--radius-sm: 0.25rem;   /* 4px - 小元素、标签 */
--radius-md: 0.5rem;    /* 8px - 按钮、输入框 */
--radius-lg: 0.75rem;   /* 12px - 卡片 */
--radius-xl: 1rem;      /* 16px - 模态框 */
--radius-2xl: 1.5rem;   /* 24px - 大卡片 */
--radius-full: 9999px;  /* 圆形 - 头像、徽章 */
```

---

## 6. 阴影系统

```css
/* 微阴影 - 按钮、小卡片 */
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);

/* 标准阴影 - 卡片 */
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
             0 2px 4px -1px rgba(0, 0, 0, 0.06);

/* 大阴影 - 浮动面板 */
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1),
             0 4px 6px -2px rgba(0, 0, 0, 0.05);

/* 特大阴影 - 模态框 */
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1),
             0 10px 10px -5px rgba(0, 0, 0, 0.04);

/* 发光效果 - 聚焦状态 */
--shadow-focus: 0 0 0 3px rgba(34, 197, 94, 0.5); /* primary color */
```

---

## 7. 动画系统

### 过渡时长
```css
--duration-fast: 150ms;     /* 快速 - hover */
--duration-normal: 250ms;   /* 标准 - 展开/收起 */
--duration-slow: 350ms;     /* 慢速 - 复杂动画 */
```

### 缓动函数
```css
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

### 应用示例
```css
/* 按钮悬停 */
.btn {
  transition: all var(--duration-fast) var(--ease-out);
}

/* 下拉菜单 */
.dropdown {
  transition: opacity var(--duration-normal) var(--ease-in-out),
              transform var(--duration-normal) var(--ease-in-out);
}

/* 模态框 */
.modal {
  transition: opacity var(--duration-slow) var(--ease-out);
}
```

---

## 8. Z-Index 层级

```css
--z-base: 0;          /* 基础层 */
--z-dropdown: 10;     /* 下拉菜单 */
--z-sticky: 20;       /* 粘性元素 */
--z-fixed: 30;        /* 固定元素 - 顶部导航 */
--z-modal-backdrop: 40; /* 模态框背景 */
--z-modal: 50;        /* 模态框 */
--z-popover: 60;      /* 弹出提示 */
--z-tooltip: 70;      /* 工具提示 */
--z-notification: 80; /* 通知 */
```

---

## 9. 布局规范

### 容器最大宽度
```css
--container-sm: 640px;
--container-md: 768px;
--container-lg: 1024px;
--container-xl: 1280px;
--container-2xl: 1536px;
```

### 栅格系统
- 使用 CSS Grid 或 Flexbox
- 基础栅格: 12列
- 间隙: 24px（桌面）/ 16px（移动）

---

## 10. 组件设计规范

### 按钮
```css
/* 主要按钮 */
.btn-primary {
  background: var(--primary-600);
  color: white;
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-md);
  font-weight: var(--font-medium);
  transition: all var(--duration-fast) var(--ease-out);
  cursor: pointer;
}

.btn-primary:hover {
  background: var(--primary-700);
  box-shadow: var(--shadow-md);
}

.btn-primary:focus {
  outline: none;
  box-shadow: var(--shadow-focus);
}

/* 次要按钮 */
.btn-secondary {
  background: transparent;
  color: var(--primary-500);
  border: 1px solid var(--primary-500);
  /* 其他样式同上 */
}

/* 尺寸变体 */
.btn-sm { padding: var(--space-2) var(--space-4); font-size: var(--text-sm); }
.btn-md { padding: var(--space-3) var(--space-6); font-size: var(--text-base); }
.btn-lg { padding: var(--space-4) var(--space-8); font-size: var(--text-lg); }
```

### 输入框
```css
.input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: var(--bg-secondary);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-md);
  color: #e2e8f0;
  font-size: var(--text-base);
  transition: all var(--duration-fast) var(--ease-out);
}

.input:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: var(--shadow-focus);
}

.input::placeholder {
  color: var(--gray-500);
}
```

### 卡片
```css
.card {
  background: var(--bg-card);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-md);
  transition: all var(--duration-fast) var(--ease-out);
}

.card:hover {
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: var(--shadow-lg);
}
```

### 徽章
```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-3);
  background: var(--primary-500);
  color: white;
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  border-radius: var(--radius-full);
}

/* 变体 */
.badge-success { background: var(--success); }
.badge-warning { background: var(--warning); }
.badge-error { background: var(--error); }
```

---

## 11. 可访问性规范

### 对比度
- 正文与背景对比度 ≥ 4.5:1
- 大文字（≥18pt）与背景对比度 ≥ 3:1

### 交互元素
- 最小触摸目标: 44x44px（移动端）
- 键盘可访问: 所有交互元素可通过 Tab 键访问
- 焦点状态: 清晰的视觉焦点指示器

### 语义化
- 使用语义化 HTML 标签
- 为图片添加 alt 属性
- 表单输入框关联 label
- 使用 ARIA 属性增强可访问性

---

## 12. 响应式断点

```css
/* 移动优先策略 */
@media (min-width: 640px) {  /* sm */}
@media (min-width: 768px) {  /* md */}
@media (min-width: 1024px) { /* lg */}
@media (min-width: 1280px) { /* xl */}
@media (min-width: 1536px) { /* 2xl */}
```

---

## 13. 图标系统

**推荐图标库**: 
- **Heroicons** - 简洁、专业
- **Lucide Icons** - 现代、一致性好
- **Feather Icons** - 轻量、优雅

**使用规范**:
- 统一尺寸: 20px（小）/ 24px（标准）/ 32px（大）
- 统一线宽: 1.5px 或 2px
- 颜色继承父元素的 color 属性
- SVG 内联，避免使用图片格式

---

## 14. 地图控件样式

```css
.map-control {
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  color: #e2e8f0;
}

.map-legend {
  background: rgba(15, 23, 42, 0.9);
  padding: var(--space-4);
  border-radius: var(--radius-md);
}

.map-tooltip {
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(8px);
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  box-shadow: var(--shadow-xl);
}
```

---

## 15. 数据可视化规范

### ECharts 主题配色
```javascript
const chartTheme = {
  color: [
    '#22c55e', // primary
    '#3b82f6', // secondary
    '#f59e0b', // warning
    '#10b981', // success
    '#ef4444', // error
    '#8b5cf6', // purple
    '#ec4899', // pink
  ],
  backgroundColor: 'transparent',
  textStyle: {
    fontFamily: 'var(--font-sans)',
    color: '#cbd5e1' // slate-300
  },
  title: {
    textStyle: {
      color: '#f8fafc', // slate-50
      fontSize: 18,
      fontWeight: 600
    }
  },
  legend: {
    textStyle: {
      color: '#94a3b8' // slate-400
    }
  },
  grid: {
    borderColor: 'rgba(255, 255, 255, 0.1)'
  }
};
```

---

## 使用建议

1. **优先使用 CSS 变量**: 便于主题切换和维护
2. **保持一致性**: 同类元素使用相同的样式
3. **避免硬编码颜色**: 使用设计系统中定义的变量
4. **渐进增强**: 先保证基础功能，再添加视觉效果
5. **性能优先**: 避免过度使用阴影、模糊等消耗性能的效果
6. **测试暗色模式**: 确保所有元素在深色背景下清晰可见

---

## 下一步

基于这个设计系统，我将为您设计：
1. 登录页面
2. 主界面布局
3. 各功能面板组件

准备好后请告知！
