<template>
  <div class="alerts">
    <div class="page-card">
      <div class="card-header">
        <span class="card-title">邮件服务器配置</span>
      </div>
      <el-form ref="configFormRef" :model="configForm" :rules="configRules" label-width="120px" style="max-width: 600px;">
        <el-form-item label="SMTP服务器" prop="smtp_server">
          <el-input v-model="configForm.smtp_server" placeholder="如: smtp.qq.com" />
        </el-form-item>
        <el-form-item label="SMTP端口" prop="smtp_port">
          <el-input-number v-model="configForm.smtp_port" :min="1" :max="65535" style="width: 100%" />
        </el-form-item>
        <el-form-item label="SMTP用户名" prop="smtp_username">
          <el-input v-model="configForm.smtp_username" placeholder="邮箱账号" />
        </el-form-item>
        <el-form-item label="SMTP密码" prop="smtp_password">
          <el-input v-model="configForm.smtp_password" type="password" placeholder="邮箱密码或授权码" show-password />
        </el-form-item>
        <el-form-item label="发件人邮箱" prop="sender_email">
          <el-input v-model="configForm.sender_email" placeholder="发件人邮箱地址" />
        </el-form-item>
        <el-form-item label="发件人名称">
          <el-input v-model="configForm.sender_name" placeholder="显示的发件人名称" />
        </el-form-item>
        <el-form-item label="加密方式">
          <el-radio-group v-model="configForm.encryption">
            <el-radio value="tls">TLS</el-radio>
            <el-radio value="ssl">SSL</el-radio>
            <el-radio value="none">无</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="磁盘告警阈值" prop="disk_threshold">
          <el-slider v-model="configForm.disk_threshold" :min="50" :max="99" show-input />
        </el-form-item>
        <el-form-item label="启用告警">
          <el-switch v-model="configForm.is_active" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="configLoading" @click="handleSaveConfig">保存配置</el-button>
          <el-button :loading="testLoading" @click="handleTestEmail">发送测试邮件</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="page-card">
      <div class="card-header">
        <span class="card-title">告警收件人</span>
        <el-button type="primary" :icon="Plus" @click="openRecipientDialog()">添加收件人</el-button>
      </div>
      <el-table :data="recipients" v-loading="recipientLoading" stripe>
        <el-table-column prop="name" label="姓名" width="150" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="添加时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="openRecipientDialog(row)">编辑</el-button>
            <el-button text type="danger" size="small" @click="handleDeleteRecipient(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="recipientDialog" :title="recipientForm.id ? '编辑收件人' : '添加收件人'" width="400px">
      <el-form ref="recipientFormRef" :model="recipientForm" :rules="recipientRules" label-width="80px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="recipientForm.name" placeholder="收件人姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="recipientForm.email" placeholder="收件人邮箱" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="recipientForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="recipientDialog = false">取消</el-button>
        <el-button type="primary" :loading="recipientSubmitLoading" @click="handleSaveRecipient">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="testDialog" title="发送测试邮件" width="400px" :close-on-press-escape="false">
      <el-form ref="testFormRef" :model="testForm" :rules="testRules" label-width="80px" @submit.prevent="handleSendTest">
        <el-form-item label="收件邮箱" prop="recipient_email">
          <el-input v-model="testForm.recipient_email" placeholder="输入测试收件邮箱" @keyup.enter="handleSendTest" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="testDialog = false">取消</el-button>
        <el-button type="primary" :loading="testSendLoading" @click="handleSendTest">发送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAlertConfig, updateAlertConfig, sendTestEmail, getRecipients, createRecipient, updateRecipient, deleteRecipient } from '@/api/alerts'

const configFormRef = ref()
const configLoading = ref(false)
const testLoading = ref(false)
const recipientLoading = ref(false)
const recipientSubmitLoading = ref(false)
const testSendLoading = ref(false)
const recipientDialog = ref(false)
const testDialog = ref(false)
const recipientFormRef = ref()
const testFormRef = ref()
const recipients = ref([])

const configForm = reactive({
  smtp_server: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  sender_email: '',
  sender_name: '巡检系统',
  encryption: 'tls',
  disk_threshold: 80,
  is_active: true
})

const configRules = {
  smtp_server: [{ required: true, message: '请输入SMTP服务器', trigger: 'blur' }],
  smtp_port: [{ required: true, message: '请输入端口', trigger: 'blur' }],
  smtp_username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  sender_email: [
    { required: true, message: '请输入发件人邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  disk_threshold: [{ required: true, message: '请设置阈值', trigger: 'blur' }]
}

const recipientForm = reactive({ id: null, name: '', email: '', is_active: true })
const recipientRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

const testForm = reactive({ recipient_email: '' })
const testRules = {
  recipient_email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

const fetchConfig = async () => {
  const res = await getAlertConfig()
  if (res.success && res.data) {
    Object.assign(configForm, res.data)
    configForm.encryption = res.data.use_ssl ? 'ssl' : (res.data.use_tls ? 'tls' : 'none')
    configForm.smtp_password = ''
  }
}

const fetchRecipients = async () => {
  recipientLoading.value = true
  try {
    const res = await getRecipients()
    if (res.success) recipients.value = res.data
  } finally {
    recipientLoading.value = false
  }
}

const handleSaveConfig = async () => {
  const valid = await configFormRef.value.validate().catch(() => false)
  if (!valid) return

  configLoading.value = true
  try {
    const data = { ...configForm }
    data.use_tls = data.encryption === 'tls'
    data.use_ssl = data.encryption === 'ssl'
    delete data.encryption
    if (!data.smtp_password) delete data.smtp_password

    const res = await updateAlertConfig(data)
    if (res.success) {
      ElMessage.success(res.message)
    } else {
      ElMessage.error(res.message)
    }
  } finally {
    configLoading.value = false
  }
}

const handleTestEmail = () => {
  testForm.recipient_email = ''
  testDialog.value = true
}

const handleSendTest = async () => {
  const valid = await testFormRef.value.validate().catch(() => false)
  if (!valid) return

  testSendLoading.value = true
  try {
    const res = await sendTestEmail(testForm)
    if (res.success) {
      ElMessage.success(res.message)
      testDialog.value = false
    } else {
      ElMessage.error(res.message)
    }
  } finally {
    testSendLoading.value = false
  }
}

const openRecipientDialog = (row = null) => {
  if (row) {
    Object.assign(recipientForm, row)
  } else {
    Object.assign(recipientForm, { id: null, name: '', email: '', is_active: true })
  }
  recipientDialog.value = true
}

const handleSaveRecipient = async () => {
  const valid = await recipientFormRef.value.validate().catch(() => false)
  if (!valid) return

  recipientSubmitLoading.value = true
  try {
    const res = recipientForm.id
      ? await updateRecipient(recipientForm.id, recipientForm)
      : await createRecipient(recipientForm)
    
    if (res.success) {
      ElMessage.success(res.message)
      recipientDialog.value = false
      fetchRecipients()
    } else {
      ElMessage.error(res.message)
    }
  } finally {
    recipientSubmitLoading.value = false
  }
}

const handleDeleteRecipient = (row) => {
  ElMessageBox.confirm(`确定要删除收件人 "${row.name}" 吗？`, '提示', { type: 'warning' })
    .then(async () => {
      const res = await deleteRecipient(row.id)
      if (res.success) {
        ElMessage.success(res.message)
        fetchRecipients()
      } else {
        ElMessage.error(res.message)
      }
    })
    .catch(() => {})
}

onMounted(() => {
  fetchConfig()
  fetchRecipients()
})
</script>
