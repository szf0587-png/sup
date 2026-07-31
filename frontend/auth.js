/**
 * 认证工具模块
 * 用于处理用户登录、token 管理、用户信息获取等
 */

const API_BASE = 'http://localhost:8000';

const Auth = {
    /**
     * 获取存储的 token
     */
    getToken() {
        return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    },

    /**
     * 保存 token
     * @param {string} token - JWT token
     * @param {boolean} remember - 是否记住登录状态
     */
    setToken(token, remember = false) {
        if (remember) {
            localStorage.setItem('access_token', token);
        } else {
            sessionStorage.setItem('access_token', token);
        }
    },

    /**
     * 清除 token
     */
    clearToken() {
        localStorage.removeItem('access_token');
        sessionStorage.removeItem('access_token');
    },

    /**
     * 获取当前用户信息
     * @returns {Promise<Object>} 用户信息
     */
    async getCurrentUser() {
        const token = this.getToken();
        if (!token) {
            throw new Error('未登录');
        }

        try {
            const response = await fetch(`${API_BASE}/api/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.clearToken();
                    throw new Error('登录已过期');
                }
                throw new Error('获取用户信息失败');
            }

            return await response.json();
        } catch (error) {
            console.error('获取用户信息错误:', error);
            throw error;
        }
    },

    /**
     * 登出
     */
    async logout() {
        const token = this.getToken();
        if (token) {
            try {
                await fetch(`${API_BASE}/api/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
            } catch (error) {
                console.error('登出错误:', error);
            }
        }

        this.clearToken();
        window.location.href = 'login.html';
    },

    /**
     * 检查登录状态
     * 如果未登录，跳转到登录页
     */
    async checkAuth() {
        try {
            await this.getCurrentUser();
        } catch (error) {
            console.error('认证检查失败:', error);
            window.location.href = 'login.html';
        }
    },

    /**
     * 创建带认证头的 fetch 请求
     * @param {string} url - 请求 URL
     * @param {Object} options - fetch 选项
     * @returns {Promise<Response>}
     */
    async fetch(url, options = {}) {
        const token = this.getToken();
        if (!token) {
            throw new Error('未登录');
        }

        const headers = {
            'Authorization': `Bearer ${token}`,
            ...options.headers
        };

        try {
            const response = await fetch(url, { ...options, headers });

            if (response.status === 401) {
                this.clearToken();
                window.location.href = 'login.html';
                throw new Error('登录已过期');
            }

            return response;
        } catch (error) {
            console.error('请求错误:', error);
            throw error;
        }
    }
};

// 导出到全局
window.Auth = Auth;
