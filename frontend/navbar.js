/**
 * 顶部导航栏组件
 * 包含：Logo、项目切换、用户信息、退出登录
 */

const TopNavbar = {
    currentUser: null,
    currentProject: null,

    /**
     * 初始化导航栏
     */
    async init() {
        // 创建导航栏 HTML
        this.render();

        // 加载用户信息
        await this.loadUserInfo();

        // 加载项目列表
        await this.loadProjects();

        // 绑定事件
        this.bindEvents();
    },

    /**
     * 渲染导航栏 HTML
     */
    render() {
        const navbar = document.createElement('div');
        navbar.id = 'topNavbar';
        navbar.className = 'top-navbar';
        navbar.innerHTML = `
            <div class="navbar-content">
                <!-- Logo -->
                <div class="navbar-logo">
                    <div class="logo-icon">天</div>
                    <span class="logo-text">天眼寻珍·苍穹</span>
                </div>

                <!-- 项目切换 -->
                <div class="navbar-project">
                    <button class="project-btn" id="projectBtn">
                        <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
                        </svg>
                        <span id="currentProjectName">选择项目</span>
                        <svg class="icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                        </svg>
                    </button>

                    <!-- 项目下拉菜单 -->
                    <div class="dropdown-menu" id="projectDropdown" style="display: none;">
                        <div class="dropdown-header">
                            <span class="dropdown-title">我的项目</span>
                            <button class="btn-icon" id="createProjectBtn" title="创建项目">
                                <svg class="icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                                </svg>
                            </button>
                        </div>
                        <div class="dropdown-body" id="projectList">
                            <div class="loading">加载中...</div>
                        </div>
                    </div>
                </div>

                <!-- 右侧区域 -->
                <div class="navbar-right">
                    <!-- 用户信息 -->
                    <div class="navbar-user">
                        <button class="user-btn" id="userBtn">
                            <div class="user-avatar" id="userAvatar">U</div>
                            <div class="user-info">
                                <div class="user-name" id="userName">用户</div>
                                <div class="user-role" id="userRole">角色</div>
                            </div>
                            <svg class="icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                            </svg>
                        </button>

                        <!-- 用户下拉菜单 -->
                        <div class="dropdown-menu" id="userDropdown" style="display: none;">
                            <div class="dropdown-item" id="userCenterBtn">
                                <svg class="icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                                </svg>
                                <span>个人中心</span>
                            </div>
                            <div class="dropdown-item" id="settingsBtn">
                                <svg class="icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                </svg>
                                <span>设置</span>
                            </div>
                            <div class="dropdown-divider"></div>
                            <div class="dropdown-item" id="logoutBtn">
                                <svg class="icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                                </svg>
                                <span>退出登录</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 插入到页面顶部
        document.body.insertBefore(navbar, document.body.firstChild);

        // 添加样式
        this.addStyles();
    },

    /**
     * 添加样式
     */
    addStyles() {
        if (document.getElementById('topNavbarStyles')) return;

        const style = document.createElement('style');
        style.id = 'topNavbarStyles';
        style.textContent = `
            .top-navbar {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                height: 64px;
                background: rgba(15, 23, 42, 0.95);
                backdrop-filter: blur(10px);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                z-index: 1000;
            }

            .navbar-content {
                height: 100%;
                padding: 0 1.5rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
                max-width: 100%;
            }

            /* Logo */
            .navbar-logo {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                cursor: pointer;
            }

            .logo-icon {
                width: 40px;
                height: 40px;
                background: linear-gradient(135deg, #22c55e, #3b82f6);
                border-radius: 0.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.25rem;
                font-weight: 700;
                color: white;
            }

            .logo-text {
                font-size: 1.125rem;
                font-weight: 600;
                color: #f8fafc;
            }

            /* 项目切换 */
            .navbar-project {
                flex: 1;
                max-width: 300px;
                margin-left: 2rem;
                position: relative;
            }

            .project-btn {
                width: 100%;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.5rem 0.75rem;
                background: rgba(30, 41, 59, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 0.5rem;
                color: #e2e8f0;
                font-size: 0.875rem;
                cursor: pointer;
                transition: all 150ms ease-out;
            }

            .project-btn:hover {
                background: rgba(30, 41, 59, 1);
                border-color: rgba(255, 255, 255, 0.2);
            }

            .project-btn .icon {
                width: 20px;
                height: 20px;
                flex-shrink: 0;
            }

            .project-btn .icon-sm {
                width: 16px;
                height: 16px;
                margin-left: auto;
                flex-shrink: 0;
            }

            /* 右侧区域 */
            .navbar-right {
                display: flex;
                align-items: center;
                gap: 1rem;
            }

            /* 用户信息 */
            .navbar-user {
                position: relative;
            }

            .user-btn {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                padding: 0.375rem 0.75rem;
                background: rgba(30, 41, 59, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 0.5rem;
                color: #e2e8f0;
                cursor: pointer;
                transition: all 150ms ease-out;
            }

            .user-btn:hover {
                background: rgba(30, 41, 59, 1);
                border-color: rgba(255, 255, 255, 0.2);
            }

            .user-avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: linear-gradient(135deg, #22c55e, #3b82f6);
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                color: white;
                font-size: 0.875rem;
            }

            .user-info {
                display: flex;
                flex-direction: column;
                align-items: flex-start;
            }

            .user-name {
                font-size: 0.875rem;
                font-weight: 500;
                color: #f8fafc;
                line-height: 1.2;
            }

            .user-role {
                font-size: 0.75rem;
                color: #94a3b8;
                line-height: 1.2;
            }

            .user-btn .icon-sm {
                width: 16px;
                height: 16px;
                flex-shrink: 0;
            }

            /* 下拉菜单 */
            .dropdown-menu {
                position: absolute;
                top: calc(100% + 0.5rem);
                right: 0;
                min-width: 240px;
                background: rgba(30, 41, 59, 0.95);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 0.75rem;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1),
                           0 10px 10px -5px rgba(0, 0, 0, 0.04);
                overflow: hidden;
                z-index: 1001;
            }

            .navbar-project .dropdown-menu {
                left: 0;
                right: auto;
            }

            .dropdown-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0.75rem 1rem;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }

            .dropdown-title {
                font-size: 0.875rem;
                font-weight: 600;
                color: #f8fafc;
            }

            .btn-icon {
                width: 28px;
                height: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: transparent;
                border: none;
                border-radius: 0.375rem;
                color: #94a3b8;
                cursor: pointer;
                transition: all 150ms ease-out;
            }

            .btn-icon:hover {
                background: rgba(255, 255, 255, 0.1);
                color: #e2e8f0;
            }

            .dropdown-body {
                max-height: 320px;
                overflow-y: auto;
                padding: 0.5rem;
            }

            .dropdown-item {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                padding: 0.625rem 0.75rem;
                border-radius: 0.375rem;
                color: #cbd5e1;
                font-size: 0.875rem;
                cursor: pointer;
                transition: all 150ms ease-out;
            }

            .dropdown-item:hover {
                background: rgba(255, 255, 255, 0.1);
                color: #f8fafc;
            }

            .dropdown-item .icon-sm {
                width: 18px;
                height: 18px;
                flex-shrink: 0;
            }

            .dropdown-divider {
                height: 1px;
                background: rgba(255, 255, 255, 0.1);
                margin: 0.5rem 0;
            }

            .project-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0.625rem 0.75rem;
                border-radius: 0.375rem;
                color: #cbd5e1;
                font-size: 0.875rem;
                cursor: pointer;
                transition: all 150ms ease-out;
            }

            .project-item:hover {
                background: rgba(255, 255, 255, 0.1);
                color: #f8fafc;
            }

            .project-item.active {
                background: rgba(34, 197, 94, 0.2);
                color: #22c55e;
            }

            .project-item-name {
                flex: 1;
            }

            .project-item-badge {
                padding: 0.125rem 0.5rem;
                background: rgba(34, 197, 94, 0.2);
                color: #22c55e;
                font-size: 0.75rem;
                border-radius: 9999px;
            }

            .loading {
                padding: 1rem;
                text-align: center;
                color: #94a3b8;
                font-size: 0.875rem;
            }

            /* 图标尺寸 */
            .icon {
                width: 20px;
                height: 20px;
            }

            .icon-sm {
                width: 16px;
                height: 16px;
            }

            /* 响应式 */
            @media (max-width: 768px) {
                .navbar-content {
                    padding: 0 1rem;
                }

                .navbar-project {
                    max-width: 200px;
                }

                .logo-text {
                    display: none;
                }

                .user-info {
                    display: none;
                }
            }
        `;

        document.head.appendChild(style);
    },

    /**
     * 加载用户信息
     */
    async loadUserInfo() {
        try {
            this.currentUser = await Auth.getCurrentUser();

            // 更新 UI
            document.getElementById('userName').textContent = this.currentUser.display_name || this.currentUser.username;
            document.getElementById('userRole').textContent = this.currentUser.role === 'admin' ? '管理员' : '用户';
            document.getElementById('userAvatar').textContent = (this.currentUser.display_name || this.currentUser.username).charAt(0).toUpperCase();
        } catch (error) {
            console.error('加载用户信息失败:', error);
        }
    },

    /**
     * 加载项目列表
     */
    async loadProjects() {
        try {
            const response = await Auth.fetch(`${API_BASE}/api/projects`);
            const data = await response.json();

            this.renderProjects(data.projects, data.active_project_id);
        } catch (error) {
            console.error('加载项目列表失败:', error);
            document.getElementById('projectList').innerHTML = '<div class="loading">加载失败</div>';
        }
    },

    /**
     * 渲染项目列表
     */
    renderProjects(projects, activeProjectId) {
        const projectList = document.getElementById('projectList');

        if (!projects || projects.length === 0) {
            projectList.innerHTML = '<div class="loading">暂无项目</div>';
            return;
        }

        const activeProject = projects.find(p => p.id === activeProjectId);
        if (activeProject) {
            document.getElementById('currentProjectName').textContent = activeProject.name;
            this.currentProject = activeProject;
        }

        projectList.innerHTML = projects.map(project => `
            <div class="project-item ${project.id === activeProjectId ? 'active' : ''}" data-project-id="${project.id}">
                <span class="project-item-name">${project.name}</span>
                ${project.id === activeProjectId ? '<span class="project-item-badge">激活</span>' : ''}
            </div>
        `).join('');

        // 绑定项目切换事件
        document.querySelectorAll('.project-item').forEach(item => {
            item.addEventListener('click', () => {
                const projectId = item.dataset.projectId;
                this.activateProject(projectId);
            });
        });
    },

    /**
     * 激活项目
     */
    async activateProject(projectId) {
        try {
            const response = await Auth.fetch(`${API_BASE}/api/projects/${projectId}/activate`, {
                method: 'POST'
            });

            const data = await response.json();

            // 更新当前项目显示
            document.getElementById('currentProjectName').textContent = data.active_project_name;

            // 重新加载项目列表
            await this.loadProjects();

            // 关闭下拉菜单
            document.getElementById('projectDropdown').style.display = 'none';

            // 触发项目切换事件
            window.dispatchEvent(new CustomEvent('projectChanged', { detail: { projectId } }));
        } catch (error) {
            console.error('激活项目失败:', error);
            alert('激活项目失败');
        }
    },

    /**
     * 绑定事件
     */
    bindEvents() {
        // 项目按钮点击
        document.getElementById('projectBtn').addEventListener('click', (e) => {
            e.stopPropagation();
            const dropdown = document.getElementById('projectDropdown');
            const userDropdown = document.getElementById('userDropdown');
            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
            userDropdown.style.display = 'none';
        });

        // 用户按钮点击
        document.getElementById('userBtn').addEventListener('click', (e) => {
            e.stopPropagation();
            const dropdown = document.getElementById('userDropdown');
            const projectDropdown = document.getElementById('projectDropdown');
            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
            projectDropdown.style.display = 'none';
        });

        // 点击页面其他地方关闭下拉菜单
        document.addEventListener('click', () => {
            document.getElementById('projectDropdown').style.display = 'none';
            document.getElementById('userDropdown').style.display = 'none';
        });

        // 创建项目按钮
        document.getElementById('createProjectBtn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.showCreateProjectModal();
        });

        // 退出登录
        document.getElementById('logoutBtn').addEventListener('click', async () => {
            if (confirm('确定要退出登录吗？')) {
                await Auth.logout();
            }
        });

        // 个人中心
        document.getElementById('userCenterBtn').addEventListener('click', () => {
            alert('个人中心功能开发中');
        });

        // 设置
        document.getElementById('settingsBtn').addEventListener('click', () => {
            alert('设置功能开发中');
        });
    },

    /**
     * 显示创建项目模态框
     */
    showCreateProjectModal() {
        // TODO: 实现创建项目模态框
        const projectName = prompt('请输入项目名称：');
        if (projectName) {
            this.createProject(projectName);
        }
    },

    /**
     * 创建项目
     */
    async createProject(name) {
        try {
            const response = await Auth.fetch(`${API_BASE}/api/projects`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name })
            });

            if (response.ok) {
                // 重新加载项目列表
                await this.loadProjects();
                alert('项目创建成功！');
            } else {
                throw new Error('创建项目失败');
            }
        } catch (error) {
            console.error('创建项目失败:', error);
            alert('创建项目失败');
        }
    }
};

// 导出到全局
window.TopNavbar = TopNavbar;
