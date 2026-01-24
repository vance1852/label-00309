<template>
  <div class="inspections">
    <div class="page-card">
      <div class="card-header">
        <span class="card-title">巡检记录</span>
        <el-button type="primary" :icon="Refresh" :loading="runLoading" @click="handleRunNow">
          立即执行巡检
        </el-button>
      </div>

      <div class="filter-form">
        <el-input v-model="query.search" placeholder="搜索服务器" clearable style="width: 200px" @clear="fetchData" @keyup.enter="fetchData" />
        <el-select v-model="query.status" placeholder="状态" clearable style="width: 120px" @change="fetchData">
          <el-option label="成功" value="success" />
          <el-option label="警告" value="warning" />
          <el-option label="失败" value="failed" />
        </el-select>
        <el-select v-model="query.has_alert" placeholder="告警" clearable style="width: 120px" @change="fetchData">
          <el-option label="有告警" :value="true" />
          <el-option label="无告警" :value="false" />
        </el-select>
        <el-button :icon="Search" @click="fetchData">搜索</el-button>
      </div>

      <el-table :data="records" v-loading="loading" stripe table-layout="fixed">
        <el-table-column prop="server_name" label="服务器" min-width="120" />
        <el-table-column prop="server_ip" label="IP地址" min-width="130" />
        <el-table-column prop="status_display" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="has_alert" label="告警" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.has_alert" type="danger" size="small">是</el-tag>
            <el-tag v-else type="info" size="small">否</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_scheduled" label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_scheduled ? 'warning' : ''" size="small">
              {{ row.is_scheduled ? '定时' : '手动' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="executed_by_name" label="执行人" width="100" align="center" />
        <el-table-column prop="inspection_time" label="巡检时间" min-width="170" />
        <el-table-column label="操作" width="130" fixed="right" align="center">
          <template #default="{ row }">
            <div style="display: flex; justify-content: center; gap: 4px; flex-wrap: nowrap;">
              <el-button text type="primary" size="small" @click="showDetail(row)">详情</el-button>
              <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.page_size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end;"
        @change="fetchData"
      />
    </div>

    <el-dialog v-model="detailDialog" title="巡检详情" width="700px">
      <template v-if="currentRecord">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="服务器">{{ currentRecord.server_name }}</el-descriptions-item>
          <el-descriptions-item label="IP地址">{{ currentRecord.server_ip }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentRecord.status)">{{ currentRecord.status_display }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="巡检时间">{{ currentRecord.inspection_time }}</el-descriptions-item>
          <el-descriptions-item label="执行命令" :span="2">{{ currentRecord.command }}</el-descriptions-item>
          <el-descriptions-item v-if="currentRecord.has_alert" label="告警信息" :span="2">
            <el-alert :title="currentRecord.alert_message" type="warning" :closable="false" />
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="currentRecord.parsed_result?.disks?.length" style="margin-top: 16px;">
          <h4 style="margin-bottom: 12px;">磁盘详情</h4>
          <el-table :data="currentRecord.parsed_result.disks" border size="small">
            <el-table-column prop="mount_point" label="挂载点" />
            <el-table-column prop="filesystem" label="文件系统" />
            <el-table-column prop="size" label="总容量" width="100" />
            <el-table-column prop="used" label="已使用" width="100" />
            <el-table-column prop="available" label="可用" width="100" />
            <el-table-column prop="use_percent" label="使用率" width="100">
              <template #default="{ row }">
                <el-progress :percentage="row.use_percent" :status="row.use_percent >= 80 ? 'exception' : ''" :stroke-width="10" />
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div style="margin-top: 16px;">
          <h4 style="margin-bottom: 12px;">原始输出</h4>
          <pre style="background: #f5f7fa; padding: 12px; border-radius: 4px; overflow-x: auto; font-size: 12px;">{{ currentRecord.raw_output }}</pre>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getInspections, deleteInspection } from '@/api/inspections'
import { runNow } from '@/api/schedule'

const loading = ref(false)
const runLoading = ref(false)
const records = ref([])
const total = ref(0)
const detailDialog = ref(false)
const currentRecord = ref(null)

const query = reactive({ page: 1, page_size: 10, search: '', status: null, has_alert: null })

const getStatusType = (status) => {
  const map = { success: 'success', warning: 'warning', failed: 'danger' }
  return map[status] || 'info'
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getInspections(query)
    if (res.success) {
      records.value = res.data.list
      total.value = res.data.total
    }
  } finally {
    loading.value = false
  }
}

const handleRunNow = async () => {
  runLoading.value = true
  try {
    const res = await runNow()
    if (res.success) {
      ElMessage.success(res.message)
      fetchData()
    } else {
      ElMessage.error(res.message)
    }
  } finally {
    runLoading.value = false
  }
}

const showDetail = (row) => {
  currentRecord.value = row
  detailDialog.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除这条巡检记录吗？', '提示', { type: 'warning' })
    .then(async () => {
      const res = await deleteInspection(row.id)
      if (res.success) {
        ElMessage.success(res.message)
        fetchData()
      } else {
        ElMessage.error(res.message)
      }
    })
    .catch(() => {})
}

onMounted(fetchData)
</script>
