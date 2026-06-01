document.addEventListener('DOMContentLoaded', () => {
    // --- LIVE STATS FETCH ---
    const fetchStats = async () => {
        try {
            // Fetch with cache-buster to ensure fresh data
            const response = await fetch(`stats.json?t=${Date.now()}`);
            if (!response.ok) return;
            
            const data = await response.json();
            
            const formatNum = (num) => new Intl.NumberFormat().format(num);

            if (data.serverCount) {
                document.getElementById('live-server-count').textContent = `${formatNum(data.serverCount)}+`;
            }
            if (data.userCount) {
                document.getElementById('live-user-count').textContent = `${formatNum(data.userCount)}+`;
            }
            if (data.influenceHarvested) {
                document.getElementById('live-influence-harvested').textContent = data.influenceHarvested;
            }
        } catch (err) {
            console.log("Using static fallback stats.");
        }
    };

    fetchStats();

    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                // Adaptive offset: Header (80px) + District Nav (60px) = 140px
                const isDistrictLink = this.closest('.district-nav');
                const headerOffset = isDistrictLink ? 140 : 100;
                
                const elementPosition = target.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                // Close mobile menu if open
                const mobileNav = document.getElementById('mobile-nav');
                if (mobileNav.style.display === 'flex') {
                    mobileNav.style.display = 'none';
                }

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Mobile Menu Toggle
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileNav = document.getElementById('mobile-nav');

    if (mobileMenuBtn && mobileNav) {
        mobileMenuBtn.addEventListener('click', () => {
            const isVisible = mobileNav.style.display === 'flex';
            mobileNav.style.display = isVisible ? 'none' : 'flex';
            
            // Animation for hamburger
            mobileMenuBtn.classList.toggle('active');
        });
    }

    // Intersection Observer for scroll-triggered reveal animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe all elements with the .reveal class
    document.querySelectorAll('.reveal').forEach(el => {
        observer.observe(el);
    });

    // Navbar background opacity shift on scroll
    const nav = document.querySelector('nav');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            nav.style.background = 'rgba(13, 13, 13, 0.95)';
            nav.style.padding = '1rem 0';
        } else {
            nav.style.background = 'rgba(13, 13, 13, 0.8)';
            nav.style.padding = '1.5rem 0';
        }
    });

    // Handle Support Ticket Form
    const ticketForm = document.getElementById('ticket-form');
    const formStatus = document.getElementById('form-status');

    if (ticketForm) {
        ticketForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const category = document.getElementById('category').value;
            const message = document.getElementById('message').value;

            formStatus.textContent = "🛰️ Synchronizing ticket with neural network...";
            formStatus.style.color = "var(--primary-gold)";

            // REPLACE THIS WITH YOUR DISCORD WEBHOOK URL
            const WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE";

            if (WEBHOOK_URL === "YOUR_DISCORD_WEBHOOK_URL_HERE") {
                formStatus.textContent = "❌ Error: Webhook URL not configured. (Staff: Update script.js)";
                formStatus.style.color = "#ff4d4d";
                return;
            }

            const payload = {
                embeds: [{
                    title: "🎫 NEW WEB TICKET",
                    color: 16627761, // Gold
                    fields: [
                        { name: "👤 User", value: `\`${username}\``, inline: true },
                        { name: "📂 Category", value: `\`${category}\``, inline: true },
                        { name: "📝 Message", value: message }
                    ],
                    footer: { text: "Haze Bot Web Support Portal" },
                    timestamp: new Date().toISOString()
                }]
            };

            try {
                const response = await fetch(WEBHOOK_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    formStatus.textContent = "✅ Ticket initialized. Our staff will reach out on Discord.";
                    formStatus.style.color = "#2ecc71";
                    ticketForm.reset();
                } else {
                    throw new Error();
                }
            } catch (err) {
                formStatus.textContent = "❌ Neural Link Failed. Please join our Discord server directly.";
                formStatus.style.color = "#ff4d4d";
            }
        });
    }
});
