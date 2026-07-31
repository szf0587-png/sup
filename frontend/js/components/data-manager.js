/**
 * 数据管理器
 * 负责数据导入、导出、元数据管理
 */

class DataManager {
    constructor() {
        this.currentDataset = null;
    }

    /**
     * 初始化数据管理器
     */
    init() {
        console.log('✓ DataManager初始化完成');
    }

    /**
     * 导入GeoJSON
     */
    async importGeoJSON() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.geojson,.json';

        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const datasource = prompt('请输入目标数据源名称:', 'user_ds');
            if (!datasource) return;

            const dataset = prompt('请输入目标数据集名称:', file.name.replace(/\.(geo)?json$/, ''));
            if (!dataset) return;

            try {
                if (window.showToast) {
                    showToast('info', '正在导入', '请稍候...');
                }

                const result = await DataManagementAPI.importGeoJSON(file, datasource, dataset);

                if (window.showToast) {
                    showToast('success', '导入成功', `成功导入 ${result.feature_count} 个要素到 ${result.dataset}`);
                }

                // 询问是否加载到地图
                if (confirm('是否将数据加载到地图？')) {
                    this.loadDatasetToMap(result.datasource, result.dataset);
                }

            } catch (error) {
                console.error('导入GeoJSON失败:', error);
                if (window.showToast) {
                    showToast('error', '导入失败', error.message);
                }
            }
        };

        input.click();
    }

    /**
     * 导入CSV（带坐标）
     */
    async importCSV() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.csv';

        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const lonField = prompt('请输入经度字段名:', 'longitude');
            if (!lonField) return;

            const latField = prompt('请输入纬度字段名:', 'latitude');
            if (!latField) return;

            const datasource = prompt('请输入目标数据源名称:', 'user_ds');
            if (!datasource) return;

            const dataset = prompt('请输入目标数据集名称:', file.name.replace('.csv', ''));
            if (!dataset) return;

            try {
                if (window.showToast) {
                    showToast('info', '正在导入', '请稍候...');
                }

                const result = await DataManagementAPI.importCSV(file, lonField, latField, datasource, dataset);

                if (window.showToast) {
                    showToast('success', '导入成功', `成功导入 ${result.feature_count} 个点要素到 ${result.dataset}`);
                }

                // 询问是否加载到地图
                if (confirm('是否将数据加载到地图？')) {
                    this.loadDatasetToMap(result.datasource, result.dataset);
                }

            } catch (error) {
                console.error('导入CSV失败:', error);
                if (window.showToast) {
                    showToast('error', '导入失败', error.message);
                }
            }
        };

        input.click();
    }

    /**
     * 导出GeoJSON
     */
    async exportGeoJSON() {
        const datasource = prompt('请输入数据源名称:', 'user_ds');
        if (!datasource) return;

        const dataset = prompt('请输入数据集名称:');
        if (!dataset) return;

        try {
            if (window.showToast) {
                showToast('info', '正在导出', '请稍候...');
            }

            const result = await DataManagementAPI.exportGeoJSON(datasource, dataset);

            // 下载文件
            const downloadUrl = result.download_url;
            if (downloadUrl) {
                window.open(downloadUrl, '_blank');
            }

            if (window.showToast) {
                showToast('success', '导出成功', `已导出 ${result.feature_count} 个要素`);
            }

        } catch (error) {
            console.error('导出GeoJSON失败:', error);
            if (window.showToast) {
                showToast('error', '导出失败', error.message);
            }
        }
    }

    /**
     * 查看元数据
     */
    async viewMetadata() {
        const datasource = prompt('请输入数据源名称:', 'user_ds');
        if (!datasource) return;

        const dataset = prompt('请输入数据集名称:');
        if (!dataset) return;

        try {
            const result = await DataManagementAPI.getMetadata(datasource, dataset);

            // 显示元数据对话框
            this.showMetadataDialog(result.metadata);

        } catch (error) {
            console.error('获取元数据失败:', error);
            if (window.showToast) {
                showToast('error', '获取失败', error.message);
            }
        }
    }

    /**
     * 显示元数据对话框
     */
    showMetadataDialog(metadata) {
        const html = `
            <div class="space-y-3">
                <h3 class="text-lg font-bold text-slate-200 mb-3">数据集元数据</h3>

                <div class="space-y-2 text-sm">
                    <div class="flex justify-between">
                        <span class="text-slate-400">名称:</span>
                        <span class="text-slate-200">${metadata.name}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-slate-400">类型:</span>
                        <span class="text-slate-200">${metadata.type}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-slate-400">记录数:</span>
                        <span class="text-slate-200">${metadata.record_count}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-slate-400">坐标系:</span>
                        <span class="text-slate-200 text-xs">${metadata.coordinate_system || 'N/A'}</span>
                    </div>
                </div>

                <div class="mt-4">
                    <h4 class="text-slate-300 font-medium mb-2">字段列表</h4>
                    <div class="space-y-1 max-h-60 overflow-y-auto">
                        ${metadata.fields.map(field => `
                            <div class="flex items-center justify-between px-3 py-2 bg-slate-800 rounded text-sm">
                                <span class="text-slate-200">${field.name}</span>
                                <span class="text-slate-400 text-xs">${field.type}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        // 更新右侧面板内容
        if (window.RightPanel) {
            document.getElementById('panel-content').innerHTML = html;
        }
    }

    /**
     * 添加字段
     */
    async addField() {
        const datasource = prompt('请输入数据源名称:', 'user_ds');
        if (!datasource) return;

        const dataset = prompt('请输入数据集名称:');
        if (!dataset) return;

        const fieldName = prompt('请输入字段名称:');
        if (!fieldName) return;

        const fieldType = prompt('请输入字段类型 (TEXT/INTEGER/DOUBLE/DATE/BOOLEAN):', 'TEXT');
        if (!fieldType) return;

        try {
            const result = await DataManagementAPI.addField(datasource, dataset, fieldName, fieldType);

            if (window.showToast) {
                showToast('success', '字段添加成功', `字段 "${fieldName}" 已添加到 ${dataset}`);
            }

        } catch (error) {
            console.error('添加字段失败:', error);
            if (window.showToast) {
                showToast('error', '添加失败', error.message);
            }
        }
    }

    /**
     * 加载数据集到地图
     */
    async loadDatasetToMap(datasource, dataset) {
        if (!window.LayerManager) {
            console.error('LayerManager未初始化');
            return;
        }

        try {
            const layerId = `${datasource}_${dataset}_${Date.now()}`;

            await window.LayerManager.addLayer({
                id: layerId,
                name: dataset,
                type: 'geojson',
                datasource: datasource,
                dataset: dataset,
                style: {
                    color: '#3b82f6',
                    weight: 2,
                    fillOpacity: 0.2
                }
            });

        } catch (error) {
            console.error('加载数据集到地图失败:', error);
        }
    }
}

// 导出为全局对象
window.DataManager = new DataManager();
