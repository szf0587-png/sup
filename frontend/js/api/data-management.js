/**
 * 数据管理API封装
 * 对接后端 /api/data-management/* 接口
 */

const DataManagementAPI = {
    /**
     * 获取数据集元数据
     */
    async getMetadata(datasource, dataset) {
        const response = await Auth.fetch(`/api/data-management/datasets/${datasource}/${dataset}/metadata`);
        return await response.json();
    },

    /**
     * 列出数据源中的所有数据集
     */
    async listDatasets(datasource) {
        const response = await Auth.fetch(`/api/data-management/datasets/${datasource}/list`);
        return await response.json();
    },

    /**
     * 添加字段
     */
    async addField(datasource, dataset, fieldName, fieldType, fieldLength = 254) {
        const response = await Auth.fetch('/api/data-management/fields/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                datasource,
                dataset,
                field_name: fieldName,
                field_type: fieldType,
                field_length: fieldLength
            })
        });
        return await response.json();
    },

    /**
     * 查询属性表记录（分页）
     */
    async getRecords(datasource, dataset, page = 1, pageSize = 100, sqlFilter = null) {
        const params = new URLSearchParams({
            page: page.toString(),
            page_size: pageSize.toString()
        });

        if (sqlFilter) {
            params.append('sql_filter', sqlFilter);
        }

        const response = await Auth.fetch(
            `/api/data-management/records/${datasource}/${dataset}?${params.toString()}`
        );
        return await response.json();
    },

    /**
     * 导入GeoJSON
     */
    async importGeoJSON(file, targetDatasource, targetDataset = null) {
        const formData = new FormData();
        formData.append('file', file);
        if (targetDatasource) formData.append('target_datasource', targetDatasource);
        if (targetDataset) formData.append('target_dataset', targetDataset);

        const response = await Auth.fetch('/api/data-management/import/geojson', {
            method: 'POST',
            body: formData
        });
        return await response.json();
    },

    /**
     * 导入CSV（带坐标）
     */
    async importCSV(file, lonField = 'longitude', latField = 'latitude', targetDatasource = null, targetDataset = null) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('lon_field', lonField);
        formData.append('lat_field', latField);
        if (targetDatasource) formData.append('target_datasource', targetDatasource);
        if (targetDataset) formData.append('target_dataset', targetDataset);

        const response = await Auth.fetch('/api/data-management/import/csv', {
            method: 'POST',
            body: formData
        });
        return await response.json();
    },

    /**
     * 导出GeoJSON
     */
    async exportGeoJSON(datasource, dataset, sqlFilter = null) {
        const response = await Auth.fetch('/api/data-management/export/geojson', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                datasource,
                dataset,
                format: 'geojson',
                sql_filter: sqlFilter
            })
        });
        return await response.json();
    }
};

window.DataManagementAPI = DataManagementAPI;
