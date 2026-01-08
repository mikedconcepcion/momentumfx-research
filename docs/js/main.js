// Main JavaScript for interactivity

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileToggle = document.querySelector('.mobile-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (mobileToggle && navMenu) {
        mobileToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            this.classList.toggle('active');
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;

            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });

                // Close mobile menu if open
                if (navMenu) {
                    navMenu.classList.remove('active');
                }
                if (mobileToggle) {
                    mobileToggle.classList.remove('active');
                }

                // Update active nav link
                document.querySelectorAll('.nav-link').forEach(link => {
                    link.classList.remove('active');
                });
                this.classList.add('active');
            }
        });
    });

    // Highlight active section in nav on scroll
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link[href^="#"]');

    function highlightNav() {
        let current = '';

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (scrollY >= (sectionTop - 200)) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active');
            }
        });
    }

    window.addEventListener('scroll', highlightNav);
    highlightNav(); // Call once on load

    // Add animation on scroll for cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe all cards
    document.querySelectorAll('.finding-card, .results-card, .method-card, .data-card, .instrument-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s, transform 0.5s';
        observer.observe(card);
    });

    // Add copy button to code blocks
    document.querySelectorAll('.code-block').forEach(block => {
        const button = document.createElement('button');
        button.textContent = 'Copy';
        button.className = 'copy-btn';
        button.style.cssText = 'position: absolute; top: 0.5rem; right: 0.5rem; padding: 0.25rem 0.75rem; background: #374151; color: white; border: none; border-radius: 0.25rem; font-size: 0.813rem; cursor: pointer; opacity: 0.7; transition: opacity 0.2s;';

        button.addEventListener('mouseenter', () => button.style.opacity = '1');
        button.addEventListener('mouseleave', () => button.style.opacity = '0.7');
        button.addEventListener('click', function() {
            const code = block.querySelector('code').textContent;
            navigator.clipboard.writeText(code).then(() => {
                button.textContent = 'Copied!';
                setTimeout(() => {
                    button.textContent = 'Copy';
                }, 2000);
            });
        });

        block.style.position = 'relative';
        block.appendChild(button);
    });
});

// Add loading animation for stats
document.addEventListener('DOMContentLoaded', function() {
    const statValues = document.querySelectorAll('.stat-value');

    statValues.forEach(stat => {
        const text = stat.textContent.trim();

        // Skip stats that are not pure numbers (like "p<0.001", "6 Years", etc.)
        // Only animate stats that start with a digit and are simple numbers
        const simpleNumberPattern = /^([\d.]+)(M|x|k|%)?$/;
        const match = text.match(simpleNumberPattern);

        if (match) {
            const number = parseFloat(match[1]);
            const suffix = match[2] || '';
            let current = 0;
            const increment = number / 50;
            const timer = setInterval(() => {
                current += increment;
                if (current >= number) {
                    current = number;
                    clearInterval(timer);
                }
                stat.textContent = current.toFixed(number % 1 === 0 ? 0 : 1) + suffix;
            }, 20);
        }
        // Otherwise, keep the original text as-is (handles "p<0.001", "6 Years", etc.)
    });
});
