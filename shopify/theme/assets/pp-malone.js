/* Post & Porch - Malone Mailbox LP v1 - vanilla JS, no deps */
(function () {
  'use strict';

  /* ---- PostHog init (guarded placeholder token) -------------------------- */
  var POSTHOG_TOKEN = 'phc_xGcXQc3AqMVDMTCo32sRQL7j29L33JhL6DDV8Ku3UEDp';
  var phReady = false;
  (function initPostHog() {
    if (!POSTHOG_TOKEN || POSTHOG_TOKEN.indexOf('__') === 0) {
      // No real project wired up yet - no-op tracker so calls below never throw.
      window.posthog = window.posthog || {
        capture: function () {},
        init: function () {}
      };
      return;
    }
    try {
      /* eslint-disable */
      !function (t, e) { var o, n, p, r; e.__SV || (window.posthog = e, e._i = [], e.init = function (i, s, a) { function g(t, e) { var o = e.split("."); 2 == o.length && (t = t[o[0]], e = o[1]); t[e] = function () { t.push([e].concat(Array.prototype.slice.call(arguments, 0))) } } (p = t.createElement("script")).type = "text/javascript", p.crossOrigin = "anonymous", p.async = !0, p.src = s.api_host.replace(".i.posthog.com", "-assets.i.posthog.com") + "/static/array.js", (r = t.getElementsByTagName("script")[0]).parentNode.insertBefore(p, r); var u = e; for (void 0 !== a ? u = e[a] = [] : a = "posthog", u.people = u.people || [], u.toString = function (t) { var e = "posthog"; return "posthog" !== a && (e += "." + a), t || (e += " (stub)"), e }, u.people.toString = function () { return u.toString(1) + ".people (stub)" }, o = "init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey getNextSurveyStep identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug".split(" "), n = 0; n < o.length; n++) g(u, o[n]); e._i.push([i, s, a]) }, e.__SV = 1) }(document, window.posthog || []);
      /* eslint-enable */
      posthog.init(POSTHOG_TOKEN, { api_host: 'https://us.i.posthog.com', person_profiles: 'identified_only' });
      phReady = true;
    } catch (e) {
      window.posthog = window.posthog || { capture: function () {}, init: function () {} };
    }
  })();

  function track(event, props) {
    try {
      if (window.posthog && typeof window.posthog.capture === 'function') {
        window.posthog.capture(event, props || {});
      }
    } catch (e) { /* never block the page on analytics */ }
  }

  /* ---- lp_pageview --------------------------------------------------------*/
  track('lp_pageview', { lp_version: 'malone-v1' });

  /* ---- lp_cta_clicked -------------------------------------------------- */
  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-cta-location]');
    if (!el) return;
    track('lp_cta_clicked', { cta_location: el.getAttribute('data-cta-location') });
  });

  /* ---- lp_section_viewed (IntersectionObserver) -------------------------- */
  var seenSections = {};
  var sections = document.querySelectorAll('[data-section]');
  if ('IntersectionObserver' in window && sections.length) {
    var sectionObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var id = entry.target.getAttribute('data-section');
        if (entry.isIntersecting && !seenSections[id]) {
          seenSections[id] = true;
          track('lp_section_viewed', { section_id: id });
        }
      });
    }, { threshold: 0.4 });
    sections.forEach(function (s) { sectionObserver.observe(s); });
  }

  /* ---- lp_faq_opened ------------------------------------------------------*/
  document.querySelectorAll('.faq-item').forEach(function (d) {
    d.addEventListener('toggle', function () {
      if (d.open) {
        track('lp_faq_opened', { question: d.getAttribute('data-question') || '' });
      }
    });
  });

  /* ---- Scroll reveal (with no-content-hidden failsafe) --------------------*/
  var revealEls = document.querySelectorAll('.reveal');
  function revealAll() {
    revealEls.forEach(function (el) { el.classList.add('is-visible'); });
  }
  var prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!('IntersectionObserver' in window) || prefersReduced) {
    revealAll();
  } else {
    var revealObserver = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(function (el) { revealObserver.observe(el); });
    // Failsafe: never let a broken observer hide content permanently.
    setTimeout(revealAll, 1500);
  }

  /* ---- Install video: lazy play/pause on scroll into view ------------------*/
  document.querySelectorAll('[data-video-autoplay]').forEach(function (wrap) {
    var video = wrap.querySelector('video');
    if (!video) return;
    var posterUrl = video.getAttribute('data-poster');  // poster is deferred so it never competes with the hero image
    if (posterUrl) {
      if ('IntersectionObserver' in window) {
        var pObserver = new IntersectionObserver(function (entries, obs) {
          if (entries[0].isIntersecting) { video.setAttribute('poster', posterUrl); obs.disconnect(); }
        }, { rootMargin: '800px 0px' });
        pObserver.observe(wrap);
      } else { video.setAttribute('poster', posterUrl); }
    }
    if ('IntersectionObserver' in window) {
      var vObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var p = video.play();
            if (p && typeof p.catch === 'function') p.catch(function () { /* autoplay blocked - poster stays visible */ });
          } else {
            video.pause();
          }
        });
      }, { threshold: 0.5 });
      vObserver.observe(wrap);
    } else {
      video.setAttribute('preload', 'metadata');
    }
  });

  /* ---- Patina before/after slider ------------------------------------------*/
  document.querySelectorAll('.ph-slider').forEach(function (slider) {
    var after = slider.querySelector('.ph-slider__after');
    var handle = slider.querySelector('.ph-slider__handle');
    var afterImg = after ? after.querySelector('img') : null;

    function setPos(pct) {
      pct = Math.max(2, Math.min(98, pct));
      after.style.width = pct + '%';
      handle.style.left = pct + '%';
      handle.setAttribute('aria-valuenow', String(Math.round(pct)));
      handle.setAttribute('aria-valuetext', Math.round(100 - pct) + ' percent patina');
      if (afterImg) afterImg.style.width = (100 / (pct / 100)) + '%';
    }

    function syncWidth() {
      var rect = slider.getBoundingClientRect();
      if (afterImg) afterImg.style.width = rect.width + 'px';
    }
    syncWidth();
    window.addEventListener('resize', syncWidth);

    function pctFromClientX(clientX) {
      var rect = slider.getBoundingClientRect();
      return ((clientX - rect.left) / rect.width) * 100;
    }

    var dragging = false;

    function onMove(clientX) {
      setPos(pctFromClientX(clientX));
    }

    handle.addEventListener('mousedown', function (e) { dragging = true; e.preventDefault(); });
    window.addEventListener('mouseup', function () { dragging = false; });
    window.addEventListener('mousemove', function (e) {
      if (!dragging) return;
      onMove(e.clientX);
    });
    slider.addEventListener('click', function (e) {
      if (e.target.closest('.ph-slider__handle')) return;
      onMove(e.clientX);
    });

    handle.addEventListener('touchstart', function () { dragging = true; }, { passive: true });
    window.addEventListener('touchend', function () { dragging = false; });
    slider.addEventListener('touchmove', function (e) {
      if (!dragging) return;
      if (e.touches && e.touches[0]) onMove(e.touches[0].clientX);
    }, { passive: true });

    handle.addEventListener('keydown', function (e) {
      var cur = parseFloat(after.style.width) || 50;
      if (e.key === 'ArrowLeft') { setPos(cur - 5); e.preventDefault(); }
      if (e.key === 'ArrowRight') { setPos(cur + 5); e.preventDefault(); }
    });
  });
})();

/* ===== Overlay guard (Shopify only): hide third-party popups that app embeds inject on this page.
   The cookie/privacy banner is intentionally NOT suppressed (compliance = client's call). ===== */
(function () {
  var SEL = ['[id*="alia" i]', '[class*="alia-" i]', '[class*="klaviyo-form" i][role="dialog"]', '[id*="privy" i]', '[class*="popup" i][class*="modal" i]'];
  var sticky = document.querySelector('.sticky-cta, .sticky-bar, [data-sticky-cta]');
  var suppressed = false;
  function hide(el) { if (!el || el === sticky || (sticky && sticky.contains(el))) return; suppressed = true; if (/^alia-root/.test(el.id)) { el.remove(); return; } el.style.setProperty('display', 'none', 'important'); }
  /* Popups lock page scroll (Alia sets body.style.overflow=hidden on mount). Once we suppress one, its unlock never runs — release it ourselves. */
  function unlock() {
    if (!suppressed) return;
    [document.body, document.documentElement].forEach(function (el) {
      var st = el.style;
      if (/hidden/.test(st.overflow)) st.removeProperty('overflow');
      if (/hidden/.test(st.overflowY)) st.removeProperty('overflow-y');
      if (st.position === 'fixed') { st.removeProperty('position'); st.removeProperty('top'); st.removeProperty('width'); }
    });
  }
  function sweep() {
    SEL.forEach(function (s) { try { document.querySelectorAll(s).forEach(hide); } catch (e) {} });
    var vw = window.innerWidth, vh = window.innerHeight;
    document.querySelectorAll('body > *, body > * > *').forEach(function (el) {
      if (el === sticky || (sticky && sticky.contains(el)) || el.tagName === 'MAIN' || el.tagName === 'HEADER' || el.tagName === 'FOOTER') return;
      var cs = getComputedStyle(el); if (cs.position !== 'fixed') return;
      var r = el.getBoundingClientRect(); if (!r.width || !r.height) return;
      var z = parseInt(cs.zIndex, 10) || 0;
      if (z >= 1000 && r.width * r.height >= vw * vh * 0.25 && !/privacy|consent|cookie|shopify-pc/i.test(el.id + ' ' + el.className)) hide(el);
    });
    unlock();
  }
  sweep();
  /* Permanent, coalesced per frame: the CSS hide rule is permanent, so a late (timed/exit-intent) popup must also get its scroll-lock released. */
  var queued = false;
  function schedule() { if (queued) return; queued = true; requestAnimationFrame(function () { queued = false; sweep(); }); }
  var mo = new MutationObserver(schedule);
  mo.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['style', 'class'] });
  mo.observe(document.documentElement, { attributes: true, attributeFilter: ['style'] });
})();
