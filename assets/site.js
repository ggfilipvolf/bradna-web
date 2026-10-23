/* Sdílený skript pro podstránky a blog (homepage má vlastní v index.html) */
(function(){
  var META_PIXEL_ID = "780593422336182";
  var REDUCE = matchMedia('(prefers-reduced-motion: reduce)').matches;

  var y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();

  // ====== COOKIE CONSENT + META PIXEL (pixel až po souhlasu) ======
  function loadMetaPixel(){
    if (!META_PIXEL_ID || window.fbq) return;
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
    n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
    n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
    t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script',
    'https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', META_PIXEL_ID);
    fbq('track', 'PageView');
  }
  (function(){
    var bar = document.getElementById('cookieBar');
    var consent = null;
    try { consent = localStorage.getItem('cookieConsent'); } catch(e){}
    if (consent === 'granted'){ loadMetaPixel(); }
    else if (!consent && bar){ setTimeout(function(){ bar.classList.add('show'); }, 900); }
    function decide(v){ try{ localStorage.setItem('cookieConsent', v); }catch(e){} if (bar) bar.classList.remove('show'); if (v === 'granted') loadMetaPixel(); }
    var a = document.getElementById('cookieAccept'), r = document.getElementById('cookieReject');
    if (a) a.onclick = function(){ decide('granted'); };
    if (r) r.onclick = function(){ decide('denied'); };
  })();

  // ====== header ======
  var header = document.getElementById('header');
  function onScroll(){ if (header) header.classList.toggle('scrolled', scrollY > 30); }
  addEventListener('scroll', onScroll, {passive:true}); onScroll();

  // ====== mobilní menu ======
  var menu = document.getElementById('mobileMenu');
  var burger = document.getElementById('burger'), closeBtn = document.getElementById('closeMenu');
  if (menu && burger) burger.onclick = function(){ menu.classList.add('open'); };
  if (menu && closeBtn) closeBtn.onclick = function(){ menu.classList.remove('open'); };

  // ====== odhalování při scrollu ======
  if (REDUCE || !('IntersectionObserver' in window)){
    document.querySelectorAll('.reveal, .split').forEach(function(el){ el.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(e){ if (e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target);} });
    }, {threshold:.08, rootMargin:'0px 0px -40px 0px'});
    document.querySelectorAll('.reveal, .split').forEach(function(el){ io.observe(el); });
    setTimeout(function(){ document.querySelectorAll('.page-hero .split, .article-hero .split').forEach(function(el){ el.classList.add('in'); }); }, 250);
  }

  // ====== ukazatel čtení ======
  var sbar = document.getElementById('scrollbar');
  if (sbar) addEventListener('scroll', function(){
    var h = document.documentElement, max = h.scrollHeight - h.clientHeight;
    sbar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + '%';
  }, {passive:true});

  // ====== rozbalovací oblasti (Co řeším) ======
  document.querySelectorAll('.srv').forEach(function(s){
    s.addEventListener('click', function(){ s.classList.toggle('open'); });
    s.addEventListener('keydown', function(e){ if (e.key === 'Enter' || e.key === ' '){ e.preventDefault(); s.classList.toggle('open'); } });
  });

  // ====== filtr kategorií na blogu ======
  var filter = document.querySelector('.cat-filter');
  if (filter){
    filter.addEventListener('click', function(e){
      var b = e.target.closest('button'); if (!b) return;
      filter.querySelectorAll('button').forEach(function(x){ x.classList.toggle('on', x === b); });
      var c = b.dataset.cat;
      document.querySelectorAll('.blog-grid .post-card').forEach(function(card){
        card.style.display = (!c || card.dataset.cat === c) ? '' : 'none';
      });
    });
  }

  // ====== konverze: klik na „Chci konzultaci“ ======
  document.querySelectorAll('a[href="/konzultace.html"]').forEach(function(a){
    a.addEventListener('click', function(){ if (window.fbq) fbq('trackCustom', 'KlikKonzultace', {stranka: location.pathname}); });
  });

  // ====== české nedělitelné mezery ======
  var RE = /([\s („>]|^)([aikosuvzAIKOSUVZ]|[Nn]a|[Dd]o|[Oo]d|[Pp]o|[Zz]a|[Zz]e|[Kk]e|[Kk]u|[Vv]e|[Ss]e|[Ss]i|[Aa]ž|[Žž]e)[ ]+/g;
  var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
    acceptNode: function(n){
      var t = n.parentElement && n.parentElement.tagName;
      return (t === 'SCRIPT' || t === 'STYLE' || t === 'TEXTAREA') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
    }
  });
  var nodes = []; while (walker.nextNode()) nodes.push(walker.currentNode);
  nodes.forEach(function(n){
    var s = n.nodeValue, prev;
    do { prev = s; s = s.replace(RE, '$1$2 '); } while (s !== prev);
    if (s !== n.nodeValue) n.nodeValue = s;
  });
})();
