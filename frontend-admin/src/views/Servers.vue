<template>
  <div class="servers">
    <div class="page-card">
      <div class="card-header">
        <span class="card-title">服务器列表</span>
        <el-button type="primary" :icon="Plus" @click="openDialog()">添加服务器</el-button>
      </div>
      
      <div class="filter-form">
        <el-input v-model="query.search" placeholder="搜索名称/IP" clearable style="width: 200px" @clear="fetchData" @keyup.enter="fetchData" />
        <el-select v-model="query.is_active" placeholder="状态" clearable style="width: 120px" @change="fetchData">
          <el-option label="启用" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
        <el-button :icon="Search" @click="fetchData">搜索</el-button>
      </div>

      <el-table :data="servers" v-loading="loading" stripe table-layout="fixed">
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="ip_address" label="IP地址" min-width="130" />
        <el-table-column prop="port" label="端口" width="80" align="center" />
        <el-table-column prop="ssh_username" label="SSH用户" min-width="100" />
        <el-table-column prop="is_active" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_by_name" label="创建人" width="100" align="center" />
        <el-table-column prop="created_at" label="创建时间" min-width="170" />
        <el-table-column label="操作" width="240" fixed="right" align="center">
          <template #default="{ row }">
            <div style="display: flex; justify-content: center; gap: 4px; flex-wrap: nowrap;">
              <el-button text type="primary" size="small" :loading="row.testing" @click="handleTest(row)">测试</el-button>
              <el-button text type="primary" size="small" @click="handleInspect(row)">巡检</el-button>
              <el-button text type="primary" size="small" @click="openDialog(row)">编辑</el-button>
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

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑服务器' : '添加服务器'" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="服务器名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入服务器名称" />
        </el-form-item>
        <el-form-item label="IP地址" prop="ip_address">
          <el-input v-model="form.ip_address" placeholder="请输入IP地址" />
        </el-form-item>
        <el-form-item label="SSH端口" prop="port">
          <el-input-number v-model="form.port" :min="1" :max="65535" style="width: 100%" />
        </el-form-item>
        <el-form-item label="SSH用户名" prop="ssh_username">
          <el-input v-model="form.ssh_username" placeholder="请输入SSH用户名" />
        </el-form-item>
        <el-form-item label="SSH密码" prop="ssh_password">
          <el-input v-model="form.ssh_password" type="password" :placeholder="form.id ? '留空则不修改' : '请输入SSH密码'" show-password />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getServers, createServer, updateServer, deleteServer, testServer } from '@/api/servers'
import { executeInspection } from '@/api/inspections'

const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const servers = ref([])
const total = ref(0)
const formRef = ref()

const query = reactive({ page: 1, page_size: 10, search: '', is_active: null })

const form = reactive({
  id: null,
  name: '',
  ip_address: '',
  port: 22,
  ssh_username: '',
  ssh_password: '',
  description: '',
  is_active: true
})

const rules = {
  name: [{ required: true, message: '请输入服务器名称', trigger: 'blur' }],
  ip_address: [{ required: true, message: '请输入IP地址', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口', trigger: 'blur' }],
  ssh_username: [{ required: true, message: '请输入SSH用户名', trigger: 'blur' }],
  ssh_password: [{ required: true, message: '请输入SSH密码', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getServers(query)
    if (res.success) {
      servers.value = res.data.list
      total.value = res.data.total
    }
  } finally {
    loading.value = false
  }
}

const openDialog = (row = null) => {
  if (row) {
    Object.assign(form, { ...row, ssh_password: '' })
    rules.ssh_password = []
  } else {
    Object.assign(form, {
      id: null, name: '', ip_address: '', port: 22,
      ssh_username: '', ssh_password: '', description: '', is_active: true
    })
    rules.ssh_password = [{ required: true, message: '请输入SSH密码', trigger: 'blur' }]
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    const data = { ...form }
    if (!data.ssh_password) delete data.ssh_password
    
    const res = form.id
      ? await updateServer(form.id, data)
      : await createServer(data)
    
    if (res.success) {
      ElMessage.success(res.message)
      dialogVisible.value = false
      fetchData()
    } else {
      ElMessage.error(res.message)
    }
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除服务器 "${row.name}" 吗？`, '提示', { type: 'warning' })
    .then(async () => {
      const res = await deleteServer(row.id)
      if (res.success) {
        ElMessage.success(res.message)
        fetchData()
      } else {
        ElMessage.error(res.message)
      }
    })
    .catch(() => {})
}

const handleTest = async (row) => {
  row.testing = true
  try {
    const res = await testServer(row.id)
    if (res.success) {
      ElMessage.success(res.message)
    } else {
      ElMessage.error(res.message)
    }
  } finally {
    row.testing = false
  }
}

const handleInspect = async (row) => {
  ElMessageBox.confirm(`确定要对服务器 "${row.name}" 执行巡检吗？`, '提示')
    .then(async () => {
      const res = await executeInspection({ server_ids: [row.id] })
      if (res.success) {
        ElMessage.success('巡检执行完成')
      } else {
        ElMessage.error(res.message)
      }
    })
    .catch(() => {})
}

onMounted(fetchData)
</script>
