<template>
  <div class="dashboard-container">
    <div class="page-header">
      <div class="header-titles">
        <h2>
          <el-icon class="dashboard-icon" color="#409eff"><DataAnalysis /></el-icon>
          数据看板
        </h2>
      </div>

      <div class="header-actions">
        <div class="filter-group">
          <el-select
            v-model="filters.model"
            placeholder="全部模型"
            clearable
            filterable
            popper-class="dashboard-select-popper"
            class="filter-select"
            @change="handleFilterChange"
            style="width: 160px"
          >
            <el-option label="全部模型" value="" />
            <el-option
              v-for="model in modelsList"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </div>

        <div class="filter-group">
          <el-select
            v-model="filters.delta_days"
            popper-class="dashboard-select-popper"
            class="filter-select"
            @change="handleFilterChange"
            style="width: 140px"
          >
          <el-option label="全部时间" :value="10000" />
          <el-option label="周内" :value="7" />
          <el-option label="月内" :value="30" />
          <el-option label="年内" :value="365" />
          </el-select>
        </div>
      </div>
    </div>

    <div class="kpi-container">
      <div class="kpi-card kpi-card--primary">
        <div class="kpi-top">
          <div class="kpi-title">总调用次数</div>
          <div class="kpi-icon">☎️</div>
        </div>
        <div class="kpi-value">{{ totalCalls.toLocaleString() }}</div>
        <div class="kpi-desc">{{ periodText }}</div>
      </div>
      <div class="kpi-card kpi-card--warning">
        <div class="kpi-top">
          <div class="kpi-title">总 Token 消耗</div>
          <div class="kpi-icon">Σ</div>
        </div>
        <div class="kpi-value">{{ totalTokens.toLocaleString() }}</div>
        <div class="kpi-desc">输入 + 输出（{{ periodText }}）</div>
      </div>
    </div>

    <div class="charts-container">
      <!-- 调用次数折线图 -->
      <div class="chart-wrapper" v-loading="loading">
        <div class="chart-title">调用次数统计</div>
        <div class="chart-content" ref="callCountChartRef"></div>
        <div class="empty" v-if="!hasCallCountData">暂无数据</div>
      </div>

      <!-- Token使用量柱状图 -->
      <div class="chart-wrapper" v-loading="loading">
        <div class="chart-title">Token使用量统计</div>
        <div class="chart-content" ref="tokenUsageChartRef"></div>
        <div class="empty" v-if="!hasTokenUsageData">暂无数据</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis } from '@element-plus/icons-vue'
// 按需引入 ECharts，避免打包体积和解析问题
import * as echarts from 'echarts/core'
import type { ECharts as EChartsInstance } from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent, DatasetComponent, DataZoomComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
echarts.use([TitleComponent, TooltipComponent, LegendComponent, GridComponent, DatasetComponent, DataZoomComponent, LineChart, BarChart, CanvasRenderer])
import {
  getUsageStatsAPI,
  getUsageCountAPI,
  getUsageModelsAPI,
  getUsageAgentsAPI,
  type UsageStatsRequest,
  type UsageDataByDate,
  type UsageCountByDate
} from '../../apis/usage-stats'

// 筛选条件
const filters = ref<UsageStatsRequest>({
  model: '',
  agent: '',
  delta_days: 10000
})

// 数据列表
const modelsList = ref<string[]>([])
const agentsList = ref<string[]>([])

// 加载状态
const loading = ref(false)

// 图表引用
const callCountChartRef = ref<HTMLElement | null>(null)
const tokenUsageChartRef = ref<HTMLElement | null>(null)

// 图表实例
let callCountChart: EChartsInstance | null = null
let tokenUsageChart: EChartsInstance | null = null

// KPI 与空数据状态
const totalCalls = ref(0)
const totalTokens = ref(0)
const hasCallCountData = ref(true)
const hasTokenUsageData = ref(true)
const periodText = computed(() => {
  const d = Number(filters.value.delta_days || 10000)
  if (d === 7) return '近7天'
  if (d === 30) return '近30天'
  if (d === 365) return '近一年'
  return '全部时间'
})

// 获取模型列表
const fetchModelsList = async () => {
  try {
    const res = await getUsageModelsAPI()
    if (res.data.status_code === 200) {
      modelsList.value = res.data.data || []
    }
  } catch (error) {
    console.error('获取模型列表失败:', error)
  }
}

// 获取智能体列表
const fetchAgentsList = async () => {
  try {
    const res = await getUsageAgentsAPI()
    if (res.data.status_code === 200) {
      agentsList.value = res.data.data || []
    }
  } catch (error) {
    console.error('获取智能体列表失败:', error)
  }
}

// 初始化调用次数折线图
const initCallCountChart = () => {
  if (!callCountChartRef.value) return
  
  if (callCountChart) {
    callCountChart.dispose()
  }
  
  callCountChart = echarts.init(callCountChartRef.value)
  
  const option = {
    color: ['#5B8FF9', '#61DDAA', '#65789B', '#F6BD16', '#7262fd', '#78D3F8'],
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: [],
      top: 0,
      type: 'scroll',
      padding: [10, 20],
      textStyle: { color: '#606266' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: 40,
      top: 65,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: [],
      axisLine: { lineStyle: { color: '#dcdfe6' } },
      axisLabel: { color: '#606266' }
    },
    yAxis: {
      type: 'value',
      name: '调用次数',
      nameTextStyle: { color: '#606266', padding: [0, 0, 0, 20] },
      splitLine: { lineStyle: { color: '#eee' } },
      axisLabel: { color: '#606266' }
    },
    series: []
  }
  
  callCountChart.setOption(option)
}

// 初始化Token使用量柱状图
const initTokenUsageChart = () => {
  if (!tokenUsageChartRef.value) return
  
  if (tokenUsageChart) {
    tokenUsageChart.dispose()
  }
  
  tokenUsageChart = echarts.init(tokenUsageChartRef.value)
  
  const option = {
    color: ['#5AD8A6', '#5B8FF9'],
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const list = Array.isArray(params) ? params : []
        const input = list.find((p: any) => p?.seriesName === '输入Token')?.value || 0
        const output = list.find((p: any) => p?.seriesName === '输出Token')?.value || 0
        const total = Number(input || 0) + Number(output || 0)
        const date = list[0]?.axisValueLabel || ''
        return `${date}<br/>输入Token：${input}<br/>输出Token：${output}<br/><b>总Token：${total}</b>`
      }
    },
    legend: {
      data: ['输入Token', '输出Token'],
      top: 0,
      type: 'scroll',
      padding: [10, 20],
      textStyle: { color: '#606266' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: 40,
      top: 65,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: [],
      axisLine: { lineStyle: { color: '#dcdfe6' } },
      axisLabel: { color: '#606266' }
    },
    yAxis: {
      type: 'value',
      name: 'Token数量',
      nameTextStyle: { color: '#606266', padding: [0, 0, 0, 20] },
      splitLine: { lineStyle: { color: '#eee' } },
      axisLabel: { color: '#606266' }
    },
    series: [
      {
        name: '输入Token',
        type: 'bar',
        stack: 'tokens',
        data: [],
        barMaxWidth: 20,
        itemStyle: {}
      },
      {
        name: '输出Token',
        type: 'bar',
        stack: 'tokens',
        data: [],
        barMaxWidth: 20,
        itemStyle: {},
        label: {
          show: true,
          position: 'top',
          color: '#606266',
          fontWeight: 600,
          formatter: (p: any) => {
            const idx = p.dataIndex
            // 输出柱顶端显示 总Token = 输入 + 输出
            const inputVal = (tokenUsageChart?.getOption()?.series?.[0] as any)?.data?.[idx] || 0
            const outputVal = (tokenUsageChart?.getOption()?.series?.[1] as any)?.data?.[idx] || 0
            return `${Number(inputVal || 0) + Number(outputVal || 0)}`
          }
        }
      }
    ]
  }
  
  tokenUsageChart.setOption(option)
}

// 更新调用次数折线图
const updateCallCountChart = (data: UsageCountByDate) => {
  if (!callCountChart) return
  
  const dates = Object.keys(data).sort()
  const seriesMap = new Map<string, number[]>()
  
  // 根据筛选条件确定数据来源（agent或model）
  const dataKey = filters.value.agent ? 'agent' : 'model'
  
  // 收集所有系列数据
  dates.forEach(date => {
    const dayData = data[date][dataKey]
    Object.entries(dayData).forEach(([name, count]) => {
      if (!seriesMap.has(name)) {
        seriesMap.set(name, new Array(dates.length).fill(0))
      }
      const index = dates.indexOf(date)
      seriesMap.get(name)![index] = count
    })
  })
  
  // 构建图表配置
  const series = Array.from(seriesMap.entries()).map(([name, data]) => ({
    name,
    type: 'line',
    data,
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: { width: 2 },
    areaStyle: {
      opacity: 0.08
    }
  }))
  
  callCountChart.setOption({
    xAxis: {
      data: dates
    },
    legend: {
      data: Array.from(seriesMap.keys())
    },
    series
  })

  hasCallCountData.value = dates.length > 0 && series.length > 0 && series.some(s => (s.data as number[]).some(v => v > 0))
}

// 更新Token使用量柱状图
const updateTokenUsageChart = (data: UsageDataByDate) => {
  if (!tokenUsageChart) return
  
  const dates = Object.keys(data).sort()
  
  // 根据筛选条件确定数据来源（agent或model）
  const dataKey = filters.value.agent ? 'agent' : 'model'
  
  const inputTokens: number[] = []
  const outputTokens: number[] = []
  const totalTokens: number[] = []
  
  // 聚合每天的Token数据
  dates.forEach(date => {
    const dayData = data[date][dataKey]
    let dayInputTotal = 0
    let dayOutputTotal = 0
    let dayTotal = 0
    
    Object.values(dayData).forEach((tokenData: any) => {
      dayInputTotal += tokenData.input_tokens || 0
      dayOutputTotal += tokenData.output_tokens || 0
      dayTotal += tokenData.total_tokens || 0
    })
    
    inputTokens.push(dayInputTotal)
    outputTokens.push(dayOutputTotal)
    totalTokens.push(dayTotal)
  })
  
  tokenUsageChart.setOption({
    xAxis: {
      data: dates
    },
    series: [
      {
        name: '输入Token',
        data: inputTokens
      },
      {
        name: '输出Token',
        data: outputTokens
      }
    ]
  })

  hasTokenUsageData.value = dates.length > 0 && (inputTokens.some(v => v > 0) || outputTokens.some(v => v > 0))
}

// 获取使用统计数据
const fetchUsageData = async () => {
  loading.value = true
  
  try {
    const params: UsageStatsRequest = {
      agent: filters.value.agent || undefined,
      model: filters.value.model || undefined,
      delta_days: filters.value.delta_days
    }
    
    // 获取调用次数数据
    const countRes = await getUsageCountAPI(params)
    if (countRes.data.status_code === 200) {
      updateCallCountChart(countRes.data.data)
      // 累计调用次数（使用显式遍历避免 unknown 类型问题）
      const dk: 'agent' | 'model' = (filters.value.agent ? 'agent' : 'model')
      let calls = 0
      const dayList = Object.values(countRes.data.data || {}) as Array<any>
      for (const day of dayList) {
        const map = (day?.[dk] || {}) as Record<string, number>
        for (const v of Object.values(map)) calls += Number(v || 0)
      }
      totalCalls.value = calls
    }
    
    // 获取Token使用量数据
    const statsRes = await getUsageStatsAPI(params)
    if (statsRes.data.status_code === 200) {
      updateTokenUsageChart(statsRes.data.data)
      // 累计Token（使用显式遍历避免 unknown 类型问题）
      const dk: 'agent' | 'model' = (filters.value.agent ? 'agent' : 'model')
      let tokens = 0
      const dayList = Object.values(statsRes.data.data || {}) as Array<any>
      for (const day of dayList) {
        const map = (day?.[dk] || {}) as Record<string, { total_tokens?: number }>
        for (const obj of Object.values(map)) tokens += Number(obj?.total_tokens || 0)
      }
      totalTokens.value = tokens
    }
  } catch (error) {
    console.error('获取使用统计数据失败:', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 筛选条件变化
const handleFilterChange = () => {
  fetchUsageData()
}

// 窗口大小变化处理
const handleResize = () => {
  callCountChart?.resize()
  tokenUsageChart?.resize()
}

// 初始化
onMounted(async () => {
  await nextTick()
  
  // 获取筛选列表
  await Promise.all([
    fetchModelsList(),
    fetchAgentsList()
  ])
  
  // 初始化图表
  initCallCountChart()
  initTokenUsageChart()
  
  // 加载数据
  await fetchUsageData()
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

// 清理
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  
  if (callCountChart) {
    callCountChart.dispose()
    callCountChart = null
  }
  
  if (tokenUsageChart) {
    tokenUsageChart.dispose()
    tokenUsageChart = null
  }
})
</script>

<style scoped lang="scss">
.dashboard-container {
  padding: 30px;
  background-color: #ffffff;
  min-height: calc(100vh - 60px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  background: linear-gradient(to right, #ffffff, #f8fafc);
  padding: 28px;
  border-radius: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;

  h2 {
    font-size: 26px;
    font-weight: 700;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 12px;
    background: linear-gradient(90deg, #409eff, #3a7be2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    
    .dashboard-icon {
      font-size: 30px;
      color: #409eff;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
    }
  }

  .header-actions {
    display: flex;
    align-items: stretch;
    gap: 16px;
    flex-wrap: wrap;
  }
}

.filter-group {
  display: flex;
  align-items: center;
}

/* Select 美化 (适用 Element Plus 2.6+) */
.filter-select :deep(.el-select__wrapper) {
  border-radius: 100px !important;
  box-shadow: 0 0 0 1px #dcdfe6 inset !important;
  transition: all .3s cubic-bezier(0.4, 0, 0.2, 1);
  background: #ffffff;
  padding: 8px 20px !important;
  min-height: 40px !important;
  height: 40px !important;
}
.filter-select :deep(.el-select__placeholder),
.filter-select :deep(.el-select__selected-item) {
  color: #475569;
  font-size: 14px;
  line-height: 1.2;
}
.filter-select :deep(.el-select__wrapper.is-hovering),
.filter-select :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #a8abb2 inset !important;
}
.filter-select :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 1.5px #409eff inset, 0 0 0 3px rgba(64, 158, 255, 0.15) !important;
}
.filter-select :deep(.el-select__caret) {
  color: #94a3b8;
  font-size: 16px;
}

/* 下拉项美化 */
.dashboard-select-popper {
  border-radius: 16px !important;
  box-shadow: 0 12px 32px rgba(0,0,0,.08) !important;
  border: 1px solid #eef0f4 !important;
  padding: 6px !important;
}
.dashboard-select-popper :deep(.el-select-dropdown__item) {
  padding: 10px 12px;
  border-radius: 10px;
  margin: 2px 4px;
  font-weight: 500;
  color: #475569;
}
.dashboard-select-popper :deep(.el-select-dropdown__item.hover),
.dashboard-select-popper :deep(.el-select-dropdown__item:hover) {
  background: #f1f5f9;
  color: #1e293b;
}
.dashboard-select-popper :deep(.el-select-dropdown__item.selected) {
  background: linear-gradient(135deg, #eff6ff 0%, #e0f2fe 100%);
  color: #2563eb;
  font-weight: 600;
}

.kpi-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 28px;
}

.kpi-card {
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #eef0f4;
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05);
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  }

  .kpi-title {
    font-size: 14px;
    font-weight: 600;
    color: #64748b;
    margin-bottom: 6px;
  }
  .kpi-value {
    font-size: 32px;
    font-weight: 700;
    color: #1e293b;
    line-height: 1.2;
    letter-spacing: -0.02em;
  }
  .kpi-desc {
    margin-top: 8px;
    font-size: 13px;
    color: #94a3b8;
    font-weight: 500;
  }
  .kpi-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  .kpi-icon {
    width: 44px;
    height: 44px;
    border-radius: 16px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
    color: #4f46e5;
    font-size: 20px;
    font-weight: 800;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
  }
}

.kpi-card--primary {
  background: linear-gradient(180deg, #ffffff 0%, #f0f9ff 100%);
  border-color: #e0f2fe;
  .kpi-icon {
    background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
    color: #0284c7;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.15);
  }
}
.kpi-card--warning {
  background: linear-gradient(180deg, #ffffff 0%, #fff7ed 100%);
  border-color: #ffedd5;
  .kpi-icon {
    background: linear-gradient(135deg, #ffedd5 0%, #fed7aa 100%);
    color: #ea580c;
    box-shadow: 0 4px 12px rgba(234, 88, 12, 0.15);
  }
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
  gap: 24px;
}

.chart-wrapper {
  background-color: #ffffff;
  border-radius: 24px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05);
  padding: 24px;
  min-height: 400px;
  position: relative;
  border: 1px solid #eef0f4;
  transition: all 0.3s ease;
  
  &:hover {
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  }
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #e2e8f0;
}

.chart-content {
  width: 100%;
  height: 350px;
}

.empty {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a8abb2;
  font-size: 13px;
  pointer-events: none;
}

@media (max-width: 1400px) {
  .charts-container {
    grid-template-columns: 1fr;
  }
}
</style>

