// Mobile nav toggle
document.documentElement.classList.add('js');

const toggle = document.getElementById('nav-toggle');
const links = document.getElementById('nav-links');

if (toggle && links) {
  toggle.addEventListener('click', () => {
    const isOpen = toggle.classList.toggle('active');
    links.classList.toggle('active');
    toggle.setAttribute('aria-expanded', String(isOpen));
  });

  // Close mobile nav on link click
  links.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      toggle.classList.remove('active');
      links.classList.remove('active');
      toggle.setAttribute('aria-expanded', 'false');
    });
  });
}

// Set current year in footer
const year = document.getElementById('year');

if (year) {
  year.textContent = new Date().getFullYear();
}

// Shrink nav on scroll
const nav = document.getElementById('nav');

if (nav) {
  window.addEventListener(
    'scroll',
    () => {
      nav.classList.toggle('scrolled', window.scrollY > 20);
    },
    { passive: true },
  );
}
