<template>
  <div class="dashboard">
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon primary"><el-icon><Monitor /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.servers }}</div>
          <div class="stat-label">服务器总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon success"><el-icon><Document /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">巡检总次数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon warning"><el-icon><Clock /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.today }}</div>
          <div class="stat-label">今日巡检</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon danger"><el-icon><Bell /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.alerts }}</div>
          <div class="stat-label">告警次数</div>
        </div>
      </div>
    </div>

    <div class="page-card">
      <div class="card-header">
        <span class="card-title">快速操作</span>
      </div>
      <div style="display: flex; gap: 12px;">
        <el-button type="primary" :icon="Refresh" :loading="runLoading" @click="handleRunNow">
          立即执行巡检
        </el-button>
        <el-button :icon="Plus" @click="$router.push('/servers')">添加服务器</el-button>
        <el-button :icon="Setting" @click="$router.push('/alerts')">配置告警</el-button>
      </div>
    </div>

    <div class="page-card">
      <div class="card-header">
        <span class="card-title">最近巡检记录</span>
        <el-button text type="primary" @click="$router.push('/inspections')">查看全部</el-button>
      </div>
      <el-table :data="recentRecords" v-loading="loading" stripe table-layout="fixed">
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
        <el-table-column prop="inspection_time" label="巡检时间" min-width="170" />
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
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
import { Monitor, Document, Clock, Bell, Refresh, Plus, Setting } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getInspections, getStatistics } from '@/api/inspections'
import { getServers } from '@/api/servers'
import { runNow } from '@/api/schedule'

const loading = ref(false)
const runLoading = ref(false)
const stats = reactive({ servers: 0, total: 0, today: 0, alerts: 0 })
const recentRecords = ref([])
const detailDialog = ref(false)
const currentRecord = ref(null)

const getStatusType = (status) => {
  const map = { success: 'success', warning: 'warning', failed: 'danger' }
  return map[status] || 'info'
}

const fetchData = async () => {
  loading.value = true
  try {
    const [serverRes, statsRes, recordsRes] = await Promise.all([
      getServers({ page_size: 1 }),
      getStatistics(),
      getInspections({ page_size: 10 })
    ])
    
    if (serverRes.success) stats.servers = serverRes.data.total
    if (statsRes.success) {
      stats.total = statsRes.data.total
      stats.today = statsRes.data.today
      stats.alerts = statsRes.data.alerts
    }
    if (recordsRes.success) recentRecords.value = recordsRes.data.list
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

onMounted(fetchData)
</script>
