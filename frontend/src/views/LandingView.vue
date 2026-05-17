<template>
  <div class="landing">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <img src="/logo.png" alt="Tempo Budget" class="hero-logo" />
        <div class="beta-badge">{{ t('landing.invitationOnly') }}</div>
        <h1>{{ t('landing.title') }}</h1>
        <p class="hero-subtitle">{{ t('landing.subtitle') }}</p>
        <div class="hero-buttons">
          <n-button type="primary" size="large" @click="openMailto">
            {{ t('landing.requestInvitation') }}
          </n-button>
          <n-button size="large" quaternary @click="router.push('/login')">
            {{ t('landing.alreadyHaveInvitation') }}
          </n-button>
        </div>
      </div>
      <div class="hero-visual">
        <div class="mockup">
          <div class="mockup-header">
            <span class="dot red"></span>
            <span class="dot yellow"></span>
            <span class="dot green"></span>
          </div>
          <div class="mockup-content">
            <div class="mock-card">
              <div class="mock-title"></div>
              <div class="mock-chart"></div>
            </div>
            <div class="mock-stats">
              <div class="mock-stat"></div>
              <div class="mock-stat"></div>
              <div class="mock-stat"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- How It Works Section -->
    <section class="how-it-works">
      <h2>{{ t('landing.howItWorksTitle') }}</h2>
      <div class="steps-grid">
        <div class="step-card">
          <div class="step-icon">1</div>
          <h3>{{ t('landing.howItWorksStep1Title') }}</h3>
          <p>{{ t('landing.howItWorksStep1Desc') }}</p>
        </div>
        <div class="step-arrow">→</div>
        <div class="step-card">
          <div class="step-icon">2</div>
          <h3>{{ t('landing.howItWorksStep2Title') }}</h3>
          <p>{{ t('landing.howItWorksStep2Desc') }}</p>
        </div>
        <div class="step-arrow">→</div>
        <div class="step-card highlight">
          <div class="step-icon pro">PRO</div>
          <h3>{{ t('landing.howItWorksStep3Title') }}</h3>
          <p>{{ t('landing.howItWorksStep3Desc') }}</p>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="features">
      <h2>{{ t('landing.featuresTitle') }}</h2>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">💰</div>
          <h3>{{ t('landing.feature1Title') }}</h3>
          <p>{{ t('landing.feature1Desc') }}</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">👥</div>
          <h3>{{ t('landing.feature2Title') }}</h3>
          <p>{{ t('landing.feature2Desc') }}</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🔄</div>
          <h3>{{ t('landing.feature3Title') }}</h3>
          <p>{{ t('landing.feature3Desc') }}</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">📊</div>
          <h3>{{ t('landing.feature4Title') }}</h3>
          <p>{{ t('landing.feature4Desc') }}</p>
        </div>
      </div>
    </section>

    <!-- Pro Section -->
    <section class="pro-section">
      <div class="pro-content">
        <div class="pro-badge">PRO</div>
        <h2>{{ t('landing.proTitle') }}</h2>
        <p class="pro-subtitle">{{ t('landing.proSubtitle') }}</p>
        <ul class="pro-features">
          <li>{{ t('landing.proFeature1') }}</li>
          <li>{{ t('landing.proFeature2') }}</li>
          <li>{{ t('landing.proFeature3') }}</li>
          <li>{{ t('landing.proFeature4') }}</li>
          <li>{{ t('landing.proFeature5') }}</li>
        </ul>
        <n-button type="primary" size="large" @click="router.push('/pricing')">
          {{ t('subscription.subscribe') }}
        </n-button>
      </div>
      <div class="pro-visual">
        <div class="tax-card">
          <div class="tax-header">{{ t('landing.taxPreview') }}</div>
          <div class="tax-row">
            <span>URSSAF</span>
            <span class="amount">-1 234 €</span>
          </div>
          <div class="tax-row">
            <span>{{ t('landing.incomeTax') }}</span>
            <span class="amount">-567 €</span>
          </div>
          <div class="tax-row highlight">
            <span>{{ t('landing.netToYou') }}</span>
            <span class="amount positive">4 199 €</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Pricing Section -->
    <section class="pricing-section">
      <h2>{{ t('landing.pricingTitle') }}</h2>
      <div class="pricing-grid">
        <div class="pricing-card">
          <div class="pricing-header">
            <h3>{{ t('landing.pricingFree') }}</h3>
            <div class="pricing-price">
              <span class="price">0 €</span>
            </div>
            <p class="pricing-desc">{{ t('landing.pricingFreeDesc') }}</p>
          </div>
          <ul class="pricing-features">
            <li><span class="check">✓</span> {{ t('landing.pricingFreeFeature1') }}</li>
            <li><span class="check">✓</span> {{ t('landing.pricingFreeFeature2') }}</li>
            <li><span class="check">✓</span> {{ t('landing.pricingFreeFeature3') }}</li>
            <li><span class="check">✓</span> {{ t('landing.pricingFreeFeature4') }}</li>
            <li><span class="check">✓</span> {{ t('landing.pricingFreeFeature5') }}</li>
          </ul>
          <n-button size="large" block @click="openMailto">
            {{ t('landing.requestInvitation') }}
          </n-button>
        </div>
        <div class="pricing-card featured">
          <div class="pricing-badge">PRO</div>
          <div class="pricing-header">
            <h3>{{ t('landing.pricingPro') }}</h3>
            <div class="pricing-price">
              <span class="price">{{ t('landing.pricingProPrice') }}</span>
              <span class="period">{{ t('landing.pricingProPeriod') }}</span>
            </div>
            <p class="pricing-desc">{{ t('landing.pricingProDesc') }}</p>
          </div>
          <ul class="pricing-features">
            <li><span class="check">✓</span> {{ t('landing.pricingProFeature1') }}</li>
            <li><span class="check">✓</span> {{ t('landing.pricingProFeature2') }}</li>
            <li><span class="check">✓</span> {{ t('landing.pricingProFeature3') }}</li>
            <li><span class="check">✓</span> {{ t('landing.pricingProFeature4') }}</li>
            <li><span class="check">✓</span> {{ t('landing.pricingProFeature5') }}</li>
          </ul>
          <n-button type="primary" size="large" block @click="router.push('/pricing')">
            {{ t('subscription.subscribe') }}
          </n-button>
        </div>
      </div>
    </section>

    <!-- Factur-X Section -->
    <section class="facturx-section">
      <div class="facturx-badge">2026</div>
      <h2>{{ t('landing.facturxTitle') }}</h2>
      <p>{{ t('landing.facturxDesc') }}</p>
      <div class="facturx-features">
        <div class="facturx-item">
          <span class="check">✓</span>
          {{ t('landing.facturxFeature1') }}
        </div>
        <div class="facturx-item">
          <span class="check">✓</span>
          {{ t('landing.facturxFeature2') }}
        </div>
        <div class="facturx-item">
          <span class="check">✓</span>
          {{ t('landing.facturxFeature3') }}
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
      <h2>{{ t('landing.ctaTitle') }}</h2>
      <p>{{ t('landing.ctaSubtitle') }}</p>
      <div class="cta-buttons">
        <n-button type="primary" size="large" @click="openMailto">
          {{ t('landing.ctaButton') }}
        </n-button>
        <n-button size="large" @click="router.push('/login')">
          {{ t('landing.alreadyHaveInvitation') }}
        </n-button>
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <div class="footer-content">
        <div class="footer-brand">
          <img src="/logo.png" alt="Tempo Budget" class="footer-logo" />
          <span>Tempo Budget</span>
        </div>
        <div class="footer-links">
          <a href="https://github.com/jdenozi/TempoBudget" target="_blank" rel="noopener">GitHub</a>
          <span class="separator">•</span>
          <span>MIT License</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { NButton } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

const { t } = useI18n()
const router = useRouter()

function openMailto() {
  window.location.href = 'mailto:contact@tempo.finance?subject=Demande%20d%27invitation%20Tempo%20Budget'
}
</script>

<style scoped>
.landing {
  min-height: 100vh;
  background: linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 100%);
  color: #fff;
  overflow-x: hidden;
}

/* Hero */
.hero {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 60px 10%;
  gap: 60px;
  flex-wrap: wrap;
}

.hero-content {
  flex: 1;
  min-width: 300px;
}

.hero-logo {
  width: 80px;
  height: 80px;
  margin-bottom: 16px;
}

.beta-badge {
  display: inline-block;
  background: linear-gradient(135deg, #ff6b6b, #ee5a5a);
  color: #fff;
  font-weight: 600;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.85rem;
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.hero h1 {
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 700;
  margin: 0 0 16px;
  background: linear-gradient(135deg, #63e2b7 0%, #18a058 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: clamp(1.1rem, 2vw, 1.4rem);
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 32px;
  line-height: 1.6;
}

.hero-buttons {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.hero-visual {
  flex: 1;
  min-width: 300px;
  display: flex;
  justify-content: center;
}

.mockup {
  width: 100%;
  max-width: 500px;
  background: #1e1e2e;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.mockup-header {
  background: #2a2a3e;
  padding: 12px 16px;
  display: flex;
  gap: 8px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}
.dot.red { background: #ff5f57; }
.dot.yellow { background: #ffbd2e; }
.dot.green { background: #28ca42; }

.mockup-content {
  padding: 24px;
}

.mock-card {
  background: #2a2a3e;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.mock-title {
  height: 20px;
  width: 60%;
  background: #3a3a4e;
  border-radius: 4px;
  margin-bottom: 16px;
}

.mock-chart {
  height: 120px;
  background: linear-gradient(90deg, #63e2b7 0%, #18a058 50%, #63e2b7 100%);
  border-radius: 8px;
  opacity: 0.3;
}

.mock-stats {
  display: flex;
  gap: 12px;
}

.mock-stat {
  flex: 1;
  height: 60px;
  background: #2a2a3e;
  border-radius: 8px;
}

/* How It Works */
.how-it-works {
  padding: 80px 10%;
  background: linear-gradient(180deg, #0a0a0a 0%, #0f0f1a 100%);
  text-align: center;
}

.how-it-works h2 {
  font-size: clamp(2rem, 4vw, 2.5rem);
  margin-bottom: 60px;
}

.steps-grid {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.step-card {
  background: #1a1a2e;
  border-radius: 16px;
  padding: 32px;
  width: 280px;
  text-align: center;
  transition: transform 0.3s, box-shadow 0.3s;
}

.step-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(99, 226, 183, 0.1);
}

.step-card.highlight {
  border: 2px solid #63e2b7;
  background: linear-gradient(180deg, #1a1a2e 0%, #1f2a1f 100%);
}

.step-icon {
  width: 60px;
  height: 60px;
  background: #2a2a3e;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  color: #63e2b7;
  margin: 0 auto 20px;
}

.step-icon.pro {
  background: linear-gradient(135deg, #63e2b7, #18a058);
  color: #000;
  font-size: 0.9rem;
}

.step-card h3 {
  font-size: 1.1rem;
  margin-bottom: 12px;
  color: #fff;
}

.step-card p {
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.5;
  font-size: 0.95rem;
}

.step-arrow {
  font-size: 2rem;
  color: rgba(255, 255, 255, 0.3);
}

/* Features */
.features {
  padding: 100px 10%;
  background: #0f0f1a;
}

.features h2 {
  text-align: center;
  font-size: clamp(2rem, 4vw, 2.5rem);
  margin-bottom: 60px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 32px;
}

.feature-card {
  background: #1a1a2e;
  border-radius: 16px;
  padding: 32px;
  transition: transform 0.3s, box-shadow 0.3s;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(99, 226, 183, 0.1);
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.feature-card h3 {
  font-size: 1.3rem;
  margin-bottom: 12px;
  color: #63e2b7;
}

.feature-card p {
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.6;
}

/* Pro Section */
.pro-section {
  padding: 100px 10%;
  display: flex;
  align-items: center;
  gap: 60px;
  flex-wrap: wrap;
}

.pro-content {
  flex: 1;
  min-width: 300px;
}

.pro-badge {
  display: inline-block;
  background: linear-gradient(135deg, #63e2b7, #18a058);
  color: #000;
  font-weight: 700;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.9rem;
  margin-bottom: 16px;
}

.pro-section h2 {
  font-size: clamp(1.8rem, 3vw, 2.2rem);
  margin-bottom: 16px;
}

.pro-subtitle {
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 24px;
  font-size: 1.1rem;
}

.pro-features {
  list-style: none;
  padding: 0;
  margin-bottom: 24px;
}

.pro-features li {
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
}

.pro-features li::before {
  content: "✓";
  color: #63e2b7;
  margin-right: 12px;
  font-weight: 700;
}

.pro-visual {
  flex: 1;
  min-width: 300px;
  display: flex;
  justify-content: center;
}

.tax-card {
  background: #1a1a2e;
  border-radius: 16px;
  padding: 24px;
  width: 100%;
  max-width: 350px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.tax-header {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 20px;
}

.tax-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.tax-row.highlight {
  border: none;
  background: rgba(99, 226, 183, 0.1);
  margin: 12px -16px -12px;
  padding: 16px;
  border-radius: 0 0 12px 12px;
}

.amount {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.6);
}

.amount.positive {
  color: #63e2b7;
  font-size: 1.2rem;
}

/* Pricing Section */
.pricing-section {
  padding: 100px 10%;
  background: #0f0f1a;
  text-align: center;
}

.pricing-section h2 {
  font-size: clamp(2rem, 4vw, 2.5rem);
  margin-bottom: 60px;
}

.pricing-grid {
  display: flex;
  justify-content: center;
  gap: 32px;
  flex-wrap: wrap;
}

.pricing-card {
  background: #1a1a2e;
  border-radius: 16px;
  padding: 32px;
  width: 100%;
  max-width: 340px;
  text-align: left;
  position: relative;
  transition: transform 0.3s, box-shadow 0.3s;
}

.pricing-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.pricing-card.featured {
  border: 2px solid #63e2b7;
  background: linear-gradient(180deg, #1a1a2e 0%, #1f2a1f 100%);
}

.pricing-badge {
  position: absolute;
  top: -12px;
  right: 24px;
  background: linear-gradient(135deg, #63e2b7, #18a058);
  color: #000;
  font-weight: 700;
  padding: 4px 16px;
  border-radius: 20px;
  font-size: 0.8rem;
}

.pricing-header h3 {
  font-size: 1.5rem;
  margin: 0 0 8px;
}

.pricing-price {
  margin-bottom: 8px;
}

.pricing-price .price {
  font-size: 2.5rem;
  font-weight: 700;
  color: #63e2b7;
}

.pricing-price .period {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.5);
}

.pricing-desc {
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 24px;
  font-size: 0.95rem;
}

.pricing-features {
  list-style: none;
  padding: 0;
  margin: 0 0 24px;
}

.pricing-features li {
  padding: 8px 0;
  color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  gap: 10px;
}

.pricing-features .check {
  color: #63e2b7;
  font-weight: 700;
}

/* Factur-X Section */
.facturx-section {
  padding: 80px 10%;
  background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%);
  text-align: center;
}

.facturx-badge {
  display: inline-block;
  background: #ff6b6b;
  color: #fff;
  font-weight: 700;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.9rem;
  margin-bottom: 16px;
}

.facturx-section h2 {
  font-size: clamp(1.6rem, 3vw, 2rem);
  margin-bottom: 16px;
}

.facturx-section > p {
  color: rgba(255, 255, 255, 0.7);
  max-width: 600px;
  margin: 0 auto 32px;
}

.facturx-features {
  display: flex;
  justify-content: center;
  gap: 32px;
  flex-wrap: wrap;
}

.facturx-item {
  background: rgba(255, 255, 255, 0.05);
  padding: 16px 24px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.check {
  color: #63e2b7;
  font-weight: 700;
}

/* CTA */
.cta-section {
  padding: 100px 10%;
  text-align: center;
  background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
}

.cta-section h2 {
  font-size: clamp(2rem, 4vw, 2.5rem);
  margin-bottom: 16px;
}

.cta-section p {
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 32px;
  font-size: 1.1rem;
}

.cta-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

/* Footer */
.footer {
  padding: 40px 10%;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
}

.footer-logo {
  width: 32px;
  height: 32px;
}

.footer-links {
  display: flex;
  align-items: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.footer-links a {
  color: #63e2b7;
  text-decoration: none;
}

.footer-links a:hover {
  text-decoration: underline;
}

.separator {
  color: rgba(255, 255, 255, 0.3);
}

/* Responsive */
@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    text-align: center;
    padding: 40px 5%;
  }

  .hero-buttons {
    justify-content: center;
  }

  .pro-section {
    flex-direction: column;
    text-align: center;
  }

  .pro-features li {
    text-align: left;
  }

  .steps-grid {
    flex-direction: column;
  }

  .step-arrow {
    transform: rotate(90deg);
  }

  .step-card {
    width: 100%;
    max-width: 300px;
  }

  .cta-buttons {
    flex-direction: column;
    align-items: center;
  }
}
</style>
