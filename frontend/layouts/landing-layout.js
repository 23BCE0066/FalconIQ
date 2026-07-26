export const LandingLayout = {
  async render(container) {
    container.innerHTML = `

  <!-- ========== NAVBAR ========== -->
  <nav class="navbar" id="navbar">
    <div class="nav-container">
      <a href="#" class="nav-logo" id="nav-logo">
        <div class="logo-icon">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 2L4 7v9c0 7.18 5.15 13.9 12 15.45C22.85 29.9 28 23.18 28 16V7L16 2z" fill="url(#shieldGrad)" />
            <path d="M12 16l3 3 5-6" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
            <defs>
              <linearGradient id="shieldGrad" x1="4" y1="2" x2="28" y2="32" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stop-color="#818cf8"/>
                <stop offset="100%" stop-color="#4f46e5"/>
              </linearGradient>
          </svg>
        </div>
        <span class="logo-text" style="font-weight: 900; font-size: 22px; letter-spacing: -0.5px;">Falcon<strong style="color: #4f46e5;">IQ</strong></span>
      </a>

      <ul class="nav-links" id="nav-links">
        <li><a href="#features" class="nav-link">Features</a></li>
        <li><a href="#how-it-works" class="nav-link">How it works</a></li>
        <li><a href="#pricing" class="nav-link">Pricing</a></li>
      </ul>

      <div class="nav-actions">
        <button class="theme-toggle" id="theme-toggle" title="Toggle theme">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="5" stroke="currentColor" stroke-width="1.8"/>
            <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
          </svg>
        </button>
        <a href="#" class="btn-ghost" id="signin-btn">Sign in</a>
        <a href="#dashboard" class="btn-primary" id="launch-btn">
          <svg viewBox="0 0 20 20" fill="none"><path d="M10 2l8 4-8 4-8-4 8-4zM2 10l8 4 8-4M2 14l8 4 8-4" stroke="white" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
          Launch FalconIQ Platform
        </a>
        <button class="hamburger" id="hamburger" aria-label="Menu">
          <span></span><span></span><span></span>
        </button>
      </div>
    </div>
  </nav>

  <!-- ========== HERO ========== -->
  <section class="hero" id="hero">
    <div class="hero-bg-grid"></div>
    <div class="hero-gradient-blob blob-1"></div>
    <div class="hero-gradient-blob blob-2"></div>

    <div class="hero-container">
      <div class="hero-left" id="hero-left">
        <div class="hero-pills">
          <span class="pill">✦ AI-Powered</span>
          <span class="pill-sep">•</span>
          <span class="pill">Autonomous</span>
          <span class="pill-sep">•</span>
          <span class="pill">Explainable</span>
        </div>

        <h1 class="hero-title">
          Smarter <span class="gradient-text">AML</span><br/>
          Stronger Compliance
        </h1>

        <p class="hero-subtitle">
          FalconIQ detects suspicious financial activity in real-time, explains the
          risk, and helps compliance teams act with ultimate confidence.
        </p>

        <div class="hero-cta-row" style="display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: center;">
          <a href="#dashboard" class="btn-primary btn-large" id="hero-launch-btn">
            <svg viewBox="0 0 20 20" fill="none"><path d="M10 2l8 4-8 4-8-4 8-4zM2 10l8 4 8-4M2 14l8 4 8-4" stroke="white" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
            Launch FalconIQ Platform
          </a>
          <a href="#how-it-works" class="btn-outline btn-large" id="watch-demo-btn">
            <svg viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="8" stroke="currentColor" stroke-width="1.6"/><path d="M8 7l6 3-6 3V7z" fill="currentColor"/></svg>
            Watch Demo
          </a>
          <a href="#" class="btn-outline btn-large" id="hero-book-demo-btn" style="background: linear-gradient(135deg, #4f46e5, #9333ea); color: white; border: none; font-weight: 700; box-shadow: 0 4px 18px rgba(147, 51, 234, 0.4); text-decoration: none; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 18px;">📅</span> Book Automated Demo
          </a>
        </div>

        <div class="hero-stats" id="hero-stats">
          <div class="stat-pill" id="stat-accuracy">
            <div class="stat-icon stat-icon-blue">
              <svg viewBox="0 0 20 20" fill="none"><path d="M3 10l5 5 9-9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <div>
              <div class="stat-value">98.3%</div>
              <div class="stat-label">Detection Accuracy</div>
            </div>
          </div>
          <div class="stat-pill" id="stat-transactions">
            <div class="stat-icon stat-icon-green">
              <svg viewBox="0 0 20 20" fill="none"><ellipse cx="10" cy="7" rx="7" ry="3" stroke="currentColor" stroke-width="1.6"/><path d="M3 7v6c0 1.66 3.13 3 7 3s7-1.34 7-3V7" stroke="currentColor" stroke-width="1.6"/></svg>
            </div>
            <div>
              <div class="stat-value">245K+</div>
              <div class="stat-label">Transactions Analyzed</div>
            </div>
          </div>
          <div class="stat-pill" id="stat-alerts">
            <div class="stat-icon stat-icon-red">
              <svg viewBox="0 0 20 20" fill="none"><path d="M10 3l7 13H3L10 3z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M10 9v3M10 14h.01" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
            </div>
            <div>
              <div class="stat-value">1,247</div>
              <div class="stat-label">Suspicious Alerts</div>
            </div>
          </div>
          <div class="stat-pill" id="stat-patterns">
            <div class="stat-icon stat-icon-yellow">
              <svg viewBox="0 0 20 20" fill="none"><path d="M10 2a8 8 0 100 16A8 8 0 0010 2z" stroke="currentColor" stroke-width="1.6"/><path d="M7 10l2 2 4-4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <div>
              <div class="stat-value">6</div>
              <div class="stat-label">AML Patterns Detected</div>
            </div>
          </div>
        </div>

        <div class="trusted-section" id="trusted-section">
          <p class="trusted-label">Trusted by compliance &amp; risk teams</p>
          <div class="trusted-logos">
            <span class="trust-logo" id="logo-hsbc">⬡ HSBC</span>
            <span class="trust-logo" id="logo-barclays">BARCLAYS</span>
            <span class="trust-logo" id="logo-sc">⊕ Standard Chartered</span>
            <span class="trust-logo" id="logo-ripple">◈ ripple</span>
            <span class="trust-logo" id="logo-deutsche">☐ Deutsche Bank</span>
          </div>
        </div>
      </div>

      <div class="hero-right" id="hero-right">
        <div class="mockup-wrapper">
          <div class="mockup-device">
            <div class="mockup-topbar">
              <div class="topbar-dots">
                <span class="dot dot-red"></span>
                <span class="dot dot-yellow"></span>
                <span class="dot dot-green"></span>
              </div>
              <div class="topbar-url" style="font-weight: 700; color: #4f46e5;">falconiq.ai/dashboard</div>
            </div>
            <div class="mockup-screen">
              <img 
                src="assets/images/dashboard_mockup.png"
                alt="FalconIQ AML Dashboard"
                class="dashboard-img"
                id="dashboard-img"
              />
            </div>
          </div>
          <div class="floating-badge" id="floating-badge">
            <div class="badge-dot"></div>
            <span>AI Agent Online</span>
          </div>
          <div class="shield-accent" id="shield-accent">
            <svg viewBox="0 0 80 96" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M40 4L8 16v24c0 22.1 13.7 42.8 32 48 18.3-5.2 32-25.9 32-48V16L40 4z" fill="url(#shieldG)" opacity="0.92"/>
              <path d="M28 46l9 9 15-18" stroke="white" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
              <defs>
                <linearGradient id="shieldG" x1="8" y1="4" x2="72" y2="96" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stop-color="#a78bfa"/>
                  <stop offset="100%" stop-color="#4338ca"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ========== HOW IT WORKS ========== -->
  <section class="how-section" id="how-it-works">
    <div class="how-container">
      <div class="how-left">
        <div class="section-eyebrow">Workflow</div>
        <h2 class="section-title">
          How <span class="gradient-text">FalconIQ AI Platform</span> Works
        </h2>
        <p class="section-subtitle">
          An autonomous AI agent that thinks, analyzes and investigates for you.
        </p>

        <div class="steps-row" id="steps-row">
          <div class="step-item" id="step-1">
            <div class="step-icon-wrap">
              <svg viewBox="0 0 32 32" fill="none"><path d="M16 28c6.627 0 12-5.373 12-12S22.627 4 16 4 4 9.373 4 16s5.373 12 12 12z" stroke="currentColor" stroke-width="1.5"/><path d="M11 20s1.5-3 5-3 5 3 5 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="12" cy="13" r="1.5" fill="currentColor"/><circle cx="20" cy="13" r="1.5" fill="currentColor"/></svg>
            </div>
            <div class="step-connector"></div>
          </div>
          <div class="step-item" id="step-2">
            <div class="step-icon-wrap">
              <svg viewBox="0 0 32 32" fill="none"><circle cx="16" cy="10" r="3" stroke="currentColor" stroke-width="1.5"/><circle cx="7" cy="22" r="3" stroke="currentColor" stroke-width="1.5"/><circle cx="25" cy="22" r="3" stroke="currentColor" stroke-width="1.5"/><path d="M16 13v4M16 17l-6 4M16 17l6 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </div>
            <div class="step-connector"></div>
          </div>
          <div class="step-item" id="step-3">
            <div class="step-icon-wrap">
              <svg viewBox="0 0 32 32" fill="none"><ellipse cx="16" cy="10" rx="8" ry="4" stroke="currentColor" stroke-width="1.5"/><path d="M8 10v6c0 2.21 3.58 4 8 4s8-1.79 8-4v-6" stroke="currentColor" stroke-width="1.5"/><path d="M8 16v6c0 2.21 3.58 4 8 4s8-1.79 8-4v-6" stroke="currentColor" stroke-width="1.5"/></svg>
            </div>
            <div class="step-connector"></div>
          </div>
          <div class="step-item" id="step-4">
            <div class="step-icon-wrap">
              <svg viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="10" stroke="currentColor" stroke-width="1.5"/><path d="M10 16l4 4 8-8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <div class="step-connector"></div>
          </div>
          <div class="step-item" id="step-5">
            <div class="step-icon-wrap">
              <svg viewBox="0 0 32 32" fill="none"><rect x="6" y="4" width="20" height="24" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M10 10h12M10 14h12M10 18h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </div>
          </div>
        </div>

        <div class="step-labels">
          <div class="step-label" id="label-1">
            <div class="step-num">1. Understand</div>
            <div class="step-desc">Agent understands your query and intent</div>
          </div>
          <div class="step-label" id="label-2">
            <div class="step-num">2. Plan</div>
            <div class="step-desc">Builds a dynamic plan and selects the right tools</div>
          </div>
          <div class="step-label" id="label-3">
            <div class="step-num">3. Analyze</div>
            <div class="step-desc">Processes data, detects patterns and anomalies</div>
          </div>
          <div class="step-label" id="label-4">
            <div class="step-num">4. Explain</div>
            <div class="step-desc">Generates explanations and risk score</div>
          </div>
          <div class="step-label" id="label-5">
            <div class="step-num">5. Recommend</div>
            <div class="step-desc">Suggests next actions and escalation</div>
          </div>
        </div>
      </div>

      <div class="how-right" id="how-right">
        <div class="why-card" id="why-card">
          <h3 class="why-title">Why Teams Love It</h3>
          <ul class="why-list">
            <li class="why-item" id="why-1"><span class="why-check">✓</span> Reduces false positives</li>
            <li class="why-item" id="why-2"><span class="why-check">✓</span> Saves hours of manual investigation</li>
            <li class="why-item" id="why-3"><span class="why-check">✓</span> Explainable and audit-ready</li>
            <li class="why-item" id="why-4"><span class="why-check">✓</span> Adaptive to new threats</li>
            <li class="why-item" id="why-5"><span class="why-check">✓</span> Built for compliance teams</li>
          </ul>
        </div>
        <div class="lock-3d" id="lock-3d">
          <img 
            src="assets/icons/lock_icon.png"
            alt="Security Shield"
            onerror="this.style.display='none'"
          />
        </div>
      </div>
    </div>
  </section>

  <!-- ========== FEATURES ========== -->
  <section class="features-section" id="features">
    <div class="features-container">
      <div class="section-eyebrow center">Capabilities</div>
      <h2 class="section-title center">Everything You Need to Fight Financial Crime</h2>
      <p class="section-subtitle center">Purpose-built for compliance teams at financial institutions.</p>

      <div class="features-grid" id="features-grid">
        <div class="feature-card" id="feature-1">
          <div class="feature-icon">
            <svg viewBox="0 0 32 32" fill="none"><path d="M16 4L4 10v7c0 7.73 5.14 14.95 12 16.73C22.86 31.95 28 24.73 28 17v-7L16 4z" stroke="currentColor" stroke-width="1.6"/><path d="M11 16l4 4 6-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
          <h3>Real-Time Monitoring</h3>
          <p>Continuously scans transactions as they happen, flagging anomalies in milliseconds.</p>
        </div>
        <div class="feature-card" id="feature-2">
          <div class="feature-icon">
            <svg viewBox="0 0 32 32" fill="none"><circle cx="12" cy="12" r="7" stroke="currentColor" stroke-width="1.6"/><path d="M17 17l7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </div>
          <h3>Network Graph Analysis</h3>
          <p>Visualize relationships between entities and uncover hidden money laundering networks.</p>
        </div>
        <div class="feature-card" id="feature-3">
          <div class="feature-icon">
            <svg viewBox="0 0 32 32" fill="none"><path d="M4 24l8-8 4 4 8-10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><rect x="4" y="4" width="24" height="24" rx="2" stroke="currentColor" stroke-width="1.6"/></svg>
          </div>
          <h3>Risk Scoring Engine</h3>
          <p>ML-powered risk scores with explainable factors for each alert and entity profile.</p>
        </div>
        <div class="feature-card" id="feature-4">
          <div class="feature-icon">
            <svg viewBox="0 0 32 32" fill="none"><path d="M28 20v6a2 2 0 01-2 2H6a2 2 0 01-2-2v-6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M21 14l-5 5-5-5M16 4v15" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
          <h3>SAR Auto-Generation</h3>
          <p>Automatically drafts Suspicious Activity Reports with supporting evidence.</p>
        </div>
        <div class="feature-card" id="feature-5">
          <div class="feature-icon">
            <svg viewBox="0 0 32 32" fill="none"><rect x="4" y="6" width="24" height="20" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M4 12h24" stroke="currentColor" stroke-width="1.6"/><circle cx="10" cy="18" r="1.5" fill="currentColor"/><path d="M14 18h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </div>
          <h3>Case Management</h3>
          <p>End-to-end investigation tracking with audit trails for regulatory compliance.</p>
        </div>
        <div class="feature-card" id="feature-6">
          <div class="feature-icon">
            <svg viewBox="0 0 32 32" fill="none"><path d="M26 14a10 10 0 11-20 0 10 10 0 0120 0z" stroke="currentColor" stroke-width="1.6"/><path d="M16 4v4M16 24v4M4 14h4M24 14h4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
          </div>
          <h3>Agentic AI Core</h3>
          <p>Planner + Supervisor architecture that dynamically builds workflows from natural language.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- ========== PRICING SECTION ========== -->
  <section class="section" id="pricing" style="padding: 100px 0; background: var(--bg-alt, #f8fafc); position: relative;">
    <div class="container" style="max-width: 1200px; margin: 0 auto; padding: 0 24px; text-align: center;">
      <span class="badge badge-high" style="background: rgba(79, 70, 229, 0.1); color: #4f46e5; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 13px; text-transform: uppercase;">Flexible Enterprise Pricing</span>
      <h2 style="font-size: 38px; font-weight: 800; color: var(--text, #111827); margin: 16px 0 12px 0;">Predictable Plans for AML Compliance & Security</h2>
      <p style="font-size: 17px; color: var(--text-muted, #6b7280); max-width: 650px; margin: 0 auto 40px auto;">Choose standard monthly billing, save 10% with quarterly commitments, or enjoy 20% discounts on annual contracts.</p>

      <!-- Pricing Frequency Switcher Pills -->
      <div style="display: inline-flex; background: var(--border, #e5e7eb); padding: 5px; border-radius: 999px; gap: 4px; margin-bottom: 56px; border: 1px solid var(--border, #d1d5db); box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <button class="pricing-tab" data-period="monthly" style="padding: 10px 24px; border-radius: 999px; border: none; font-size: 14px; font-weight: 700; cursor: pointer; background: var(--primary, #4f46e5); color: white; transition: all 0.2s;">Monthly</button>
        <button class="pricing-tab" data-period="quarterly" style="padding: 10px 24px; border-radius: 999px; border: none; font-size: 14px; font-weight: 600; cursor: pointer; background: transparent; color: var(--text-muted, #4b5563); transition: all 0.2s; display: flex; align-items: center; gap: 6px;">Quarterly <span style="background: #10b981; color: white; font-size: 11px; padding: 2px 8px; border-radius: 12px; font-weight: 700;">SAVE 10%</span></button>
        <button class="pricing-tab" data-period="yearly" style="padding: 10px 24px; border-radius: 999px; border: none; font-size: 14px; font-weight: 600; cursor: pointer; background: transparent; color: var(--text-muted, #4b5563); transition: all 0.2s; display: flex; align-items: center; gap: 6px;">Yearly <span style="background: #ef4444; color: white; font-size: 11px; padding: 2px 8px; border-radius: 12px; font-weight: 700;">SAVE 20%</span></button>
      </div>

      <!-- Pricing Cards Grid with Interactive Hover Styling -->
      <style>
        .pricing-card {
          background: var(--card-bg, #ffffff);
          border: 2px solid var(--border, #e5e7eb);
          border-radius: 24px;
          padding: 38px 34px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          position: relative;
          box-shadow: 0 10px 30px rgba(0,0,0,0.04);
          transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
          z-index: 1;
        }
        .pricing-card:hover {
          border-color: #4f46e5;
          box-shadow: 0 24px 60px rgba(79, 70, 229, 0.22);
          transform: translateY(-8px) scale(1.03);
          z-index: 5;
        }
        .pricing-btn {
          width: 100%;
          text-align: center;
          padding: 16px;
          border-radius: 14px;
          font-weight: 800;
          font-size: 15.5px;
          cursor: pointer;
          transition: all 0.25s ease;
          display: block;
          margin-top: 28px;
          border: 2px solid #4f46e5;
          background: rgba(79, 70, 229, 0.05);
          color: #4f46e5;
          box-shadow: 0 4px 14px rgba(79, 70, 229, 0.08);
        }
        .pricing-card:hover .pricing-btn {
          background: linear-gradient(135deg, #4f46e5, #6366f1);
          border-color: transparent;
          color: #ffffff;
          box-shadow: 0 10px 28px rgba(79, 70, 229, 0.45);
          transform: scale(1.02);
        }
        .pricing-btn:hover {
          filter: brightness(1.1);
          box-shadow: 0 12px 32px rgba(79, 70, 229, 0.55);
        }
      </style>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 32px; text-align: left; padding: 10px 0;">
        <!-- Starter Plan -->
        <div class="pricing-card">
          <div>
            <h3 style="font-size: 22px; font-weight: 800; color: var(--text, #111827); margin-top: 0;">Fintech Starter</h3>
            <p style="font-size: 14px; color: var(--text-muted, #6b7280); min-height: 44px;">Ideal for early-stage Indian fintech startups & lending apps managing up to 25,000 monthly transactions.</p>
            <div style="margin: 28px 0; padding-bottom: 24px; border-bottom: 1px solid var(--border, #f1f5f9);">
              <span class="price-val" data-monthly="₹1,500" data-quarterly="₹1,350" data-yearly="₹1,200" style="font-size: 44px; font-weight: 900; color: var(--text, #111827);">₹1,500</span>
              <span style="font-size: 15px; font-weight: 600; color: var(--text-muted, #6b7280);"> / month</span>
              <div class="bill-note" style="font-size: 13px; color: var(--text-muted, #6b7280); margin-top: 4px;">Billed monthly</div>
            </div>
            <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 16px; font-size: 15px; color: var(--text, #374151);">
              <li style="display: flex; align-items: center; gap: 12px;"><span style="color: #10b981; font-weight: bold; font-size: 18px;">✔</span> Up to 25,000 AI Transactions / mo</li>
              <li style="display: flex; align-items: center; gap: 12px;"><span style="color: #10b981; font-weight: bold; font-size: 18px;">✔</span> Real-Time Autonomous Flagging</li>
              <li style="display: flex; align-items: center; gap: 12px;"><span style="color: #10b981; font-weight: bold; font-size: 18px;">✔</span> Standard Network Analysis Graphs</li>
              <li style="display: flex; align-items: center; gap: 12px;"><span style="color: #10b981; font-weight: bold; font-size: 18px;">✔</span> Basic SAR & Compliance Reporting</li>
            </ul>
          </div>
          <button class="btn-pay-plan pricing-btn" data-plan-name="Fintech Starter" data-plan-price="₹1,500" data-plan-desc="Up to 25,000 AI transactions / mo">Pay & Activate Starter</button>
        </div>

        <!-- Pro Plan -->
        <div class="pricing-card">
          <div style="position: absolute; top: -14px; right: 28px; background: linear-gradient(135deg, #4f46e5, #6366f1); color: white; font-size: 11px; font-weight: 800; padding: 6px 14px; border-radius: 20px; box-shadow: 0 4px 12px rgba(79,70,229,0.3); text-transform: uppercase; letter-spacing: 0.5px;">Most Popular</div>
          <div>
            <h3 style="font-size: 22px; font-weight: 800; color: var(--text, #111827); margin-top: 0;">Compliance Pro</h3>
            <p style="font-size: 14px; color: var(--text-muted, #6b7280); min-height: 44px;">Designed for growing Indian NBFCs & regional banks requiring deep investigative graphs & custom dataset tests.</p>
            <div style="margin: 28px 0; padding-bottom: 24px; border-bottom: 1px solid var(--border, #f1f5f9);">
              <span class="price-val" data-monthly="₹3,500" data-quarterly="₹3,150" data-yearly="₹2,800" style="font-size: 44px; font-weight: 900; color: #4f46e5;">₹3,500</span>
              <span style="font-size: 15px; font-weight: 600; color: var(--text-muted, #6b7280);"> / month</span>
              <div class="bill-note" style="font-size: 13px; color: var(--text-muted, #6b7280); margin-top: 4px;">Billed monthly</div>
            </div>
            <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 16px; font-size: 15px; color: var(--text, #374151);">
              <li style="display: flex; align-items: center; gap: 12px;"><span style="color: #4f46e5; font-weight: bold; font-size: 18px;">★</span> Up to 100,000 AI Transactions / mo</li>
              <li style="display: flex; align-items: center; gap: 12px;"><span style="color: #4f46e5; font-weight: bold; font-size: 18px;">★</span> Custom CSV Typology Uploads & Tests</li>
              <li style="display: flex; align-items: center; gap: 12px;"><span style="color: #4f46e5; font-weight: bold; font-size: 18px;">★</span> Multi-Hop Entity Knowledge Graph</li>
              <li style="display: flex; align-items: center; gap: 12px;"><span style="color: #4f46e5; font-weight: bold; font-size: 18px;">★</span> Supabase Persistent Cloud Storage</li>
              <li style="display: flex; align-items: center; gap: 12px;"><span style="color: #4f46e5; font-weight: bold; font-size: 18px;">★</span> Automated PDF Audit & Doc Exporting</li>
            </ul>
          </div>
          <button class="btn-pay-plan pricing-btn" data-plan-name="Compliance Pro" data-plan-price="₹3,500" data-plan-desc="Up to 100,000 AI tx/mo + Supabase storage">Pay & Upgrade to Pro</button>
        </div>

        <!-- Enterprise Custom Plan -->
        <div class="pricing-card">
          <div>
            <h3 style="font-size: 22px; font-weight: 800; color: var(--text, #111827); margin-top: 0;">Enterprise Institutional</h3>
            <p style="font-size: 14px; color: var(--text-muted, #6b7280); min-height: 44px;">For commercial banks & payment aggregators seeking dedicated cloud infrastructure & full SLA.</p>
            <div style="margin: 28px 0; padding-bottom: 24px; border-bottom: 1px solid var(--border, #f1f5f9);">
              <span class="price-val" data-monthly="₹7,500" data-quarterly="₹6,750" data-yearly="₹6,000" style="font-size: 44px; font-weight: 900; color: var(--text, #111827);">₹7,500</span>
              <span style="font-size: 15px; font-weight: 600; color: var(--text-muted, #6b7280);"> / month</span>
              <div class="bill-note" style="font-size: 13px; color: var(--text-muted, #6b7280); margin-top: 4px;">Billed monthly</div>
            </div>
            <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 16px; font-size: 15px; color: var(--text, #374151);">
              <li style="display: flex; align-items: center; gap: 12px;"><span style="color: #10b981; font-weight: bold; font-size: 18px;">✔</span> Unlimited Autonomous AI Processing</li>
              <li style="display: flex; align-items: center; gap: 12px;"><span style="color: #10b981; font-weight: bold; font-size: 18px;">✔</span> Dedicated VPC & On-Prem Supabase DB</li>
              <li style="display: flex; align-items: center; gap: 12px;"><span style="color: #10b981; font-weight: bold; font-size: 18px;">✔</span> Clerk Enterprise SSO & SAML Integrations</li>
              <li style="display: flex; align-items: center; gap: 12px;"><span style="color: #10b981; font-weight: bold; font-size: 18px;">✔</span> Dedicated RBI/AML Compliance Support</li>
            </ul>
          </div>
          <button class="btn-pay-plan pricing-btn" data-plan-name="Enterprise Institutional" data-plan-price="₹7,500" data-plan-desc="Unlimited processing + Dedicated VPC">Subscribe to Enterprise</button>
        </div>
      </div>
    </div>
  </section>

  <!-- ========== CTA BANNER ========== -->
  <section class="cta-banner" id="cta-banner">
    <div class="cta-glow"></div>
    <div class="cta-content">
      <h2>Ready to Transform Your AML Program?</h2>
      <p>Join compliance teams at leading financial institutions using FalconIQ.</p>
      <div class="cta-buttons">
        <a href="#" class="btn-primary btn-large" id="cta-primary">
          <svg viewBox="0 0 20 20" fill="none"><path d="M10 2l8 4-8 4-8-4 8-4zM2 10l8 4 8-4M2 14l8 4 8-4" stroke="white" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
          Launch FalconIQ Platform
        </a>
        <a href="#" class="btn-ghost-white btn-large" id="cta-demo">Book a Demo</a>
      </div>
    </div>
  </section>

  <!-- ========== FOOTER ========== -->
  <footer class="footer" id="footer">
    <div class="footer-container">
      <div class="footer-top">
        <div class="footer-brand">
          <a href="#" class="nav-logo footer-logo">
            <div class="logo-icon">
              <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M16 2L4 7v9c0 7.18 5.15 13.9 12 15.45C22.85 29.9 28 23.18 28 16V7L16 2z" fill="url(#shieldGrad2)" />
                <path d="M12 16l3 3 5-6" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                <defs>
                  <linearGradient id="shieldGrad2" x1="4" y1="2" x2="28" y2="32" gradientUnits="userSpaceOnUse">
                    <stop offset="0%" stop-color="#818cf8"/>
                    <stop offset="100%" stop-color="#4f46e5"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <span class="logo-text">FalconIQ</span>
          </a>
          <p class="footer-tagline">Enterprise AI-Powered AML Investigation Platform for financial institutions.</p>
        </div>
      </div>
      <div class="footer-bottom" style="margin-top: 24px; border-top: 1px solid var(--border, #374151); padding-top: 24px;">
        <p>© 2025 FalconIQ. All rights reserved.</p>
        <div class="footer-socials">
          <a href="#" class="social-link" id="social-twitter">𝕏</a>
          <a href="#" class="social-link" id="social-linkedin">in</a>
          <a href="#" class="social-link" id="social-github">⌥</a>
        </div>
      </div>
    </div>
  </footer>

  <!-- ========== MINIMALIST FLOATING WHATSAPP DIRECT ICON ========== -->
  <div style="position: fixed; bottom: 28px; right: 28px; z-index: 8888;">
    <a href="https://wa.me/919466593517?text=${encodeURIComponent('Hello FalconIQ Executive Team! I would like to inquire about a platform demo and enterprise consultation.')}" target="_blank" title="Chat with an Executive via WhatsApp" style="display: flex; align-items: center; justify-content: center; width: 60px; height: 60px; background: linear-gradient(135deg, #25D366, #128C7E); color: white; border-radius: 50%; box-shadow: 0 8px 25px rgba(37, 211, 102, 0.45); text-decoration: none; transition: transform 0.2s ease, box-shadow 0.2s ease; cursor: pointer;">
      <svg width="34" height="34" viewBox="0 0 24 24" fill="currentColor" style="display: block;">
        <path d="M11.999 0C5.373 0 0 5.373 0 12c0 2.126.556 4.194 1.614 6.014L.108 23.633a.75.75 0 0 0 .911.911l5.728-1.554A11.944 11.944 0 0 0 12 24c6.627 0 12-5.373 12-12S18.627 0 11.999 0zm0 21.818c-1.782 0-3.523-.477-5.05-1.381a.75.75 0 0 0-.585-.078l-4.225 1.146 1.139-4.2a.75.75 0 0 0-.074-.585 9.773 9.773 0 0 1-1.387-5.074c0-5.415 4.403-9.818 9.818-9.818s9.818 4.403 9.818 9.818-4.403 9.818-9.818 9.818z"/>
        <path d="M17.067 14.168l-2.033-.941a1.002 1.002 0 0 0-1.186.273l-.707.88a.5.5 0 0 1-.572.14 8.784 8.784 0 0 1-4.39-4.39.5.5 0 0 1 .14-.572l.88-.707a1.002 1.002 0 0 0 .273-1.186l-.941-2.033A1.003 1.003 0 0 0 7.397 5.12c-.783.208-1.52.92-1.656 1.763-.357 2.215 1.258 5.434 3.75 7.926 2.492 2.492 5.711 4.107 7.926 3.75.843-.136 1.555-.873 1.763-1.656a1.003 1.003 0 0 0-.513-1.135z"/>
      </svg>
    </a>
  </div>
`;
    this.initScripts();
  },

  initScripts() {
    // Dispatch custom event so router can re-init logic if needed
    window.dispatchEvent(new Event("landing:rendered"));
  }
};


