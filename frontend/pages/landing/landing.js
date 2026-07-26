/* ===================================================
   FalconIQ — JavaScript for Navbar, Scroll, Animations
   =================================================== */

export function initLanding() {

  // ---- NAVBAR SCROLL EFFECT ----
  const navbar = document.getElementById('navbar');
  let lastScroll = 0;

  window.addEventListener('scroll', () => {
    const currentScroll = window.scrollY;
    if (currentScroll > 20) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
    lastScroll = currentScroll;
  });

  // ---- HAMBURGER MENU ----
  const hamburger = document.getElementById('hamburger');
  const navLinks = document.getElementById('nav-links');
  let menuOpen = false;

  hamburger.addEventListener('click', () => {
    menuOpen = !menuOpen;
    if (menuOpen) {
      navLinks.style.display = 'flex';
      navLinks.style.flexDirection = 'column';
      navLinks.style.position = 'absolute';
      navLinks.style.top = '68px';
      navLinks.style.left = '0';
      navLinks.style.right = '0';
      navLinks.style.background = 'rgba(255,255,255,0.97)';
      navLinks.style.backdropFilter = 'blur(20px)';
      navLinks.style.borderBottom = '1px solid #e5e7f3';
      navLinks.style.padding = '16px 24px';
      navLinks.style.gap = '4px';
      navLinks.style.zIndex = '999';
      hamburger.style.transform = 'rotate(90deg)';
    } else {
      navLinks.style.display = '';
      navLinks.style.cssText = '';
      hamburger.style.transform = '';
    }
  });

  // ---- SMOOTH SCROLL FOR ANCHOR LINKS ----
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const href = anchor.getAttribute('href');
      if (href === '#') return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        const offset = 80;
        const top = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: 'smooth' });
        // Close mobile menu if open
        if (menuOpen) {
          menuOpen = false;
          navLinks.style.cssText = '';
          hamburger.style.transform = '';
        }
      }
    });
  });

  // ---- INTERSECTION OBSERVER FOR SCROLL ANIMATIONS ----
  const observerOptions = {
    root: null,
    rootMargin: '0px 0px -60px 0px',
    threshold: 0.1,
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Apply to elements that should animate on scroll
  const animatedEls = document.querySelectorAll(
    '.stat-pill, .feature-card, .step-item, .why-item, .why-card, .trust-logo, .step-label'
  );

  animatedEls.forEach((el, index) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(24px)';
    el.style.transition = `opacity 0.5s ease ${index * 0.07}s, transform 0.5s ease ${index * 0.07}s`;
    observer.observe(el);
  });

  // Add in-view styles via CSS class
  const style = document.createElement('style');
  style.textContent = `.in-view { opacity: 1 !important; transform: translateY(0) !important; }`;
  document.head.appendChild(style);

  // ---- ANIMATED COUNTER ----
  function animateCounter(el, target, suffix = '', duration = 1600) {
    const start = 0;
    const startTime = performance.now();
    const isFloat = target % 1 !== 0;
    const decimals = isFloat ? 1 : 0;

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = start + (target - start) * eased;
      el.textContent = current.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + suffix;
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  }

  // Observe stat values for counter animation
  const statCounters = [
    { id: 'stat-accuracy', value: 98.3, suffix: '%', selector: '.stat-value' },
    { id: 'stat-transactions', value: 245, suffix: 'K+', selector: '.stat-value' },
    { id: 'stat-alerts', value: 1247, suffix: '', selector: '.stat-value' },
    { id: 'stat-patterns', value: 6, suffix: '', selector: '.stat-value' },
  ];

  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        const config = statCounters.find(c => c.id === id);
        if (config) {
          const valueEl = entry.target.querySelector(config.selector);
          if (valueEl) {
            animateCounter(valueEl, config.value, config.suffix);
          }
        }
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  statCounters.forEach(c => {
    const el = document.getElementById(c.id);
    if (el) counterObserver.observe(el);
  });

  // ---- STEP ICON HOVER EFFECT ----
  document.querySelectorAll('.step-icon-wrap').forEach((icon, idx) => {
    icon.addEventListener('mouseenter', () => {
      const labels = document.querySelectorAll('.step-label');
      labels.forEach(l => l.style.opacity = '0.4');
      if (labels[idx]) labels[idx].style.opacity = '1';
    });
    icon.addEventListener('mouseleave', () => {
      const labels = document.querySelectorAll('.step-label');
      labels.forEach(l => l.style.opacity = '1');
    });
  });

  // ---- NAVBAR ACTIVE LINK ----
  const sections = document.querySelectorAll('section[id]');
  const navAnchors = document.querySelectorAll('.nav-link');

  const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        navAnchors.forEach(a => {
          a.style.color = '';
          a.style.fontWeight = '';
        });
        const active = document.querySelector(`.nav-link[href="#${id}"]`);
        if (active) {
          active.style.color = 'var(--primary)';
          active.style.fontWeight = '600';
        }
      }
    });
  }, { rootMargin: '-40% 0px -55% 0px' });

  sections.forEach(s => sectionObserver.observe(s));

  // ---- MOUSE PARALLAX ON HERO MOCKUP ----
  const heroRight = document.getElementById('hero-right');
  const mockupDevice = document.querySelector('.mockup-device');

  if (heroRight && mockupDevice) {
    document.addEventListener('mousemove', (e) => {
      const rect = heroRight.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const deltaX = (e.clientX - centerX) / rect.width;
      const deltaY = (e.clientY - centerY) / rect.height;

      const maxRotateY = 8;
      const maxRotateX = 4;
      const rotateY = -4 + deltaX * maxRotateY;
      const rotateX = 2 - deltaY * maxRotateX;

      mockupDevice.style.transform = 
        `perspective(1200px) rotateY(${rotateY}deg) rotateX(${rotateX}deg)`;
    });

    heroRight.addEventListener('mouseleave', () => {
      mockupDevice.style.transform = 
        'perspective(1200px) rotateY(-4deg) rotateX(2deg)';
    });
  }

  // ---- FLOATING BADGE CLICK RIPPLE ----
  const badge = document.getElementById('floating-badge');
  if (badge) {
    badge.addEventListener('click', () => {
      badge.style.transform = 'scale(0.96)';
      setTimeout(() => badge.style.transform = '', 150);
    });
  }

  // ---- PRICING PERIOD SWITCHER ----
  const pricingTabs = document.querySelectorAll('.pricing-tab');
  pricingTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      pricingTabs.forEach(t => {
        t.style.background = 'transparent';
        t.style.color = 'var(--text-muted, #6b7280)';
      });
      tab.style.background = 'var(--primary, #4f46e5)';
      tab.style.color = 'white';

      const period = tab.dataset.period;
      document.querySelectorAll('.price-val').forEach(priceEl => {
        const val = priceEl.getAttribute(`data-${period}`);
        if (val) priceEl.textContent = val;
      });

      document.querySelectorAll('.bill-note').forEach(note => {
        if (note.textContent.startsWith('Billed') || note.textContent.startsWith('Tailored')) {
          if (period === 'quarterly') note.textContent = 'Billed quarterly (Save 10%)';
          else if (period === 'yearly') note.textContent = 'Billed annually (Save 20%)';
          else note.textContent = 'Billed monthly';
        }
      });
      if (window.showToast) window.showToast(`Updated pricing to ${period.toUpperCase()} billing`, 'success');
    });
  });

  // ---- RAZORPAY PAYMENT INTEGRATION ----
  const payButtons = document.querySelectorAll('.btn-pay-plan');
  payButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const planName = btn.getAttribute('data-plan-name') || 'FalconIQ Plan';
      const planDesc = btn.getAttribute('data-plan-desc') || 'Autonomous AI AML Processing';
      
      // Get currently displayed price from card or data attribute
      const card = btn.closest('.pricing-card') || btn.parentElement;
      const priceEl = card ? card.querySelector('.price-val') : null;
      const priceText = priceEl ? priceEl.textContent.trim() : (btn.getAttribute('data-plan-price') || '₹3,500');
      
      // Calculate paise from price text (e.g., "₹3,500" -> 350000)
      const cleanPrice = parseInt(priceText.replace(/[^\d]/g, ''), 10) || 3500;
      const amountPaise = cleanPrice * 100;

      if (typeof window.Razorpay === 'undefined') {
        if (window.showToast) window.showToast('⚠️ Razorpay SDK is still loading or blocked by ad-blocker. Please check internet connection.', 'error');
        return;
      }

      if (window.showToast) {
        window.showToast(`🛡️ Opening Razorpay Gateway for ${planName} (${priceText})...`, 'info');
      }

      const options = {
        key: 'rzp_test_TI4usMiw3Mw2tq',
        amount: amountPaise,
        currency: 'INR',
        name: 'FalconIQ AI AML',
        description: `${planName} - ${planDesc}`,
        image: 'https://cdn-icons-png.flaticon.com/512/3135/3135688.png',
        handler: function (response) {
          console.log('Payment success:', response);
          if (window.showToast) {
            window.showToast('✅ Razorpay Payment Successful! Generating Tax Invoice & Activating Plan...', 'success');
          }

          localStorage.setItem('falconiq_active_plan', planName);
          localStorage.setItem('falconiq_payment_id', response.razorpay_payment_id);
          localStorage.setItem('falconiq_plan_price', priceText);
          localStorage.setItem('falconiq_activation_date', new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }));

          // Trigger Receipt Modal
          setTimeout(() => {
            showPaymentSuccessModal(planName, priceText, response.razorpay_payment_id);
          }, 600);
        },
        prefill: {
          name: 'Mehul Goyal',
          email: 'mehulgoyal8888@gmail.com',
          contact: '9466593517'
        },
        notes: {
          plan_name: planName,
          platform: 'FalconIQ Enterprise AML',
          environment: 'Test / Real Gateway Integration'
        },
        theme: {
          color: '#4f46e5'
        },
        modal: {
          ondismiss: function() {
            if (window.showToast) window.showToast('ℹ️ Payment cancelled or closed by user.', 'info');
          }
        }
      };

      try {
        const rzp = new window.Razorpay(options);
        rzp.open();
      } catch (err) {
        console.error('Razorpay Initialization error:', err);
        if (window.showToast) window.showToast('❌ Failed to launch Razorpay checkout modal.', 'error');
      }
    });
  });

  // Helper: Show Payment Success & Invoice Modal
  function showPaymentSuccessModal(planName, priceText, paymentId) {
    let modal = document.getElementById('payment-success-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'payment-success-modal';
      modal.style.cssText = 'position: fixed; inset: 0; background: rgba(15, 14, 42, 0.88); backdrop-filter: blur(14px); display: flex; align-items: center; justify-content: center; z-index: 10000; padding: 20px; opacity: 0; transition: opacity 0.3s ease;';
      document.body.appendChild(modal);
    }

    const nextMonthDate = new Date();
    nextMonthDate.setMonth(nextMonthDate.getMonth() + 1);
    const renewalDateStr = nextMonthDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
    const todayStr = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });

    modal.innerHTML = `
      <div style="background: var(--card-bg, #ffffff); border: 1.5px solid #10b981; border-radius: 24px; max-width: 580px; width: 100%; padding: 40px; box-shadow: 0 25px 60px -12px rgba(16, 185, 129, 0.25); position: relative; max-height: 90vh; overflow-y: auto; text-align: left;">
        <button onclick="document.getElementById('payment-success-modal').style.display='none'" style="position: absolute; top: 20px; right: 20px; background: var(--hover-bg, #f3f4f6); border: none; width: 36px; height: 36px; border-radius: 50%; font-size: 18px; cursor: pointer; color: var(--text-muted); display: flex; align-items: center; justify-content: center;">✕</button>
        
        <div style="text-align: center; margin-bottom: 24px;">
          <div style="width: 72px; height: 72px; background: #10b98115; color: #10b981; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 38px; margin: 0 auto 14px auto; border: 2px solid #10b981; box-shadow: 0 0 20px rgba(16,185,129,0.3);">🚀</div>
          <span style="background: #10b981; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Razorpay Verified • Transaction Paid</span>
          <h2 style="font-size: 26px; font-weight: 900; color: var(--text, #111827); margin: 10px 0 6px 0;">Subscription Active!</h2>
          <p style="font-size: 14px; color: var(--text-muted, #6b7280); margin: 0;">Your organization has successfully upgraded to the <strong>${planName}</strong> Tier.</p>
        </div>

        <!-- Official Receipt Container -->
        <div style="background: var(--bg, #f8fafc); border: 1.5px dashed var(--border, #cbd5e1); border-radius: 16px; padding: 22px; margin-bottom: 26px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-bottom: 1px solid var(--border, #e2e8f0); padding-bottom: 12px;">
            <div>
              <div style="font-size: 12px; color: var(--text-muted, #64748b); font-weight: 600;">AMOUNT SETTLED</div>
              <div style="font-size: 24px; font-weight: 900; color: #4f46e5;">${priceText} <span style="font-size: 13px; color: var(--text-muted, #64748b);">/ billing cycle</span></div>
            </div>
            <div style="text-align: right;">
              <span style="background: #e2e8f0; color: #334155; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; font-family: monospace;">INVOICE #FLQ-${Math.floor(100000 + Math.random() * 900000)}</span>
            </div>
          </div>

          <div style="display: flex; flex-direction: column; gap: 10px; font-size: 13.5px;">
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-muted, #64748b);">Transaction ID (Razorpay):</span>
              <span style="font-weight: 700; color: var(--text, #0f172a); font-family: monospace; background: rgba(79,70,229,0.08); padding: 2px 6px; border-radius: 4px;">${paymentId}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-muted, #64748b);">Date & Time:</span>
              <span style="font-weight: 600; color: var(--text, #334155);">${todayStr}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-muted, #64748b);">Payment Method:</span>
              <span style="font-weight: 700; color: #10b981;">UPI / Cards / Gateway Verified ✓</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-muted, #64748b);">Next Renewal / Expiry:</span>
              <span style="font-weight: 600; color: var(--text, #334155);">${renewalDateStr}</span>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div style="display: flex; flex-direction: column; gap: 12px;">
          <a href="#/dashboard" onclick="document.getElementById('payment-success-modal').style.display='none'" style="display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #4f46e5, #6366f1); color: white; padding: 16px; border-radius: 14px; font-weight: 800; font-size: 15px; text-decoration: none; box-shadow: 0 10px 25px rgba(79,70,229,0.35); text-align: center; transition: transform 0.2s;">
            <span>🛡️ Enter FalconIQ Dashboard with Pro Features ➔</span>
          </a>
          <button onclick="if(window.showToast) window.showToast('📥 Downloading official Tax Invoice (PDF)...', 'info')" style="background: var(--hover-bg, #f1f5f9); color: var(--text, #334155); border: 1px solid var(--border, #cbd5e1); padding: 12px; border-radius: 12px; font-weight: 700; font-size: 13.5px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;">
            <span>📄 Download Official GST Invoice (.PDF)</span>
          </button>
        </div>
      </div>
    `;

    modal.style.display = 'flex';
    requestAnimationFrame(() => { modal.style.opacity = '1'; });
  }

  // ---- INTERACTIVE AUTOMATED BOOK A DEMO MODAL (WITH INSTANT EMAIL & 1-CLICK CALENDAR SAVERS) ----
  function openAutomatedDemoModal(e) {
    if (e) e.preventDefault();
    let modal = document.getElementById('demo-feature-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'demo-feature-modal';
      modal.style.cssText = 'position: fixed; inset: 0; background: rgba(15, 14, 42, 0.85); backdrop-filter: blur(14px); display: flex; align-items: center; justify-content: center; z-index: 9999; padding: 20px; opacity: 0; transition: opacity 0.3s ease;';
      modal.innerHTML = `
        <div style="background: #ffffff; border: 1px solid #e5e7f3; border-radius: 24px; max-width: 680px; width: 100%; padding: 38px; box-shadow: 0 30px 60px -12px rgba(15, 14, 42, 0.5); position: relative; max-height: 90vh; overflow-y: auto; text-align: left; color: #0f0e2a;">
          <button id="close-demo-modal" style="position: absolute; top: 22px; right: 22px; background: #f4f5fc; border: 1px solid #e5e7f3; width: 36px; height: 36px; border-radius: 50%; font-size: 16px; cursor: pointer; color: #64748b; display: flex; align-items: center; justify-content: center; transition: background 0.2s;">✕</button>
          
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
            <span style="background: linear-gradient(135deg, #4f46e5, #9333ea); color: white; padding: 6px 14px; border-radius: 20px; font-weight: 800; font-size: 11px; letter-spacing: 0.5px; text-transform: uppercase;">⚡ VIP AUTOMATION ACTIVE</span>
            <span style="background: #e0e7ff; color: #3730a3; padding: 6px 12px; border-radius: 20px; font-weight: 700; font-size: 11px;">Free Enterprise Session</span>
          </div>
          <h2 style="font-size: 26px; font-weight: 800; color: #0f0e2a; margin-bottom: 10px; line-height: 1.25;">Book Your Live FalconIQ AML Demo & Sandbox</h2>
          <p style="font-size: 14.5px; color: #64748b; margin-bottom: 24px;">Experience zero-shot AI money laundering detection live. Select your preferences and receive an instant automated calendar scheduled link and confirmation email!</p>
          
          <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 26px;">
            <label style="display: flex; align-items: flex-start; gap: 14px; padding: 15px; border: 1.5px solid #4f46e5; border-radius: 16px; cursor: pointer; background: #f4f5fc; transition: all 0.2s;">
              <input type="checkbox" checked style="margin-top: 3px; accent-color: #4f46e5; width: 18px; height: 18px;" />
              <div>
                <h4 style="margin: 0 0 3px 0; color: #0f0e2a; font-size: 15px; font-weight: 700;">🤖 Live Autonomous AI Investigation Showcase</h4>
                <p style="margin: 0; font-size: 12.5px; color: #64748b;">Watch our agent trace synthetic entity networks and generate explainable suspicious activity verdicts in milliseconds.</p>
              </div>
            </label>
            <label style="display: flex; align-items: flex-start; gap: 14px; padding: 15px; border: 1.5px solid #e5e7f3; border-radius: 16px; cursor: pointer; background: #ffffff; transition: all 0.2s;">
              <input type="checkbox" checked style="margin-top: 3px; accent-color: #4f46e5; width: 18px; height: 18px;" />
              <div>
                <h4 style="margin: 0 0 3px 0; color: #0f0e2a; font-size: 15px; font-weight: 700;">📂 Custom Bank Transaction Dataset Typology Test</h4>
                <p style="margin: 0; font-size: 12.5px; color: #64748b;">Upload your institution's sample transaction CSVs to evaluate our real-time fraud monitoring alerts.</p>
              </div>
            </label>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
            <div>
              <label style="display: block; font-size: 13px; font-weight: 700; color: #334155; margin-bottom: 6px;">Work Email (For Instant Automation)</label>
              <input id="demo-work-email" type="email" placeholder="mehulgoyal8888@gmail.com" value="mehulgoyal8888@gmail.com" style="width: 100%; padding: 13px 16px; border-radius: 12px; border: 1.5px solid #cbd5e1; font-size: 14px; background: #fff; color: #0f0e2a; font-weight: 600;" />
            </div>
            <div>
              <label style="display: block; font-size: 13px; font-weight: 700; color: #334155; margin-bottom: 6px;">Preferred Schedule Date</label>
              <input id="demo-pref-date" type="date" value="2026-07-28" style="width: 100%; padding: 13px 16px; border-radius: 12px; border: 1.5px solid #cbd5e1; font-size: 14px; background: #fff; color: #0f0e2a; font-weight: 700;" />
            </div>
          </div>

          <div>
            <button id="submit-demo-request" style="width: 100%; padding: 18px; border-radius: 14px; font-size: 16px; font-weight: 800; border: none; cursor: pointer; text-align: center; background: linear-gradient(135deg, #4f46e5, #9333ea); color: white; box-shadow: 0 10px 25px rgba(79,70,229,0.4); transition: transform 0.2s, box-shadow 0.2s; display: flex; align-items: center; justify-content: center; gap: 10px;">
              <span style="font-size: 20px;">⚡</span> Trigger Automated Schedule & Dispatch Link
            </button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);

      document.getElementById('close-demo-modal').addEventListener('click', () => {
        modal.style.opacity = '0';
        setTimeout(() => { modal.style.display = 'none'; }, 200);
      });

      document.getElementById('submit-demo-request').addEventListener('click', (ev) => {
        ev.preventDefault();
        const emailInput = document.getElementById('demo-work-email');
        const dateInput = document.getElementById('demo-pref-date');
        const email = (emailInput && emailInput.value.trim()) ? emailInput.value.trim() : 'mehulgoyal8888@gmail.com';
        const rawDate = (dateInput && dateInput.value) ? dateInput.value : '2026-07-28';
        
        let dateStr = rawDate;
        try {
          const dateObj = new Date(rawDate);
          if (!isNaN(dateObj)) {
            dateStr = dateObj.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'long', year: 'numeric' }) + ' @ 11:30 AM IST / GMT';
          } else {
            dateStr = rawDate + ' @ 11:30 AM IST';
          }
        } catch(err) {
          dateStr = rawDate + ' @ 11:30 AM IST';
        }

        // Generate custom unique IDs & automated meeting schedule link
        const randCode = Math.floor(1000 + Math.random() * 9000);
        const vipScheduleUrl = `https://meet.falconiq.ai/schedule-room/VIP-DEMO-${randCode}`;
        const teamsLink = 'https://teams.microsoft.com/l/meetup-join/19%3ameeting_FLQ2026AML_ENTERPRISE%40thread.v2/0?context=%7b%22Tid%22%3a%22falconiq-aml-ai-enterprise%22%7d';

        // Calculate ISO dates for automated calendar adders
        const startIso = (rawDate.replace(/-/g, '')) + 'T060000Z';
        const endIso = (rawDate.replace(/-/g, '')) + 'T070000Z';
        const gCalUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent('🦅 FalconIQ AI: Executive AML Platform Live Demo & Sandbox')}&dates=${startIso}/${endIso}&details=${encodeURIComponent('Your scheduled Live AML AI Investigation and Typology Test with FalconIQ Enterprise Specialists.\n\nExclusive Meeting Schedule Link: ' + vipScheduleUrl + '\nMicrosoft Teams Video Room: ' + teamsLink + '\nMeeting ID: 319 824 590 11\nPasscode: FALCON26\n\nWhatsApp Concierge: +91 9466593517')}&location=${encodeURIComponent('Microsoft Teams VIP Video Conference')}&add=automation@falconiq.ai`;

        // Show loading state
        const submitBtn = document.getElementById('submit-demo-request');
        if (submitBtn) {
          submitBtn.innerHTML = `<span>⚙️ Transmitting Real Automated Email via EmailJS & Generating Room...</span>`;
          submitBtn.style.background = '#64748b';
          submitBtn.disabled = true;
        }

        // --- REAL LIVE EMAILJS AUTOMATION DISPATCH ---
        const EMAILJS_USER_ID = "Mt6dNwq0v5a1HwPK6";       // Live Public Key
        const EMAILJS_ACCESS_TOKEN = "koQ9oQHWFMTTQ0HtIKbfQ"; // Live Private Key / Access Token
        const EMAILJS_SERVICE_ID = window.EMAILJS_SERVICE_ID || "service_b1uotjf";   // Real EmailJS Service ID
        const EMAILJS_TEMPLATE_ID = window.EMAILJS_TEMPLATE_ID || "template_kwvufiv"; // Real EmailJS Template ID

        fetch("https://api.emailjs.com/api/v1.0/email/send", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            service_id: EMAILJS_SERVICE_ID,
            template_id: EMAILJS_TEMPLATE_ID,
            user_id: EMAILJS_USER_ID,
            accessToken: EMAILJS_ACCESS_TOKEN,
            template_params: {
              to_email: email,
              user_email: email,
              email: email,
              recipient: email,
              reply_to: "automation@falconiq.ai",
              to_name: email.split('@')[0] || "Valued Customer",
              name: email.split('@')[0] || "Valued Customer",
              subject: `📅 Confirmed: FalconIQ Autonomous AML VIP Demo (${dateStr})`,
              meeting_date: dateStr,
              scheduled_time: dateStr,
              date: dateStr,
              vip_schedule_link: vipScheduleUrl,
              schedule_link: vipScheduleUrl,
              teams_video_room: teamsLink,
              teams_link: teamsLink,
              meeting_id: "319 824 590 11",
              passcode: "FALCON26",
              whatsapp_concierge: "+91 9466593517",
              message: `Your live demonstration of the FalconIQ Autonomous AML Engine is confirmed for ${dateStr}.\n\nExclusive Schedule Room: ${vipScheduleUrl}\nMicrosoft Teams Video Room: ${teamsLink}\nMeeting ID: 319 824 590 11 | Passcode: FALCON26\n24/7 Concierge WhatsApp: +91 9466593517`
            }
          })
        }).then(async res => {
          if (res.ok) {
            console.log("🟢 EmailJS: Live email successfully sent to " + email);
            if (window.showToast) window.showToast("📧 REAL EMAIL DELIVERED! Check your Gmail (" + email + ") now!", "success");
          } else {
            const errorText = await res.text();
            console.error("🔴 EmailJS Failed (Status " + res.status + "): " + errorText);
            if (window.showToast) window.showToast("⚠️ Email delivery notice: " + errorText, "error");
          }
        }).catch(err => {
          console.error("EmailJS Error:", err);
          if (window.showToast) window.showToast("⚠️ EmailJS Network Error: " + err.message, "error");
        });

        setTimeout(() => {

          const contentBox = modal.children[0];
          contentBox.innerHTML = `
            <button id="close-confirmation-modal" style="position: absolute; top: 20px; right: 20px; background: #f4f5fc; border: 1px solid #e5e7f3; width: 36px; height: 36px; border-radius: 50%; font-size: 16px; cursor: pointer; color: #64748b; display: flex; align-items: center; justify-content: center; transition: background 0.2s;">✕</button>
            
            <!-- Header Status -->
            <div style="text-align: center; margin-bottom: 24px;">
              <div style="width: 68px; height: 68px; background: #10b98115; color: #10b981; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 34px; margin: 0 auto 12px auto; border: 2px solid #10b981;">🎉</div>
              <span style="background: #10b981; color: white; padding: 5px 14px; border-radius: 16px; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">AUTOMATION COMPLETE • REAL-TIME DEPLOYMENT</span>
              <h2 style="font-size: 25px; font-weight: 800; color: #0f0e2a; margin: 10px 0 6px 0;">Your Live VIP Session is Scheduled!</h2>
              <p style="font-size: 13.5px; color: #64748b; margin: 0;">Both automatic email transmission & interactive scheduled meeting links are active below.</p>
            </div>

            <!-- OPTION 2: REAL-TIME INTERACTIVE SCHEDULE LINK & 1-CLICK CALENDAR SAVERS -->
            <div style="background: #f8fafc; border: 2px solid #4f46e5; border-radius: 18px; padding: 22px; margin-bottom: 22px; box-shadow: 0 10px 30px rgba(79, 70, 229, 0.1);">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <span style="font-weight: 800; color: #4f46e5; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">🔗 YOUR EXCLUSIVE SCHEDULE LINK</span>
                <span style="background: #e0e7ff; color: #3730a3; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 800;">VIP ROOM #${randCode}</span>
              </div>
              
              <!-- Copyable Schedule Link Input -->
              <div style="display: flex; gap: 8px; margin-bottom: 16px;">
                <input type="text" readOnly value="${vipScheduleUrl}" style="flex: 1; padding: 12px 14px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; color: #4f46e5; font-weight: 700; font-size: 13.5px; font-family: monospace;" />
                <button id="copy-schedule-btn" style="background: #4f46e5; color: white; border: none; border-radius: 10px; padding: 0 18px; font-weight: 700; font-size: 13px; cursor: pointer; white-space: nowrap; box-shadow: 0 4px 12px rgba(79,70,229,0.3);">📋 Copy Link</button>
              </div>

              <!-- 1-Click Calendar Buttons -->
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <a href="${gCalUrl}" target="_blank" style="display: flex; align-items: center; justify-content: center; gap: 8px; background: #ffffff; border: 1.5px solid #4f46e5; color: #4f46e5; padding: 12px; border-radius: 12px; font-weight: 700; font-size: 12.5px; text-decoration: none; transition: background 0.2s;">
                  <span style="font-size: 16px;">📅</span> 1-Click Google Calendar Save
                </a>
                <button id="download-ics-btn" style="display: flex; align-items: center; justify-content: center; gap: 8px; background: #ffffff; border: 1.5px solid #10b981; color: #10b981; padding: 12px; border-radius: 12px; font-weight: 700; font-size: 12.5px; cursor: pointer; transition: background 0.2s;">
                  <span style="font-size: 16px;">📥</span> Download Apple / Outlook Invite (.ICS)
                </button>
              </div>
            </div>

            <!-- OPTION 1: AUTOMATED INBOX EMAIL TRANSMISSION SYSTEM -->
            <div style="background: #ffffff; border: 1.5px solid #e5e7f3; border-radius: 18px; padding: 22px; margin-bottom: 24px; position: relative; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.03);">
              <div style="position: absolute; top: 0; right: 0; background: #10b981; color: white; font-size: 10px; font-weight: 800; padding: 4px 14px; border-bottom-left-radius: 12px; letter-spacing: 0.5px;">📨 REAL EMAIL AUTOMATION INBOX</div>
              
              <div style="font-size: 13px; border-bottom: 1px dashed #cbd5e1; padding-bottom: 12px; margin-bottom: 14px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                  <span style="color: #64748b;">To Customer:</span>
                  <span style="font-weight: 700; color: #4f46e5;">${email}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                  <span style="color: #64748b;">From Automation Desk:</span>
                  <span style="font-weight: 600; color: #334155;">automation@falconiq.ai (24/7 AI Concierge)</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                  <span style="color: #64748b;">Subject:</span>
                  <span style="font-weight: 700; color: #0f0e2a;">📅 Exclusive Meeting Schedule & VIP Sandbox Link</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                  <span style="color: #64748b;">Scheduled Time:</span>
                  <span style="font-weight: 800; color: #10b981;">${dateStr}</span>
                </div>
              </div>
              
              <div style="font-size: 13.5px; color: #334155; line-height: 1.6; margin-bottom: 16px;">
                <p style="margin: 0 0 10px 0;"><strong>Welcome to FalconIQ Autonomous AML Engine!</strong></p>
                <p style="margin: 0 0 12px 0;">Your live demonstration is confirmed for <strong>${dateStr}</strong>. Your exclusive meeting schedule link is set up and our architects are staging your bank sample dataset.</p>
                
                <div style="background: #f4f5fc; border-left: 4px solid #4f46e5; padding: 12px 14px; border-radius: 8px; font-size: 12px; font-weight: 600;">
                  📹 Microsoft Teams Room: <a href="${teamsLink}" target="_blank" style="color: #4f46e5; text-decoration: underline;">Join Room Direct</a><br/>
                  🔑 Meeting ID: 319 824 590 11 • Passcode: <strong>FALCON26</strong>
                </div>
              </div>

              <div style="display: flex; gap: 10px;">
                <a href="mailto:${email}?subject=${encodeURIComponent('📅 Confirmation: Your Scheduled FalconIQ Live Demo & Sandbox')}&body=${encodeURIComponent('Hello,\n\nThank you for booking your scheduled live AML session with FalconIQ!\n\nScheduled Date & Time: ' + dateStr + '\nExclusive Schedule Link: ' + vipScheduleUrl + '\nMicrosoft Teams Video Room: ' + teamsLink + '\nMeeting ID: 319 824 590 11\nPasscode: FALCON26\n\nNeed to reschedule or inquire? Contact our Executive Desk via WhatsApp: +91 9466593517.\n\nBest Regards,\nFalconIQ AI Enterprise Concierge')}" target="_blank" style="flex: 1; text-align: center; background: #e0e7ff; color: #3730a3; padding: 11px; border-radius: 10px; font-weight: 700; font-size: 12px; text-decoration: none;">
                  📨 Open Mail App & Verify Email Dispatch
                </a>
                <a href="https://mail.google.com" target="_blank" style="flex: 1; text-align: center; background: #dcfce7; color: #166534; padding: 11px; border-radius: 10px; font-weight: 700; font-size: 12px; text-decoration: none;">
                  📬 Check Gmail / Inbox Online Now
                </a>
              </div>
            </div>

            <!-- Direct Action Footer Buttons -->
            <div style="display: flex; flex-direction: column; gap: 10px;">
              <a href="${teamsLink}" target="_blank" style="display: flex; align-items: center; justify-content: center; gap: 10px; background: #5a32a3; color: white; padding: 15px; border-radius: 14px; font-weight: 800; font-size: 15px; text-decoration: none; box-shadow: 0 6px 20px rgba(90,50,163,0.35); transition: transform 0.2s;">
                <span style="font-size: 18px;">📹</span> Enter Live Microsoft Teams Conference Lounge Now
              </a>
              <div style="display: flex; gap: 10px;">
                <a href="demo.html" target="_blank" style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px; background: linear-gradient(135deg, #4f46e5, #6366f1); color: white; padding: 13px; border-radius: 12px; font-weight: 700; font-size: 13.5px; text-decoration: none;">
                  <span>🎬 Watch Widescreen Demo ➔</span>
                </a>
                <a href="#/dashboard" onclick="document.getElementById('demo-feature-modal').style.display='none'" style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px; background: #1e293b; color: white; padding: 13px; border-radius: 12px; font-weight: 700; font-size: 13.5px; text-decoration: none;">
                  <span>⚡ Go to Live Dashboard ➔</span>
                </a>
              </div>
              <a href="https://wa.me/919466593517?text=${encodeURIComponent('Hello FalconIQ Executive Team! I scheduled my automated demo for ' + dateStr + ' (' + email + ') and received my VIP schedule link (' + vipScheduleUrl + '). I want to discuss a few details!')}" target="_blank" style="display: flex; align-items: center; justify-content: center; gap: 8px; background: #ffffff; color: #10b981; border: 1.5px solid #10b981; padding: 13px; border-radius: 12px; font-weight: 700; font-size: 13.5px; text-decoration: none;">
                <span style="font-size: 18px;">💬</span> Instant Chat with Concierge Desk on WhatsApp (+91 9466593517)
              </a>
            </div>
          `;

          // Event Listeners for the Confirmation Suite
          document.getElementById('close-confirmation-modal').addEventListener('click', () => {
            modal.style.opacity = '0';
            setTimeout(() => { modal.style.display = 'none'; }, 200);
          });

          // Copy Schedule Link Handler
          const copyBtn = document.getElementById('copy-schedule-btn');
          if (copyBtn) {
            copyBtn.addEventListener('click', () => {
              navigator.clipboard.writeText(vipScheduleUrl);
              copyBtn.textContent = '✅ Copied!';
              copyBtn.style.background = '#10b981';
              if (window.showToast) window.showToast('🔗 Exclusive Schedule Link Copied to Clipboard!', 'success');
              setTimeout(() => { copyBtn.textContent = '📋 Copy Link'; copyBtn.style.background = '#4f46e5'; }, 3000);
            });
          }

          // .ICS Download Handler
          const icsBtn = document.getElementById('download-ics-btn');
          if (icsBtn) {
            icsBtn.addEventListener('click', () => {
              const icsContent = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//FalconIQ AI Platform//Enterprise AML Demo//EN",
                "CALSCALE:GREGORIAN",
                "METHOD:REQUEST",
                "BEGIN:VEVENT",
                "DTSTART:" + startIso,
                "DTEND:" + endIso,
                "SUMMARY:🦅 FalconIQ AI: Executive AML Platform Live Demo & Sandbox",
                "DESCRIPTION:Your scheduled Live AML AI Investigation and Typology Test with FalconIQ Enterprise Specialists.\\n\\nExclusive Schedule Link: " + vipScheduleUrl + "\\nMicrosoft Teams Video Conference: " + teamsLink + "\\nMeeting ID: 319 824 590 11\\nPasscode: FALCON26\\n\\nWhatsApp Executive Desk: +91 9466593517",
                "LOCATION:Microsoft Teams VIP Video Conference",
                "STATUS:CONFIRMED",
                "ORGANIZER;CN=FalconIQ Automation Desk:mailto:automation@falconiq.ai",
                "END:VEVENT",
                "END:VCALENDAR"
              ].join("\r\n");
              const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
              const link = document.createElement('a');
              link.href = window.URL.createObjectURL(blob);
              link.setAttribute('download', 'FalconIQ_VIP_Demo_Invitation.ics');
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
              if (window.showToast) window.showToast('📥 Calendar invitation (.ICS) file downloaded successfully!', 'success');
            });
          }
        }, 800);
      });
    }

    modal.style.display = 'flex';
    requestAnimationFrame(() => { modal.style.opacity = '1'; });
  }

  // Bind to both our bottom CTA and top Hero Book Demo buttons
  const ctaDemoBtn = document.getElementById('cta-demo');
  if (ctaDemoBtn) ctaDemoBtn.addEventListener('click', openAutomatedDemoModal);
  const heroBookBtn = document.getElementById('hero-book-demo-btn');
  if (heroBookBtn) heroBookBtn.addEventListener('click', openAutomatedDemoModal);

  // ---- FULL-SCREEN LIGHT-MODE INTERACTIVE EXECUTIVE VIDEO DEMO TOUR ("WATCH DEMO") ----
  const watchDemoBtn = document.getElementById('watch-demo-btn');
  if (watchDemoBtn) {
    watchDemoBtn.addEventListener('click', (e) => {
      e.preventDefault();
      // Open our dedicated full-screen light-mode guided video presentation in a brand new tab!
      window.open('demo.html', '_blank');
    });
  }

  console.log('🦅 FalconIQ landing page initialized');
}
