<template>
  <n-space vertical size="large">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
      <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('pro.dashboard.title') }}</h1>
      <n-button @click="showProfileModal = true">{{ t('pro.profile.title') }}</n-button>
    </div>

    <!-- Loading State -->
    <div v-if="proStore.loading" style="text-align: center; padding: 40px;">
      <n-spin size="large" />
    </div>

    <template v-else>
      <!-- Setup Profile Alert -->
      <n-card v-if="proStore.proProfile && !proStore.proProfile.siret" size="small" style="border-left: 3px solid #2080f0;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
          <div>
            <strong>{{ t('pro.dashboard.setupProfile') }}</strong>
            <div style="font-size: 13px; color: rgba(255,255,255,0.6); margin-top: 4px;">{{ t('pro.dashboard.setupProfileDesc') }}</div>
          </div>
          <n-button size="small" type="primary" @click="showProfileModal = true">{{ t('pro.profile.title') }}</n-button>
        </div>
      </n-card>

      <!-- Summary Stats -->
      <n-grid :cols="isMobile ? 2 : 3" :x-gap="12" :y-gap="12">
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.dashboard.caMonth')" :value="summary.ca_month.toFixed(2)">
              <template #prefix><n-icon color="#18a058"><TrendingUpOutline /></n-icon></template>
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.dashboard.caQuarter')" :value="summary.ca_quarter.toFixed(2)">
              <template #prefix><n-icon color="#18a058"><TrendingUpOutline /></n-icon></template>
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.dashboard.caYear')" :value="summary.ca_year.toFixed(2)">
              <template #prefix><n-icon color="#18a058"><TrendingUpOutline /></n-icon></template>
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.dashboard.expensesMonth')" :value="summary.expenses_month.toFixed(2)">
              <template #prefix><n-icon color="#d03050"><TrendingDownOutline /></n-icon></template>
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.dashboard.netMonth')" :value="summary.net_month.toFixed(2)">
              <template #prefix><n-icon :color="summary.net_month >= 0 ? '#18a058' : '#d03050'"><WalletOutline /></n-icon></template>
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small">
            <n-statistic :label="t('pro.dashboard.cotisationsMonth')" :value="summary.cotisations_estimated.toFixed(2)">
              <template #prefix><n-icon color="#f0a020"><CashOutline /></n-icon></template>
              <template #suffix>€</template>
            </n-statistic>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- Threshold Progress -->
      <n-card :title="t('pro.dashboard.thresholdProgress')" size="small">
        <div style="display: flex; align-items: center; gap: 12px;">
          <n-progress
            type="line"
            :percentage="Math.min(summary.threshold_percentage, 100)"
            :color="summary.threshold_percentage > 90 ? '#d03050' : summary.threshold_percentage > 70 ? '#f0a020' : '#18a058'"
            :rail-color="'rgba(255,255,255,0.1)'"
            style="flex: 1;"
          />
          <span style="white-space: nowrap; font-size: 13px;">
            {{ summary.ca_year.toFixed(0) }}€ / {{ threshold.toFixed(0) }}€
          </span>
        </div>
      </n-card>

      <!-- Tracked limits (user-defined thresholds from pro_thresholds) -->
      <n-card v-if="trackedLimits.length > 0" :title="t('pro.dashboard.trackedLimits')" size="small">
        <n-space vertical :size="10">
          <div v-for="lim in trackedLimits" :key="lim.id" class="tracked-limit-row">
            <div class="tracked-limit-header">
              <span class="dot" :style="{ background: lim.color }" />
              <strong>{{ lim.name }}</strong>
              <n-tag size="tiny" type="info">{{ t(`pro.thresholds.period.${lim.period}`) }}</n-tag>
              <span class="amount-text">{{ lim.current.toFixed(0) }} € / {{ lim.amount.toFixed(0) }} €</span>
              <span class="pct-text" :style="{ color: lim.colorClass }">{{ lim.rawPercentage.toFixed(0) }} %</span>
            </div>
            <n-progress
              type="line"
              :percentage="lim.percentage"
              :color="lim.colorClass"
              :rail-color="'rgba(255,255,255,0.1)'"
              :show-indicator="false"
            />
          </div>
        </n-space>
      </n-card>

      <!-- VAT summary (only when subject to VAT) -->
      <n-card v-if="vatSummary && vatSummary.is_subject_to_vat === 1" :title="t('pro.vat.title')" size="small">
        <template #header-extra>
          <n-radio-group v-model:value="vatPeriod" size="small">
            <n-radio-button value="month">{{ t('pro.charts.monthly') }}</n-radio-button>
            <n-radio-button value="quarter">{{ t('pro.charts.quarterly') }}</n-radio-button>
            <n-radio-button value="year">{{ t('pro.tax.yearly') }}</n-radio-button>
          </n-radio-group>
        </template>
        <n-grid :cols="isMobile ? 1 : 3" :x-gap="12">
          <n-gi>
            <div class="vat-stat">
              <div class="vat-label">{{ t('pro.vat.collected') }}</div>
              <div class="vat-value" style="color: #18a058;">{{ vatSummary.collected.toFixed(2) }} €</div>
            </div>
          </n-gi>
          <n-gi>
            <div class="vat-stat">
              <div class="vat-label">{{ t('pro.vat.deductible') }}</div>
              <div class="vat-value" style="color: #2080f0;">{{ vatSummary.deductible.toFixed(2) }} €</div>
            </div>
          </n-gi>
          <n-gi>
            <div class="vat-stat">
              <div class="vat-label">
                {{ vatSummary.balance >= 0 ? t('pro.vat.toPay') : t('pro.vat.toRefund') }}
              </div>
              <div class="vat-value" :style="{ color: vatSummary.balance >= 0 ? '#d03050' : '#18a058' }">
                {{ Math.abs(vatSummary.balance).toFixed(2) }} €
              </div>
            </div>
          </n-gi>
        </n-grid>
        <div v-for="(note, i) in vatSummary.notes" :key="i" class="vat-note">
          ⓘ {{ note }}
        </div>
      </n-card>

      <!-- Tax breakdown -->
      <n-card :title="t('pro.tax.estimated')" size="small">
        <template #header-extra>
          <n-space size="small">
            <n-radio-group v-model:value="breakdownPeriod" size="small">
              <n-radio-button value="month">{{ t('pro.charts.monthly') }}</n-radio-button>
              <n-radio-button value="quarter">{{ t('pro.charts.quarterly') }}</n-radio-button>
              <n-radio-button value="year">{{ t('pro.tax.yearly') }}</n-radio-button>
            </n-radio-group>
            <n-select
              v-if="breakdownPeriod === 'year'"
              v-model:value="breakdownYear"
              :options="yearOptions"
              size="small"
              style="width: 100px;"
            />
            <n-button size="small" @click="openCompareModal">{{ t('pro.tax.compareRegimes') }}</n-button>
          </n-space>
        </template>
        <div v-if="!breakdown" style="opacity: 0.6;">{{ t('pro.tax.loading') }}</div>
        <div v-else>
          <n-grid :cols="isMobile ? 1 : 2" :x-gap="12" :y-gap="6">
            <n-gi>
              <div class="tax-row">
                <span>{{ t('pro.tax.turnover') }}</span>
                <strong>{{ breakdown.turnover.toFixed(2) }} €</strong>
              </div>
            </n-gi>
            <n-gi v-if="breakdown.deductible_expenses > 0">
              <div class="tax-row">
                <span>{{ t('pro.tax.deductibleExpenses') }}</span>
                <strong>{{ breakdown.deductible_expenses.toFixed(2) }} €</strong>
              </div>
            </n-gi>
            <n-gi v-if="breakdown.benefice_imposable != null">
              <div class="tax-row">
                <span>{{ t('pro.tax.beneficeImposable') }}</span>
                <strong>{{ breakdown.benefice_imposable.toFixed(2) }} €</strong>
              </div>
            </n-gi>
            <n-gi v-if="breakdown.net_salary != null">
              <div class="tax-row">
                <span>{{ t('pro.tax.netSalary') }}</span>
                <strong style="color: #18a058;">{{ breakdown.net_salary.toFixed(2) }} €</strong>
              </div>
            </n-gi>
            <n-gi>
              <div class="tax-row">
                <span>{{ t('pro.tax.cotisations') }}</span>
                <strong>{{ breakdown.cotisations_sociales.toFixed(2) }} €</strong>
              </div>
            </n-gi>
            <n-gi v-if="breakdown.cfp > 0">
              <div class="tax-row">
                <span>{{ t('pro.tax.cfp') }}</span>
                <strong>{{ breakdown.cfp.toFixed(2) }} €</strong>
              </div>
            </n-gi>
            <n-gi v-if="breakdown.ir_versement_liberatoire != null">
              <div class="tax-row">
                <span>{{ t('pro.tax.irVL') }}</span>
                <strong>{{ breakdown.ir_versement_liberatoire.toFixed(2) }} €</strong>
              </div>
            </n-gi>
            <n-gi v-if="breakdown.ir_classique_estime != null">
              <div class="tax-row">
                <span>{{ t('pro.tax.irClassique') }}</span>
                <strong>{{ breakdown.ir_classique_estime.toFixed(2) }} €</strong>
              </div>
            </n-gi>
            <n-gi v-if="breakdown.impot_societes != null">
              <div class="tax-row">
                <span>{{ t('pro.tax.is') }}</span>
                <strong>{{ breakdown.impot_societes.toFixed(2) }} €</strong>
              </div>
            </n-gi>
            <n-gi v-if="breakdown.dividendes_taxes != null && breakdown.dividendes_taxes > 0">
              <div class="tax-row">
                <span>{{ t('pro.tax.dividends') }}</span>
                <strong>{{ breakdown.dividendes_taxes.toFixed(2) }} €</strong>
              </div>
            </n-gi>
          </n-grid>
          <n-divider style="margin: 8px 0;" />
          <div class="tax-row" style="font-size: 15px;">
            <strong>{{ t('pro.tax.totalPrelevements') }}</strong>
            <strong style="color: #f0a020;">{{ breakdown.total_prelevements.toFixed(2) }} €</strong>
          </div>
          <div class="tax-row">
            <span>{{ t('pro.tax.netAfterTaxes') }}</span>
            <strong :style="{ color: breakdown.net_after_taxes >= 0 ? '#18a058' : '#d03050' }">
              {{ breakdown.net_after_taxes.toFixed(2) }} €
            </strong>
          </div>
          <div class="tax-row" style="font-size: 15px; padding-top: 6px;">
            <strong>{{ t('pro.tax.personalTakeHome') }}</strong>
            <strong :style="{ color: breakdown.personal_take_home >= 0 ? '#18a058' : '#d03050' }">
              {{ breakdown.personal_take_home.toFixed(2) }} €
            </strong>
          </div>
          <div v-for="(note, i) in breakdown.notes" :key="i" style="margin-top: 8px; font-size: 12px; opacity: 0.7;">
            ⓘ {{ note }}
          </div>
          <div v-if="regimeHint" class="regime-hint" @click="openCompareModal">
            💡 {{ regimeHint }}
          </div>
        </div>
      </n-card>

      <!-- Recent Transactions -->
      <n-card :title="t('pro.dashboard.recentTransactions')" size="small">
        <n-empty v-if="proStore.proTransactions.length === 0" :description="t('pro.transactions.noTransactions')" />
        <n-list v-else>
          <n-list-item v-for="tx in recentTransactions" :key="tx.id">
            <n-thing>
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span>{{ tx.title }}</span>
                  <span :style="{ color: tx.transaction_type === 'income' ? '#18a058' : '#d03050', fontWeight: 'bold' }">
                    {{ tx.transaction_type === 'income' ? '+' : '-' }}{{ tx.amount.toFixed(2) }} €
                  </span>
                </div>
              </template>
              <template #description>
                <n-space size="small">
                  <n-tag size="tiny" :type="tx.transaction_type === 'income' ? 'success' : 'error'">
                    {{ tx.category_name }}
                  </n-tag>
                  <span style="color: rgba(255,255,255,0.5); font-size: 12px;">{{ tx.date }}</span>
                  <span v-if="tx.client_name" style="color: rgba(255,255,255,0.5); font-size: 12px;">· {{ tx.client_name }}</span>
                </n-space>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-card>
    </template>

    <!-- Profile Modal -->
    <n-modal v-model:show="showProfileModal" preset="card" :title="t('pro.profile.title')" style="max-width: 550px; max-height: 85vh; overflow-y: auto;">
      <n-form>
        <!-- Company Info -->
        <n-divider style="margin: 0 0 16px;">{{ t('pro.profile.companySection') }}</n-divider>
        <n-form-item :label="t('pro.profile.companyName')">
          <n-input v-model:value="profileForm.company_name" :placeholder="t('pro.profile.companyNamePlaceholder')" />
        </n-form-item>
        <n-form-item :label="t('pro.profile.companyAddress')">
          <n-input v-model:value="profileForm.company_address" type="textarea" :rows="2" :placeholder="t('pro.profile.companyAddressPlaceholder')" />
        </n-form-item>
        <n-form-item :label="t('pro.profile.companyEmail')">
          <n-input v-model:value="profileForm.company_email" placeholder="contact@entreprise.fr" />
        </n-form-item>
        <n-form-item :label="t('pro.profile.companyPhone')">
          <n-input v-model:value="profileForm.company_phone" placeholder="06 12 34 56 78" />
        </n-form-item>
        <n-form-item :label="t('pro.profile.siret')">
          <n-input v-model:value="profileForm.siret" :placeholder="t('pro.profile.siret')" />
        </n-form-item>

        <!-- Legal Form -->
        <n-divider style="margin: 8px 0 16px;">{{ t('pro.profile.regimeSection') }}</n-divider>
        <n-form-item :label="t('pro.profile.legalForm')">
          <n-select v-model:value="profileForm.legal_form" :options="legalFormOptions" />
        </n-form-item>

        <!-- Micro: full activity & cotisations + IR options -->
        <template v-if="profileForm.legal_form === 'micro'">
          <n-divider style="margin: 8px 0 16px;">{{ t('pro.profile.activitySection') }}</n-divider>
          <n-form-item :label="t('pro.profile.activityType')">
            <n-select :value="profileForm.activity_type" :options="activityTypeOptions" @update:value="onActivityTypeChange" />
          </n-form-item>
          <n-form-item :label="t('pro.profile.cotisationRate')">
            <n-input-number v-model:value="profileForm.cotisation_rate" :min="0" :max="100" :precision="1" style="width: 100%;" />
          </n-form-item>
          <n-form-item :label="t('pro.profile.cfpRate')">
            <n-input-number v-model:value="profileForm.cfp_rate" :min="0" :max="10" :precision="3" :placeholder="t('pro.profile.cfpAuto')" style="width: 100%;">
              <template #suffix>%</template>
            </n-input-number>
          </n-form-item>
          <n-form-item :label="t('pro.profile.declarationFrequency')">
            <n-select v-model:value="profileForm.declaration_frequency" :options="frequencyOptions" />
          </n-form-item>
          <n-form-item :label="t('pro.profile.revenueThreshold')">
            <n-input-number v-model:value="profileForm.revenue_threshold" :min="0" :precision="0" style="width: 100%;">
              <template #suffix>€</template>
            </n-input-number>
          </n-form-item>

          <n-divider style="margin: 8px 0 16px;">{{ t('pro.profile.irSection') }}</n-divider>
          <n-form-item :label="t('pro.profile.versementLiberatoire')">
            <n-switch :value="profileForm.versement_liberatoire_enabled === 1" @update:value="(v: boolean) => profileForm.versement_liberatoire_enabled = v ? 1 : 0" />
          </n-form-item>
          <n-form-item v-if="profileForm.versement_liberatoire_enabled === 1" :label="t('pro.profile.versementLiberatoireRate')">
            <n-input-number v-model:value="profileForm.versement_liberatoire_rate" :min="0" :max="10" :precision="2" :placeholder="t('pro.profile.cfpAuto')" style="width: 100%;">
              <template #suffix>%</template>
            </n-input-number>
          </n-form-item>
          <template v-if="profileForm.versement_liberatoire_enabled === 0">
            <n-form-item :label="t('pro.profile.irAbattement')">
              <n-input-number v-model:value="profileForm.ir_abattement_rate" :min="0" :max="100" :precision="0" :placeholder="t('pro.profile.cfpAuto')" style="width: 100%;">
                <template #suffix>%</template>
              </n-input-number>
            </n-form-item>
            <n-form-item :label="t('pro.profile.foyerTmi')">
              <n-input-number v-model:value="profileForm.foyer_tmi" :min="0" :max="50" :precision="0" :placeholder="t('pro.profile.foyerTmiPlaceholder')" style="width: 100%;">
                <template #suffix>%</template>
              </n-input-number>
            </n-form-item>
          </template>
        </template>

        <!-- EI au réel & EURL: TNS rate + TMI (always for IR) -->
        <template v-if="profileForm.legal_form === 'ei_reel' || profileForm.legal_form === 'eurl'">
          <n-divider style="margin: 8px 0 16px;">{{ t('pro.profile.realRegimeSection') }}</n-divider>
          <n-form-item v-if="profileForm.legal_form === 'eurl'" :label="t('pro.profile.eurlTaxOption')">
            <n-radio-group v-model:value="profileForm.eurl_tax_option">
              <n-radio-button value="ir">{{ t('pro.profile.eurlIR') }}</n-radio-button>
              <n-radio-button value="is">{{ t('pro.profile.eurlIS') }}</n-radio-button>
            </n-radio-group>
          </n-form-item>
          <template v-if="profileForm.legal_form === 'ei_reel' || profileForm.eurl_tax_option === 'ir'">
            <n-form-item :label="t('pro.profile.tnsCotisationsRate')">
              <n-input-number v-model:value="profileForm.tns_cotisations_rate" :min="0" :max="100" :precision="1" style="width: 100%;">
                <template #suffix>%</template>
              </n-input-number>
            </n-form-item>
            <n-form-item :label="t('pro.profile.foyerTmi')">
              <n-input-number v-model:value="profileForm.foyer_tmi" :min="0" :max="50" :precision="0" :placeholder="t('pro.profile.foyerTmiPlaceholder')" style="width: 100%;">
                <template #suffix>%</template>
              </n-input-number>
            </n-form-item>
          </template>
        </template>

        <!-- Incorporated (SASU, SAS, EURL-IS): salary + IS + dividends -->
        <template v-if="isIncorporated">
          <n-divider style="margin: 8px 0 16px;">{{ t('pro.profile.incorporatedSection') }}</n-divider>
          <n-form-item :label="t('pro.profile.salaryGrossMonthly')">
            <n-input-number v-model:value="profileForm.salary_gross_monthly" :min="0" :precision="0" style="width: 100%;">
              <template #suffix>€</template>
            </n-input-number>
          </n-form-item>
          <n-form-item v-if="profileForm.legal_form === 'eurl'" :label="t('pro.profile.tnsCotisationsRate')">
            <n-input-number v-model:value="profileForm.tns_cotisations_rate" :min="0" :max="100" :precision="1" style="width: 100%;">
              <template #suffix>%</template>
            </n-input-number>
          </n-form-item>
          <n-form-item :label="t('pro.profile.dividendsYearly')">
            <n-input-number v-model:value="profileForm.dividends_yearly" :min="0" :precision="0" style="width: 100%;">
              <template #suffix>€</template>
            </n-input-number>
          </n-form-item>
        </template>

        <!-- TVA -->
        <n-divider style="margin: 8px 0 16px;">TVA</n-divider>
        <n-form-item :label="t('pro.profile.isSubjectToVat')">
          <n-switch :value="profileForm.is_subject_to_vat === 1" @update:value="(v: boolean) => profileForm.is_subject_to_vat = v ? 1 : 0" />
        </n-form-item>
        <template v-if="profileForm.is_subject_to_vat === 1">
          <n-form-item :label="t('pro.profile.vatRate')">
            <n-input-number v-model:value="profileForm.vat_rate" :min="0" :max="100" :precision="1" style="width: 100%;">
              <template #suffix>%</template>
            </n-input-number>
          </n-form-item>
          <n-form-item :label="t('pro.profile.vatNumber')">
            <n-input v-model:value="profileForm.vat_number" placeholder="FR XX XXXXXXXXX" />
          </n-form-item>
        </template>

        <n-button type="primary" block @click="saveProfile" style="margin-top: 16px;">{{ t('common.save') }}</n-button>
      </n-form>
    </n-modal>

    <!-- Regime Comparison Modal -->
    <n-modal v-model:show="showCompareModal" preset="card" :title="t('pro.tax.compareRegimes')" style="max-width: 900px;">
      <n-space vertical>
        <n-space size="small">
          <n-radio-group v-model:value="comparePeriod" size="small">
            <n-radio-button value="month">{{ t('pro.charts.monthly') }}</n-radio-button>
            <n-radio-button value="quarter">{{ t('pro.charts.quarterly') }}</n-radio-button>
            <n-radio-button value="year">{{ t('pro.tax.yearly') }}</n-radio-button>
          </n-radio-group>
          <n-select
            v-if="comparePeriod === 'year'"
            v-model:value="compareYear"
            :options="yearOptions"
            size="small"
            style="width: 100px;"
          />
        </n-space>

        <div v-if="comparisonRows.length === 0" style="opacity: 0.6; padding: 16px 0;">{{ t('pro.tax.loading') }}</div>

        <div v-else style="overflow-x: auto;">
          <table class="regime-compare">
            <thead>
              <tr>
                <th></th>
                <th
                  v-for="row in comparisonRows"
                  :key="row.regime"
                  :class="{ 'current': row.regime === currentRegimeKey, 'best': row.regime === bestRegimeKey }"
                >
                  {{ t(`pro.tax.regimeLabels.${row.regime}`) }}
                  <div v-if="row.regime === currentRegimeKey" class="badge">{{ t('pro.tax.current') }}</div>
                  <div v-else-if="row.regime === bestRegimeKey" class="badge best-badge">{{ t('pro.tax.lowest') }}</div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th>{{ t('pro.tax.turnover') }}</th>
                <td v-for="row in comparisonRows" :key="row.regime">{{ row.breakdown.turnover.toFixed(0) }} €</td>
              </tr>
              <tr>
                <th>{{ t('pro.tax.deductibleExpenses') }}</th>
                <td v-for="row in comparisonRows" :key="row.regime">{{ row.breakdown.deductible_expenses.toFixed(0) }} €</td>
              </tr>
              <tr>
                <th>{{ t('pro.tax.beneficeImposable') }}</th>
                <td v-for="row in comparisonRows" :key="row.regime">
                  {{ row.breakdown.benefice_imposable != null ? row.breakdown.benefice_imposable.toFixed(0) + ' €' : '—' }}
                </td>
              </tr>
              <tr>
                <th>{{ t('pro.tax.netSalary') }}</th>
                <td v-for="row in comparisonRows" :key="row.regime">
                  {{ row.breakdown.net_salary != null ? row.breakdown.net_salary.toFixed(0) + ' €' : '—' }}
                </td>
              </tr>
              <tr>
                <th>{{ t('pro.tax.cotisations') }}</th>
                <td v-for="row in comparisonRows" :key="row.regime">{{ row.breakdown.cotisations_sociales.toFixed(0) }} €</td>
              </tr>
              <tr>
                <th>{{ t('pro.tax.cfp') }}</th>
                <td v-for="row in comparisonRows" :key="row.regime">{{ row.breakdown.cfp.toFixed(0) }} €</td>
              </tr>
              <tr>
                <th>{{ t('pro.tax.irVL') }}</th>
                <td v-for="row in comparisonRows" :key="row.regime">
                  {{ row.breakdown.ir_versement_liberatoire != null ? row.breakdown.ir_versement_liberatoire.toFixed(0) + ' €' : '—' }}
                </td>
              </tr>
              <tr>
                <th>{{ t('pro.tax.irClassique') }}</th>
                <td v-for="row in comparisonRows" :key="row.regime">
                  {{ row.breakdown.ir_classique_estime != null ? row.breakdown.ir_classique_estime.toFixed(0) + ' €' : '—' }}
                </td>
              </tr>
              <tr>
                <th>{{ t('pro.tax.is') }}</th>
                <td v-for="row in comparisonRows" :key="row.regime">
                  {{ row.breakdown.impot_societes != null ? row.breakdown.impot_societes.toFixed(0) + ' €' : '—' }}
                </td>
              </tr>
              <tr>
                <th>{{ t('pro.tax.dividends') }}</th>
                <td v-for="row in comparisonRows" :key="row.regime">
                  {{ row.breakdown.dividendes_taxes != null ? row.breakdown.dividendes_taxes.toFixed(0) + ' €' : '—' }}
                </td>
              </tr>
              <tr class="total">
                <th>{{ t('pro.tax.totalPrelevements') }}</th>
                <td
                  v-for="row in comparisonRows"
                  :key="row.regime"
                  :class="{ 'best': row.regime === bestRegimeKey }"
                >
                  {{ row.breakdown.total_prelevements.toFixed(0) }} €
                </td>
              </tr>
              <tr class="net">
                <th>{{ t('pro.tax.netAfterTaxes') }}</th>
                <td v-for="row in comparisonRows" :key="row.regime">
                  {{ row.breakdown.net_after_taxes.toFixed(0) }} €
                </td>
              </tr>
              <tr class="net take-home">
                <th>{{ t('pro.tax.personalTakeHome') }}</th>
                <td
                  v-for="row in comparisonRows"
                  :key="row.regime"
                  :class="{ 'best': row.regime === bestRegimeKey }"
                >
                  {{ row.breakdown.personal_take_home.toFixed(0) }} €
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div style="font-size: 12px; opacity: 0.7;">
          ⓘ {{ t('pro.tax.compareNote') }}
        </div>
      </n-space>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  NSpace, NCard, NGrid, NGi, NStatistic, NIcon, NProgress,
  NList, NListItem, NThing, NTag, NEmpty, NButton, NRadioGroup, NRadioButton,
  NModal, NForm, NFormItem, NInput, NInputNumber, NSelect, NSwitch, NDivider, NSpin
} from 'naive-ui'
import { TrendingUpOutline, TrendingDownOutline, WalletOutline, CashOutline } from '@vicons/ionicons5'
import { useI18n } from 'vue-i18n'
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'
import { proProfileAPI, type TaxBreakdown, type RegimeComparisonRow, type VatSummary } from '@/services/api'

const { t } = useI18n()
const proStore = useProStore()
const { isMobile } = useMobileDetect()

const showProfileModal = ref(false)

const profileForm = ref({
  siret: '',
  legal_form: 'micro' as 'micro' | 'ei_reel' | 'eurl' | 'sasu' | 'sas',
  activity_type: 'services',
  cotisation_rate: 21.1,
  declaration_frequency: 'quarterly',
  revenue_threshold: 77700,
  cfp_rate: null as number | null,
  versement_liberatoire_enabled: 0 as number,
  versement_liberatoire_rate: null as number | null,
  ir_abattement_rate: null as number | null,
  foyer_tmi: null as number | null,
  tns_cotisations_rate: 45.0,
  salary_gross_monthly: 0,
  dividends_yearly: 0,
  eurl_tax_option: 'ir' as 'ir' | 'is',
  is_subject_to_vat: 0 as number,
  vat_rate: 20.0,
  vat_number: '',
  company_name: '',
  company_address: '',
  company_email: '',
  company_phone: '',
})

/** Activity types with their default cotisation rates and thresholds */
const ACTIVITY_PRESETS: Record<string, { rate: number; threshold: number }> = {
  services: { rate: 21.2, threshold: 77700 },
  liberal: { rate: 21.1, threshold: 77700 },
  vente: { rate: 12.3, threshold: 188700 },
  artisan: { rate: 21.2, threshold: 77700 },
  commercant: { rate: 12.3, threshold: 188700 },
  agent_commercial: { rate: 21.2, threshold: 77700 },
  location_meublee: { rate: 6.0, threshold: 188700 },
  restauration: { rate: 21.2, threshold: 77700 },
  transport: { rate: 21.2, threshold: 77700 },
  activite_mixte: { rate: 21.2, threshold: 188700 },
}

const activityTypeOptions = computed(() => [
  { label: t('pro.profile.services'), value: 'services' },
  { label: t('pro.profile.liberal'), value: 'liberal' },
  { label: t('pro.profile.vente'), value: 'vente' },
  { label: t('pro.profile.artisan'), value: 'artisan' },
  { label: t('pro.profile.commercant'), value: 'commercant' },
  { label: t('pro.profile.agent_commercial'), value: 'agent_commercial' },
  { label: t('pro.profile.location_meublee'), value: 'location_meublee' },
  { label: t('pro.profile.restauration'), value: 'restauration' },
  { label: t('pro.profile.transport'), value: 'transport' },
  { label: t('pro.profile.activite_mixte'), value: 'activite_mixte' },
])

/** Auto-fill rate and threshold when activity type changes */
function onActivityTypeChange(value: string) {
  profileForm.value.activity_type = value
  const preset = ACTIVITY_PRESETS[value]
  if (preset) {
    profileForm.value.cotisation_rate = preset.rate
    profileForm.value.revenue_threshold = preset.threshold
  }
}

const frequencyOptions = computed(() => [
  { label: t('pro.profile.monthly'), value: 'monthly' },
  { label: t('pro.profile.quarterly'), value: 'quarterly' },
])

const legalFormOptions = computed(() => [
  { label: t('pro.profile.legalForms.micro'), value: 'micro' },
  { label: t('pro.profile.legalForms.ei_reel'), value: 'ei_reel' },
  { label: t('pro.profile.legalForms.eurl'), value: 'eurl' },
  { label: t('pro.profile.legalForms.sasu'), value: 'sasu' },
  { label: t('pro.profile.legalForms.sas'), value: 'sas' },
])

const isIncorporated = computed(() => {
  if (profileForm.value.legal_form === 'sasu' || profileForm.value.legal_form === 'sas') return true
  if (profileForm.value.legal_form === 'eurl' && profileForm.value.eurl_tax_option === 'is') return true
  return false
})

const summary = computed(() => proStore.dashboardSummary || {
  ca_month: 0, ca_quarter: 0, ca_year: 0,
  expenses_month: 0, expenses_quarter: 0, expenses_year: 0,
  net_month: 0, cotisations_estimated: 0, threshold_percentage: 0,
})

const threshold = computed(() => proStore.proProfile?.revenue_threshold || 77700)

const recentTransactions = computed(() => proStore.proTransactions.slice(0, 10))

/** For a threshold's period, compute current accumulated turnover (income) for the user. */
function turnoverForPeriod(period: 'monthly' | 'quarterly' | 'yearly'): number {
  const now = new Date()
  const year = now.getFullYear()
  return proStore.proTransactions
    .filter(tx => {
      if (tx.transaction_type !== 'income') return false
      const d = new Date(tx.date)
      if (d.getFullYear() !== year) return false
      if (period === 'yearly') return true
      if (period === 'monthly') return d.getMonth() === now.getMonth()
      // quarterly
      return Math.floor(d.getMonth() / 3) === Math.floor(now.getMonth() / 3)
    })
    .reduce((s, tx) => s + tx.amount, 0)
}

const trackedLimits = computed(() => {
  return proStore.proThresholds
    .filter(th => th.active === 1)
    .map(th => {
      const current = turnoverForPeriod(th.period)
      const percentage = th.amount > 0 ? (current / th.amount) * 100 : 0
      const colorClass = percentage > 90 ? '#d03050' : percentage > 70 ? '#f0a020' : '#18a058'
      return { ...th, current, percentage: Math.min(percentage, 100), rawPercentage: percentage, colorClass }
    })
})

onMounted(async () => {
  await Promise.all([
    proStore.fetchProfile(),
    proStore.fetchDashboard(),
    proStore.fetchTransactions(),
    proStore.fetchThresholds(),
  ])

  if (proStore.proProfile) {
    profileForm.value = {
      siret: proStore.proProfile.siret || '',
      legal_form: proStore.proProfile.legal_form || 'micro',
      activity_type: proStore.proProfile.activity_type,
      cotisation_rate: proStore.proProfile.cotisation_rate,
      declaration_frequency: proStore.proProfile.declaration_frequency,
      revenue_threshold: proStore.proProfile.revenue_threshold,
      cfp_rate: proStore.proProfile.cfp_rate,
      versement_liberatoire_enabled: proStore.proProfile.versement_liberatoire_enabled || 0,
      versement_liberatoire_rate: proStore.proProfile.versement_liberatoire_rate,
      ir_abattement_rate: proStore.proProfile.ir_abattement_rate,
      foyer_tmi: proStore.proProfile.foyer_tmi,
      tns_cotisations_rate: proStore.proProfile.tns_cotisations_rate ?? 45.0,
      salary_gross_monthly: proStore.proProfile.salary_gross_monthly ?? 0,
      dividends_yearly: proStore.proProfile.dividends_yearly ?? 0,
      eurl_tax_option: proStore.proProfile.eurl_tax_option ?? 'ir',
      is_subject_to_vat: proStore.proProfile.is_subject_to_vat || 0,
      vat_rate: proStore.proProfile.vat_rate || 20.0,
      vat_number: proStore.proProfile.vat_number || '',
      company_name: proStore.proProfile.company_name || '',
      company_address: proStore.proProfile.company_address || '',
      company_email: proStore.proProfile.company_email || '',
      company_phone: proStore.proProfile.company_phone || '',
    }
  }

  await loadBreakdown()
  await loadVatSummary()
})

async function saveProfile() {
  await proStore.updateProfile(profileForm.value)
  await proStore.fetchDashboard()
  await loadBreakdown()
  showProfileModal.value = false
}

// ── Tax breakdown ──

const breakdownPeriod = ref<'month' | 'quarter' | 'year'>('month')
const breakdownYear = ref<number>(new Date().getFullYear())
const breakdown = ref<TaxBreakdown | null>(null)

const yearOptions = computed(() => {
  const current = new Date().getFullYear()
  return [0, 1, 2, 3, 4].map(offset => ({ label: String(current - offset), value: current - offset }))
})

async function loadBreakdown() {
  try {
    const year = breakdownPeriod.value === 'year' ? breakdownYear.value : undefined
    breakdown.value = await proProfileAPI.getTaxBreakdown(breakdownPeriod.value, year)
  } catch {
    breakdown.value = null
  }
  // Refresh the comparison-derived hint in the background
  loadComparisonForHint()
}

const comparisonForHint = ref<RegimeComparisonRow[]>([])
async function loadComparisonForHint() {
  try {
    const year = breakdownPeriod.value === 'year' ? breakdownYear.value : undefined
    comparisonForHint.value = await proProfileAPI.getRegimeComparison(breakdownPeriod.value, year)
  } catch {
    comparisonForHint.value = []
  }
}

const regimeHint = computed<string | null>(() => {
  if (!breakdown.value || comparisonForHint.value.length === 0) return null
  const current = comparisonForHint.value.find(r => r.regime === currentRegimeKey.value)
  if (!current) return null
  let best = current
  for (const row of comparisonForHint.value) {
    if (row.breakdown.personal_take_home > best.breakdown.personal_take_home) best = row
  }
  if (best.regime === current.regime) return null
  const delta = best.breakdown.personal_take_home - current.breakdown.personal_take_home
  if (delta < 1) return null
  return t('pro.tax.regimeHint', {
    regime: t(`pro.tax.regimeLabels.${best.regime}`),
    amount: delta.toFixed(0),
  })
})

watch(breakdownPeriod, loadBreakdown)
watch(breakdownYear, loadBreakdown)

// ── VAT summary ──

const vatPeriod = ref<'month' | 'quarter' | 'year'>('month')
const vatSummary = ref<VatSummary | null>(null)

async function loadVatSummary() {
  try {
    vatSummary.value = await proProfileAPI.getVatSummary(vatPeriod.value)
  } catch {
    vatSummary.value = null
  }
}

watch(vatPeriod, loadVatSummary)

// ── Regime comparison ──

const showCompareModal = ref(false)
const comparePeriod = ref<'month' | 'quarter' | 'year'>('year')
const compareYear = ref<number>(new Date().getFullYear())
const comparisonRows = ref<RegimeComparisonRow[]>([])

async function loadComparison() {
  try {
    const year = comparePeriod.value === 'year' ? compareYear.value : undefined
    comparisonRows.value = await proProfileAPI.getRegimeComparison(comparePeriod.value, year)
  } catch {
    comparisonRows.value = []
  }
}

async function openCompareModal() {
  comparisonRows.value = []
  showCompareModal.value = true
  await loadComparison()
}

watch([comparePeriod, compareYear], () => {
  if (showCompareModal.value) loadComparison()
})

const currentRegimeKey = computed<string>(() => {
  const lf = proStore.proProfile?.legal_form ?? 'micro'
  if (lf === 'eurl') {
    return proStore.proProfile?.eurl_tax_option === 'is' ? 'eurl_is' : 'eurl_ir'
  }
  return lf
})

const bestRegimeKey = computed<string | null>(() => {
  const first = comparisonRows.value[0]
  if (!first) return null
  let best = first
  for (const row of comparisonRows.value) {
    if (row.breakdown.personal_take_home > best.breakdown.personal_take_home) best = row
  }
  return best.regime
})
</script>

<style scoped>
.tax-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}
.tracked-limit-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.tracked-limit-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 13px;
}
.tracked-limit-header .dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.tracked-limit-header .amount-text {
  margin-left: auto;
  opacity: 0.75;
}
.tracked-limit-header .pct-text {
  font-weight: bold;
  min-width: 44px;
  text-align: right;
}
.regime-compare {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.regime-compare th,
.regime-compare td {
  padding: 6px 10px;
  text-align: right;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.regime-compare thead th {
  text-align: center;
  vertical-align: top;
  font-weight: 600;
  position: relative;
}
.regime-compare tbody th {
  text-align: left;
  font-weight: 500;
  opacity: 0.75;
}
.regime-compare th.current {
  background: rgba(32, 128, 240, 0.18);
}
.regime-compare th.best,
.regime-compare td.best {
  background: rgba(24, 160, 88, 0.18);
}
.regime-compare tr.total td,
.regime-compare tr.total th,
.regime-compare tr.net td,
.regime-compare tr.net th {
  font-weight: bold;
  font-size: 14px;
}
.regime-compare .badge {
  display: inline-block;
  margin-top: 4px;
  font-size: 10px;
  font-weight: normal;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(32, 128, 240, 0.3);
}
.regime-compare .best-badge {
  background: rgba(24, 160, 88, 0.4);
}
.regime-hint {
  margin-top: 12px;
  padding: 8px 12px;
  background: rgba(24, 160, 88, 0.12);
  border-left: 3px solid #18a058;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s ease;
}
.regime-hint:hover {
  background: rgba(24, 160, 88, 0.2);
}
.vat-stat {
  text-align: center;
  padding: 8px 0;
}
.vat-label {
  font-size: 12px;
  opacity: 0.7;
  margin-bottom: 4px;
}
.vat-value {
  font-size: 22px;
  font-weight: bold;
}
.vat-note {
  margin-top: 8px;
  font-size: 12px;
  opacity: 0.7;
}
</style>
