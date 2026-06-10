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

            // --- MUSIC DASHBOARD RENDER ---
            if (data.activeSoundstages !== undefined) {
                document.getElementById('live-music-sessions').textContent = data.activeSoundstages;
            }

            if (data.globalPlaylists) {
                const list = document.getElementById('global-playlist-list');
                list.innerHTML = ""; // Clear loader
                
                data.globalPlaylists.forEach(p => {
                    const li = document.createElement('li');
                    li.innerHTML = `
                        <div class="playlist-info">
                            <span class="p-name">🎵 ${p.name.toUpperCase()}</span>
                            <span class="p-tracks">${p.tracks} Frequencies</span>
                        </div>
                        <div class="p-visual">
                            <div class="p-bar"></div>
                        </div>
                    `;
                    list.appendChild(li);
                });
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

            formStatus.textContent = "🛰️ Transmitting ticket to staff frequencies...";
            formStatus.style.color = "var(--primary-gold)";

            // ⚠️ HIGH ARCHITECT: PASTE YOUR DISCORD WEBHOOK URL BELOW ⚠️
            const WEBHOOK_URL = "https://discord.com/api/webhooks/1512570083740880906/llpi9fAZ-8sC-3b92OE98_IbIgbFozVQIJ7D85se_Uyq_lrTWOKiQC7AalXMPxJmwiYi";

            if (WEBHOOK_URL === "YOUR_DISCORD_WEBHOOK_URL_HERE") {
                formStatus.textContent = "❌ Neural Error: Webhook missing. Join the Discord manually.";
                formStatus.style.color = "#ff4d4d";
                return;
            }

            const payload = {
                // If you want to ping a specific role (like Support), put its ID here: "<@&ROLE_ID_HERE>"
                content: "🚨 **New Web Ticket Received**", 
                embeds: [{
                    title: "🎫 WEB SUPPORT TICKET",
                    color: 16627761, // Gold
                    fields: [
                        { name: "👤 Discord Username", value: `\`${username}\``, inline: true },
                        { name: "📂 Issue Category", value: `**${category.toUpperCase()}**`, inline: true },
                        { name: "📝 Transmission", value: `>>> ${message}`, inline: false }
                    ],
                    footer: { text: "Elite Elysium | Web Portal" },
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
                    formStatus.textContent = "✅ Ticket securely transmitted. A staff member will DM you.";
                    formStatus.style.color = "#00FFCC";
                    ticketForm.reset();
                } else {
                    throw new Error();
                }
            } catch (err) {
                formStatus.textContent = "❌ Transmission blocked. Please join the Discord to open a ticket.";
                formStatus.style.color = "#ff4d4d";
            }
        });
    }

    // Handle Developer Application Form
    const devForm = document.getElementById('dev-form');
    const devFormStatus = document.getElementById('dev-form-status');

    if (devForm) {
        devForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('dev-username').value;
            const role = document.getElementById('dev-role').value;
            const portfolio = document.getElementById('dev-portfolio').value || "Not Provided";
            const experience = document.getElementById('dev-experience').value;

            devFormStatus.textContent = "🛰️ Transmitting application to High Architects...";
            devFormStatus.style.color = "#2ecc71";

            // ⚠️ HIGH ARCHITECT: PASTE YOUR DEV APPLICATION WEBHOOK URL BELOW ⚠️
            // You can use the same webhook as support, or create a new one for a #dev-applications channel
            const DEV_WEBHOOK_URL = "https://discord.com/api/webhooks/1512570083740880906/llpi9fAZ-8sC-3b92OE98_IbIgbFozVQIJ7D85se_Uyq_lrTWOKiQC7AalXMPxJmwiYi";

            if (DEV_WEBHOOK_URL === "YOUR_DEV_WEBHOOK_URL_HERE") {
                devFormStatus.textContent = "❌ Neural Error: Webhook missing. Join the Discord manually.";
                devFormStatus.style.color = "#ff4d4d";
                return;
            }

            const payload = {
                content: "🛠️ **New Cultivator Application Received**", 
                embeds: [{
                    title: "💻 DEVELOPER APPLICATION",
                    color: 3066993, // Green
                    fields: [
                        { name: "👤 Discord Username", value: `\`${username}\``, inline: true },
                        { name: "🎯 Primary Discipline", value: `**${role}**`, inline: true },
                        { name: "🔗 Portfolio / GitHub", value: portfolio, inline: false },
                        { name: "📝 Experience & Motivation", value: `>>> ${experience}`, inline: false }
                    ],
                    footer: { text: "Elite Elysium | Recruitment Protocol" },
                    timestamp: new Date().toISOString()
                }]
            };

            try {
                const response = await fetch(DEV_WEBHOOK_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    devFormStatus.textContent = "✅ Application successfully transmitted. We will contact you soon.";
                    devFormStatus.style.color = "#2ecc71";
                    devForm.reset();
                } else {
                    throw new Error();
                }
            } catch (err) {
                devFormStatus.textContent = "❌ Transmission blocked. Please join the Discord to apply.";
                devFormStatus.style.color = "#ff4d4d";
            }
        });
    }

    // Handle Music Controller Form
    const musicForm = document.getElementById('music-form');
    const musicFormStatus = document.getElementById('music-form-status');

    if (musicForm) {
        musicForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('music-username').value;
            const query = document.getElementById('music-query').value;

            musicFormStatus.textContent = "🛰️ Connecting to Soundstage...";
            musicFormStatus.style.color = "#1db954";

            // ⚠️ HIGH ARCHITECT: PASTE YOUR DISCORD WEBHOOK URL BELOW ⚠️
            const MUSIC_WEBHOOK_URL = "https://discord.com/api/webhooks/1512570083740880906/llpi9fAZ-8sC-3b92OE98_IbIgbFozVQIJ7D85se_Uyq_lrTWOKiQC7AalXMPxJmwiYi";

            if (MUSIC_WEBHOOK_URL === "YOUR_MUSIC_WEBHOOK_URL_HERE") {
                musicFormStatus.textContent = "❌ Neural Error: Webhook missing.";
                musicFormStatus.style.color = "#ff4d4d";
                return;
            }

            // The specific payload format that bot.py looks for: "!webplay username|query"
            const payload = {
                content: `!webplay ${username}|${query}`
            };

            try {
                const response = await fetch(MUSIC_WEBHOOK_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    musicFormStatus.textContent = "✅ Audio Frequency Queued!";
                    musicFormStatus.style.color = "#1db954";
                    musicForm.reset();
                    setTimeout(() => { musicFormStatus.textContent = ""; }, 3000);
                } else {
                    throw new Error();
                }
            } catch (err) {
                musicFormStatus.textContent = "❌ Transmission blocked.";
                musicFormStatus.style.color = "#ff4d4d";
            }
        });
    }
});
