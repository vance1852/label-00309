<template>
  <div class="schedule">
    <div class="page-card">
      <div class="card-header">
        <span class="card-title">巡检调度配置</span>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" style="max-width: 600px;" v-loading="loading">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="巡检周期" prop="interval_type">
          <el-select v-model="form.interval_type" style="width: 100%">
            <el-option label="每小时" value="hourly" />
            <el-option label="每天" value="daily" />
            <el-option label="每周" value="weekly" />
            <el-option label="每月" value="monthly" />
          </el-select>
        </el-form-item>
        <el-form-item label="间隔" prop="interval_value">
          <el-input-number v-model="form.interval_value" :min="1" :max="30" style="width: 100%" />
          <div class="el-form-item__tip">每隔 {{ form.interval_value }} 个{{ intervalLabel }}执行一次</div>
        </el-form-item>
        <el-form-item label="执行时间" prop="execute_time" v-if="form.interval_type !== 'hourly'">
          <el-time-picker v-model="form.execute_time" format="HH:mm" value-format="HH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="执行日" prop="execute_day" v-if="form.interval_type === 'weekly'">
          <el-select v-model="form.execute_day" style="width: 100%">
            <el-option v-for="d in 7" :key="d" :label="weekDays[d-1]" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="执行日" prop="execute_day" v-if="form.interval_type === 'monthly'">
          <el-select v-model="form.execute_day" style="width: 100%">
            <el-option v-for="d in 28" :key="d" :label="`每月${d}号`" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="巡检命令" prop="inspection_command">
          <el-input v-model="form.inspection_command" type="textarea" :rows="3" placeholder="df -h" />
          <div class="el-form-item__tip">默认使用 df -h 查看磁盘使用情况</div>
        </el-form-item>
        <el-form-item label="启用调度">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item label="上次执行" v-if="form.last_run">
          <span>{{ form.last_run }}</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitLoading" @click="handleSave">保存配置</el-button>
          <el-button type="success" :loading="runLoading" @click="handleRunNow">立即执行</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="page-card">
      <div class="card-header">
        <span class="card-title">调度说明</span>
      </div>
      <el-alert type="info" :closable="false" show-icon>
        <template #title>
          <div>
            <p>1. 定时巡检任务会在设定的时间自动执行，对所有启用的服务器进行磁盘检查</p>
            <p>2. 如果磁盘使用率超过告警阈值，系统会自动发送告警邮件</p>
            <p>3. 巡检命令默认为 <code>df -h</code>，可根据需要修改</p>
            <p>4. 点击"立即执行"可手动触发一次巡检</p>
          </div>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSchedule, updateSchedule, runNow } from '@/api/schedule'

const loading = ref(false)
const submitLoading = ref(false)
const runLoading = ref(false)
const formRef = ref()

const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const form = reactive({
  name: '定时巡检',
  interval_type: 'daily',
  interval_value: 1,
  execute_time: '02:00:00',
  execute_day: 1,
  inspection_command: 'df -h',
  is_active: true,
  last_run: null
})

const rules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  interval_type: [{ required: true, message: '请选择周期类型', trigger: 'change' }],
  interval_value: [{ required: true, message: '请输入间隔', trigger: 'blur' }],
  inspection_command: [{ required: true, message: '请输入巡检命令', trigger: 'blur' }]
}

const intervalLabel = computed(() => {
  const map = { hourly: '小时', daily: '天', weekly: '周', monthly: '月' }
  return map[form.interval_type] || '天'
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getSchedule()
    if (res.success && res.data) {
      Object.assign(form, res.data)
    }
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    const res = await updateSchedule(form)
    if (res.success) {
      ElMessage.success(res.message)
    } else {
      ElMessage.error(res.message)
    }
  } finally {
    submitLoading.value = false
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

onMounted(fetchData)
</script>

<style scoped>
.el-form-item__tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}
</style>
