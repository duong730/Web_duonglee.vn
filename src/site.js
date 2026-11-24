// Thanh trên có viền khi cuộn; nút trượt kệ ảnh; nút sao chép email.
(() => {
  const topbar = document.querySelector('[data-topbar]');
  if (topbar) {
    const onScroll = () => topbar.classList.toggle('is-scrolled', window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  for (const shelf of document.querySelectorAll('[data-shelf]')) {
    const track = shelf.querySelector('.shelf-track');
    const prev = shelf.querySelector('.prev');
    const next = shelf.querySelector('.next');
    const update = () => {
      const max = track.scrollWidth - track.clientWidth - 2;
      prev.hidden = track.scrollLeft <= 2;
      next.hidden = track.scrollLeft >= max;
    };
    const step = (dir) => track.scrollBy({ left: dir * track.clientWidth * 0.8, behavior: 'smooth' });
    prev.addEventListener('click', () => step(-1));
    next.addEventListener('click', () => step(1));
    track.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    track.querySelectorAll('img').forEach((img) => img.addEventListener('load', update, { once: true }));
    update();
  }

  let toast;
  const say = (text) => {
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'toast';
      toast.setAttribute('role', 'status');
      document.body.append(toast);
    }
    toast.textContent = text;
    toast.classList.add('is-on');
    clearTimeout(say.t);
    say.t = setTimeout(() => toast.classList.remove('is-on'), 1800);
  };
  const vi = document.documentElement.lang === 'vi';
  for (const btn of document.querySelectorAll('[data-copy]')) {
    btn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(btn.dataset.copy);
        say(vi ? 'Đã chép địa chỉ email' : 'Email address copied');
      } catch {
        say(btn.dataset.copy);
      }
    });
  }
})();
