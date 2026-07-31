/**
 * 分析工具管理器
 * 提供空间分析向导界面和结果展示
 */

class AnalysisTools {
    constructor() {
        this.currentAnalysis = null;
        this.analysisResults = [];
    }

    /**
     * 初始化分析工具
     */
    init() {
        console.log('✓ AnalysisTools初始化完成');
    }

    /**
     * 打开分析工具
     */
    openAnalysis(analysisType) {
        this.currentAnalysis = analysisType;

        // 显示分析配置面板
        this.showAnalysisConfig(analysisType);
    }

    /**
     * 显示分析配置面板
     */
    showAnalysisConfig(analysisType) {
        const config = this.getAnalysisConfig(analysisType);

        if (!config) {
            console.error('未知的分析类型:', analysisType);
            return;
        }

        // 更新右侧面板内容
        if (window.RightPanel) {
            const content = this.renderAnalysisForm(config);
            document.getElementById('panel-content').innerHTML = content;
            document.getElementById('panel-title').textContent = config.title;
        }
    }

    /**
     * 获取分析配置
     */
    getAnalysisConfig(analysisType) {
        const configs = {
            'slope': {
                title: '坡度分析',
                icon: 'mountain',
                description: '计算DEM地表坡度（度或百分比）',
                fields: [
                    { name: 'datasource', label: '数据源', type: 'text', value: 'luonan_ds', required: true },
                    { name: 'dataset', label: 'DEM数据集', type: 'text', value: 'luonan_dem', required: true },
                    { name: 'slope_type', label: '坡度类型', type: 'select', options: [
                        { value: 'DEGREE', label: '度' },
                        { value: 'PERCENT_RISE', label: '百分比' }
                    ], value: 'DEGREE' },
                    { name: 'z_factor', label: 'Z因子', type: 'number', value: 1.0, step: 0.1 }
                ],
                apiMethod: 'analyzeSlope'
            },
            'aspect': {
                title: '坡向分析',
                icon: 'compass',
                description: '计算DEM地表朝向（0-360度）',
                fields: [
                    { name: 'datasource', label: '数据源', type: 'text', value: 'luonan_ds', required: true },
                    { name: 'dataset', label: 'DEM数据集', type: 'text', value: 'luonan_dem', required: true }
                ],
                apiMethod: 'analyzeAspect'
            },
            'hillshade': {
                title: '山体阴影分析',
                icon: 'sun',
                description: '生成地形晕渲图',
                fields: [
                    { name: 'datasource', label: '数据源', type: 'text', value: 'luonan_ds', required: true },
                    { name: 'dataset', label: 'DEM数据集', type: 'text', value: 'luonan_dem', required: true },
                    { name: 'azimuth', label: '光源方位角', type: 'number', value: 315, min: 0, max: 360 },
                    { name: 'altitude', label: '光源高度角', type: 'number', value: 45, min: 0, max: 90 }
                ],
                apiMethod: 'analyzeHillshade'
            },
            'kernel-density': {
                title: '核密度分析',
                icon: 'fire',
                description: '计算点要素的空间密度分布',
                fields: [
                    { name: 'datasource', label: '数据源', type: 'text', value: 'luonan_ds', required: true },
                    { name: 'dataset', label: '点数据集', type: 'text', required: true },
                    { name: 'search_radius', label: '搜索半径（米）', type: 'number', value: 2000, required: true },
                    { name: 'cell_size', label: '栅格像元大小（米）', type: 'number', value: 100 },
                    { name: 'population_field', label: '权重字段', type: 'text', placeholder: '可选' }
                ],
                apiMethod: 'kernelDensity'
            },
            'point-density': {
                title: '点密度分析',
                icon: 'braille',
                description: '计算单位面积内的点数量',
                fields: [
                    { name: 'datasource', label: '数据源', type: 'text', value: 'luonan_ds', required: true },
                    { name: 'dataset', label: '点数据集', type: 'text', required: true },
                    { name: 'cell_size', label: '栅格像元大小（米）', type: 'number', value: 100, required: true },
                    { name: 'search_radius', label: '搜索半径（米）', type: 'number', value: 1000, required: true },
                    { name: 'population_field', label: '权重字段', type: 'text', placeholder: '可选' }
                ],
                apiMethod: 'pointDensity'
            },
            'weighted-overlay': {
                title: '加权叠加分析',
                icon: 'layer-group',
                description: '多因子综合评价（核心功能）',
                fields: [
                    { name: 'datasource', label: '数据源', type: 'text', value: 'luonan_ds', required: true },
                    { name: 'layers_config', label: '图层配置', type: 'json',
                      placeholder: '[\n  {"dataset": "slope_reclass", "weight": 0.4},\n  {"dataset": "aspect_reclass", "weight": 0.3},\n  {"dataset": "soil_reclass", "weight": 0.3}\n]',
                      required: true }
                ],
                apiMethod: 'weightedOverlay',
                note: '权重总和必须为1.0'
            },
            'idw': {
                title: 'IDW反距离权重插值',
                icon: 'chart-line',
                description: '根据采样点生成连续表面',
                fields: [
                    { name: 'datasource', label: '数据源', type: 'text', value: 'luonan_ds', required: true },
                    { name: 'dataset', label: '点数据集', type: 'text', required: true },
                    { name: 'z_field', label: '高程/值字段', type: 'text', required: true },
                    { name: 'cell_size', label: '栅格像元大小', type: 'number', value: 100, required: true },
                    { name: 'power', label: '距离幂次', type: 'number', value: 2.0, step: 0.1 },
                    { name: 'search_radius', label: '搜索半径（米）', type: 'number', placeholder: '可选' }
                ],
                apiMethod: 'idwInterpolation'
            },
            'kriging': {
                title: 'Kriging克里金插值',
                icon: 'chart-area',
                description: '基于空间自相关的最优插值',
                fields: [
                    { name: 'datasource', label: '数据源', type: 'text', value: 'luonan_ds', required: true },
                    { name: 'dataset', label: '点数据集', type: 'text', required: true },
                    { name: 'z_field', label: '高程/值字段', type: 'text', required: true },
                    { name: 'cell_size', label: '栅格像元大小', type: 'number', value: 100, required: true },
                    { name: 'variogram_type', label: '变异函数类型', type: 'select', options: [
                        { value: 'SPHERICAL', label: '球状' },
                        { value: 'EXPONENTIAL', label: '指数' },
                        { value: 'GAUSSIAN', label: '高斯' },
                        { value: 'LINEAR', label: '线性' }
                    ], value: 'SPHERICAL' }
                ],
                apiMethod: 'krigingInterpolation'
            }
        };

        return configs[analysisType];
    }

    /**
     * 渲染分析表单
     */
    renderAnalysisForm(config) {
        let html = `
            <div class="space-y-4">
                <div class="glass-panel p-4 rounded-lg">
                    <div class="flex items-center mb-2">
                        <i class="fas fa-${config.icon} text-green-400 mr-2"></i>
                        <h4 class="text-slate-300 font-medium">${config.title}</h4>
                    </div>
                    <p class="text-slate-400 text-sm">${config.description}</p>
                    ${config.note ? `<p class="text-yellow-400 text-sm mt-2"><i class="fas fa-info-circle mr-1"></i>${config.note}</p>` : ''}
                </div>

                <form id="analysis-form" class="space-y-3">
        `;

        // 渲染表单字段
        config.fields.forEach(field => {
            html += this.renderFormField(field);
        });

        html += `
                </form>

                <div class="flex space-x-2">
                    <button onclick="window.AnalysisTools.runAnalysis('${config.apiMethod}')"
                            class="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white font-medium cursor-pointer transition-colors">
                        <i class="fas fa-play mr-2"></i>运行分析
                    </button>
                    <button onclick="window.AnalysisTools.resetForm()"
                            class="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 cursor-pointer transition-colors">
                        <i class="fas fa-redo mr-2"></i>重置
                    </button>
                </div>

                <div id="analysis-result" class="hidden glass-panel p-4 rounded-lg">
                    <!-- 结果将显示在这里 -->
                </div>
            </div>
        `;

        return html;
    }

    /**
     * 渲染表单字段
     */
    renderFormField(field) {
        let input = '';

        switch (field.type) {
            case 'text':
            case 'number':
                input = `
                    <input type="${field.type}"
                           id="field-${field.name}"
                           name="${field.name}"
                           value="${field.value || ''}"
                           placeholder="${field.placeholder || ''}"
                           ${field.required ? 'required' : ''}
                           ${field.min !== undefined ? `min="${field.min}"` : ''}
                           ${field.max !== undefined ? `max="${field.max}"` : ''}
                           ${field.step !== undefined ? `step="${field.step}"` : ''}
                           class="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500 transition-colors">
                `;
                break;

            case 'select':
                input = `
                    <select id="field-${field.name}"
                            name="${field.name}"
                            class="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500 transition-colors cursor-pointer">
                        ${field.options.map(opt => `
                            <option value="${opt.value}" ${opt.value === field.value ? 'selected' : ''}>${opt.label}</option>
                        `).join('')}
                    </select>
                `;
                break;

            case 'json':
                input = `
                    <textarea id="field-${field.name}"
                              name="${field.name}"
                              rows="6"
                              placeholder="${field.placeholder || ''}"
                              ${field.required ? 'required' : ''}
                              class="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 font-mono text-sm focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500 transition-colors"></textarea>
                `;
                break;
        }

        return `
            <div>
                <label class="block text-slate-300 text-sm font-medium mb-1">
                    ${field.label}
                    ${field.required ? '<span class="text-red-400">*</span>' : ''}
                </label>
                ${input}
            </div>
        `;
    }

    /**
     * 运行分析
     */
    async runAnalysis(apiMethod) {
        try {
            // 获取表单数据
            const form = document.getElementById('analysis-form');
            const formData = new FormData(form);
            const params = {};

            for (const [key, value] of formData.entries()) {
                // 处理JSON字段
                if (key === 'layers_config') {
                    try {
                        const parsed = JSON.parse(value);
                        params.layers = parsed;
                    } catch (e) {
                        throw new Error('图层配置JSON格式错误');
                    }
                } else {
                    // 转换数字类型
                    const input = form.querySelector(`[name="${key}"]`);
                    if (input && input.type === 'number') {
                        params[key] = value ? parseFloat(value) : undefined;
                    } else {
                        params[key] = value || undefined;
                    }
                }
            }

            // 显示进度
            this.showProgress('正在运行分析...');

            // 调用API
            const result = await SpatialAnalysisAPI[apiMethod](params);

            // 显示结果
            this.showResult(result);

            // 保存结果
            this.analysisResults.push({
                type: this.currentAnalysis,
                params: params,
                result: result,
                timestamp: new Date().toISOString()
            });

        } catch (error) {
            console.error('分析运行失败:', error);
            this.showError(error.message);
        }
    }

    /**
     * 显示进度
     */
    showProgress(message) {
        const resultDiv = document.getElementById('analysis-result');
        resultDiv.classList.remove('hidden');
        resultDiv.innerHTML = `
            <div class="flex items-center justify-center py-4">
                <div class="spinner mr-3"></div>
                <span class="text-slate-300">${message}</span>
            </div>
        `;
    }

    /**
     * 显示结果
     */
    showResult(result) {
        const resultDiv = document.getElementById('analysis-result');
        resultDiv.classList.remove('hidden');
        resultDiv.innerHTML = `
            <div class="space-y-3">
                <div class="flex items-center text-green-400">
                    <i class="fas fa-check-circle mr-2"></i>
                    <span class="font-medium">分析完成</span>
                </div>

                <div class="space-y-2 text-sm">
                    <div class="flex justify-between">
                        <span class="text-slate-400">结果ID:</span>
                        <span class="text-slate-200 font-mono">${result.result_id || 'N/A'}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-slate-400">消息:</span>
                        <span class="text-slate-200">${result.message || '成功'}</span>
                    </div>
                </div>

                <div class="flex space-x-2 pt-2">
                    <button onclick="window.AnalysisTools.viewResult('${result.result_id}')"
                            class="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm cursor-pointer transition-colors">
                        查看结果
                    </button>
                    <button onclick="window.AnalysisTools.exportResult('${result.result_id}')"
                            class="flex-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-sm cursor-pointer transition-colors">
                        导出
                    </button>
                </div>
            </div>
        `;

        if (window.showToast) {
            showToast('success', '分析完成', `结果ID: ${result.result_id}`);
        }
    }

    /**
     * 显示错误
     */
    showError(message) {
        const resultDiv = document.getElementById('analysis-result');
        resultDiv.classList.remove('hidden');
        resultDiv.innerHTML = `
            <div class="flex items-start text-red-400">
                <i class="fas fa-exclamation-triangle mr-2 mt-1"></i>
                <div>
                    <div class="font-medium mb-1">分析失败</div>
                    <div class="text-sm text-slate-300">${message}</div>
                </div>
            </div>
        `;

        if (window.showToast) {
            showToast('error', '分析失败', message);
        }
    }

    /**
     * 重置表单
     */
    resetForm() {
        document.getElementById('analysis-form')?.reset();
        document.getElementById('analysis-result')?.classList.add('hidden');
    }

    /**
     * 查看结果
     */
    viewResult(resultId) {
        // TODO: 实现结果查看功能
        console.log('查看结果:', resultId);
        if (window.showToast) {
            showToast('info', '功能开发中', '结果查看功能即将推出');
        }
    }

    /**
     * 导出结果
     */
    exportResult(resultId) {
        // TODO: 实现结果导出功能
        console.log('导出结果:', resultId);
        if (window.showToast) {
            showToast('info', '功能开发中', '结果导出功能即将推出');
        }
    }

    /**
     * 获取历史分析结果
     */
    getAnalysisHistory() {
        return this.analysisResults;
    }
}

// 导出为全局对象
window.AnalysisTools = new AnalysisTools();
