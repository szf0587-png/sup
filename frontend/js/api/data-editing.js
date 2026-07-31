/**
 * 数据编辑API封装
 * 对接后端 /api/data-editing/* 接口
 */

const DataEditingAPI = {
    /**
     * 添加要素
     */
    async addFeatures(datasource, dataset, features) {
        const response = await Auth.fetch('/api/data-editing/features/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                datasource,
                dataset,
                features
            })
        });
        return await response.json();
    },

    /**
     * 更新要素
     */
    async updateFeatures(datasource, dataset, features, ids) {
        const response = await Auth.fetch('/api/data-editing/features/update', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                datasource,
                dataset,
                features,
                ids
            })
        });
        return await response.json();
    },

    /**
     * 删除要素
     */
    async deleteFeatures(datasource, dataset, ids) {
        const response = await Auth.fetch('/api/data-editing/features/delete', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                datasource,
                dataset,
                ids
            })
        });
        return await response.json();
    },

    /**
     * 按ID查询要素
     */
    async queryByIds(datasource, dataset, ids) {
        const response = await Auth.fetch('/api/data-editing/features/query-by-ids', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                datasource,
                dataset,
                ids
            })
        });
        return await response.json();
    },

    /**
     * SQL查询要素
     */
    async queryBySQL(datasource, dataset, sqlFilter, maxFeatures = 500) {
        const response = await Auth.fetch('/api/data-editing/features/query-by-sql', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                datasource,
                dataset,
                sql_filter: sqlFilter,
                max_features: maxFeatures
            })
        });
        return await response.json();
    },

    /**
     * 批量更新属性
     */
    async batchUpdateAttribute(datasource, dataset, ids, fieldName, newValue) {
        const response = await Auth.fetch('/api/data-editing/features/batch-update-attribute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                datasource,
                dataset,
                ids,
                field_name: fieldName,
                new_value: newValue
            })
        });
        return await response.json();
    }
};

window.DataEditingAPI = DataEditingAPI;
