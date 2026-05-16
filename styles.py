"""
styles.py - CSS Injection Functions for Scorpio Website Builder
"""

import re


def inject_matching_features_faq_css(html_content: str) -> str:
    """Inject default professional purple CSS for Features and FAQ sections"""
    
    print("🎨 Injecting default purple Features & FAQ CSS...")
    
    matching_css = '''
    /* ========== FEATURES & FAQ - MATCHING PROFESSIONAL PURPLE STYLE ========== */
    /* NOTE: All styles are scoped to #page_home to prevent affecting footer */

    /* ===== SECTION BACKGROUNDS ===== */
    #page_home section.py-20.px-4,
    #page_home section.py-20.px-4:last-of-type {
        background: linear-gradient(180deg, #0a0a0f 0%, #12121a 100%);
        position: relative;
    }

    /* Remove any pseudo-element orbs or patterns */
    #page_home section.py-20.px-4::before,
    #page_home section.py-20.px-4::after,
    #page_home section.py-20.px-4:last-of-type::before,
    #page_home section.py-20.px-4:last-of-type::after {
        display: none;
    }

    /* ===== SECTION HEADERS ===== */
    #page_home section.py-20.px-4 .text-center.mb-12 h2,
    #page_home section.py-20.px-4:last-of-type .text-center.mb-12 h2 {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0.75rem;
        background: linear-gradient(135deg, #ffffff, #c084fc, #f472b6);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        position: relative;
        display: inline-block;
        padding-bottom: 0.75rem;
    }

    /* Animated underline for headers */
    #page_home section.py-20.px-4 .text-center.mb-12 h2::after,
    #page_home section.py-20.px-4:last-of-type .text-center.mb-12 h2::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 70px;
        height: 3px;
        background: linear-gradient(90deg, #c084fc, #f472b6, #c084fc);
        border-radius: 3px;
        animation: underlinePulse 2s ease-in-out infinite;
    }

    @keyframes underlinePulse {
        0%, 100% { width: 70px; opacity: 0.6; }
        50% { width: 100px; opacity: 1; }
    }

    /* Section subheadings */
    #page_home section.py-20.px-4 .text-center.mb-12 p,
    #page_home section.py-20.px-4:last-of-type .text-center.mb-12 p {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 0.5rem;
    }

    /* ===== CARDS - Features Grid ===== */
    #page_home .grid.md\\:grid-cols-4 {
        gap: 1.5rem;
    }

    /* Feature cards */
    #page_home .grid.md\\:grid-cols-4 > div {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 20px;
        transition: all 0.3s cubic-bezier(0.2, 0.9, 0.4, 1.1);
        position: relative;
        overflow: hidden;
    }

    /* FAQ items */
    #page_home .space-y-4 > div {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 20px;
        transition: all 0.3s cubic-bezier(0.2, 0.9, 0.4, 1.1);
        position: relative;
        overflow: hidden;
    }

    /* Card hover effect */
    #page_home .grid.md\\:grid-cols-4 > div:hover,
    #page_home .space-y-4 > div:hover {
        transform: translateY(-4px);
        border-color: rgba(139, 92, 246, 0.5);
        background: rgba(139, 92, 246, 0.08);
        box-shadow: 0 10px 25px -5px rgba(139, 92, 246, 0.2);
    }

    /* Subtle shine on hover */
    #page_home .grid.md\\:grid-cols-4 > div::before,
    #page_home .space-y-4 > div::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.1), transparent);
        transition: left 0.5s ease;
        pointer-events: none;
    }

    #page_home .grid.md\\:grid-cols-4 > div:hover::before,
    #page_home .space-y-4 > div:hover::before {
        left: 100%;
    }

    /* ===== FEATURE ICONS ===== */
    #page_home .grid.md\\:grid-cols-4 > div i {
        font-size: 2.2rem;
        background: linear-gradient(135deg, #c084fc, #f472b6);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin-bottom: 1rem;
        display: inline-block;
        transition: transform 0.2s ease;
    }

    #page_home .grid.md\\:grid-cols-4 > div:hover i {
        transform: scale(1.05);
    }

    /* Feature titles */
    #page_home .grid.md\\:grid-cols-4 > div h3 {
        font-size: 1.125rem;
        font-weight: 600;
        color: #f1f5f9;
        margin-bottom: 0.5rem;
    }

    /* Feature descriptions */
    #page_home .grid.md\\:grid-cols-4 > div p {
        font-size: 0.875rem;
        color: #94a3b8;
        line-height: 1.5;
    }

    /* ===== FAQ SECTION SPECIFIC ===== */
    #page_home .space-y-4 {
        max-width: 768px;
        margin: 0 auto;
    }

    /* FAQ buttons */
    #page_home .faq-btn {
        width: 100%;
        font-weight: 500;
        font-size: 1rem;
        padding: 1.25rem 1.5rem;
        color: #f1f5f9;
        background: transparent;
        border: none;
        text-align: left;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
    }

    #page_home .faq-btn span {
        transition: color 0.2s ease;
    }

    #page_home .faq-btn:hover span {
        color: #c084fc;
    }

    /* FAQ icons */
    #page_home .faq-btn i {
        color: #a855f7;
        font-size: 0.875rem;
        transition: all 0.2s ease;
    }

    #page_home .faq-btn:hover i {
        color: #c084fc;
        transform: scale(1.1);
    }

    /* Rotate icon when open */
    #page_home .faq-btn i.fa-minus {
        transform: rotate(180deg);
        color: #c084fc;
    }

    /* FAQ answers */
    #page_home .faq-answer {
        color: #94a3b8;
        line-height: 1.6;
        font-size: 0.875rem;
        padding: 0 1.5rem 1.25rem 1.5rem;
        border-top: 1px solid rgba(139, 92, 246, 0.15);
    }

    /* ===== RESPONSIVE ADJUSTMENTS ===== */
    @media (max-width: 768px) {
        #page_home .grid.md\\:grid-cols-4 {
            gap: 1rem;
        }
        
        #page_home .grid.md\\:grid-cols-4 > div,
        #page_home .space-y-4 > div {
            border-radius: 16px;
        }
        
        #page_home .faq-btn {
            padding: 1rem 1.25rem;
            font-size: 0.875rem;
        }
        
        #page_home section.py-20.px-4 .text-center.mb-12 h2,
        #page_home section.py-20.px-4:last-of-type .text-center.mb-12 h2 {
            font-size: 1.5rem;
        }
    }

    /* ===== OPTIONAL: Subtle background depth ===== */
    #page_home section.py-20.px-4,
    #page_home section.py-20.px-4:last-of-type {
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(139, 92, 246, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 90% 80%, rgba(236, 72, 153, 0.03) 0%, transparent 50%);
    }
    '''
    
    # Check if CSS already exists
    if 'FEATURES & FAQ - MATCHING PROFESSIONAL PURPLE STYLE' in html_content:
        print("  ✅ Matching Features & FAQ CSS already exists - skipping injection")
        return html_content
    
    # Inject into existing style tag
    if '<style>' in html_content:
        html_content = html_content.replace('</style>', matching_css + '\n</style>', 1)
        print("  ✅ Injected matching Features & FAQ CSS into style tag")
    else:
        html_content = html_content.replace('<head>', f'<head><style>{matching_css}</style>', 1)
        print("  ✅ Created style tag with matching Features & FAQ CSS")
    
    return html_content


def inject_cyberpunk_features_faq_css(html_content: str) -> str:
    """Inject cyberpunk purple neon CSS for Features and FAQ sections - SCOPED to #page_home"""
    
    print("🎨 Injecting Cyberpunk Features & FAQ CSS (scoped to #page_home)...")
    
    cyberpunk_css = '''
    /* ========== FEATURES - CLEAN CYBERPUNK (SCOPED TO #page_home) ========== */
    #page_home section.py-20.px-4.bg-gradient-to-br.from-purple-950\\/20 {
        background: #09090b;
        position: relative;
    }

    /* Remove the grid overlay completely */
    #page_home section.py-20.px-4.bg-gradient-to-br.from-purple-950\\/20::before {
        display: none;
    }

    /* Feature cards - clean cyberpunk (ONLY in #page_home) */
    #page_home .grid.md\\:grid-cols-4 > div {
        background: rgba(0, 0, 0, 0.6);
        border: 1px solid #c084fc;
        box-shadow: 0 0 10px rgba(192, 132, 252, 0.2);
        border-radius: 12px;
        transition: all 0.3s ease;
    }

    #page_home .grid.md\\:grid-cols-4 > div:hover {
        box-shadow: 0 0 20px rgba(192, 132, 252, 0.4);
        transform: translateY(-5px);
        border-color: #f472b6;
    }

    /* Feature icons */
    #page_home .grid.md\\:grid-cols-4 > div i {
        color: #c084fc;
        font-size: 2rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }

    #page_home .grid.md\\:grid-cols-4 > div:hover i {
        color: #f472b6;
        transform: scale(1.1);
    }

    /* Feature titles */
    #page_home .grid.md\\:grid-cols-4 > div h3 {
        color: #ffffff;
        font-size: 1.125rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    /* Feature descriptions */
    #page_home .grid.md\\:grid-cols-4 > div p {
        color: #9ca3af;
        font-size: 0.875rem;
        line-height: 1.5;
    }

    /* ========== FAQ - CLEAN CYBERPUNK (SCOPED TO #page_home) ========== */
    #page_home .space-y-4 > div {
        background: rgba(0, 0, 0, 0.5);
        border: 1px solid #c084fc;
        border-radius: 12px;
        transition: all 0.3s ease;
    }

    #page_home .space-y-4 > div:hover {
        border-color: #f472b6;
        box-shadow: 0 0 15px rgba(192, 132, 252, 0.3);
        transform: translateY(-2px);
    }

    /* FAQ buttons */
    #page_home .faq-btn {
        font-weight: 600;
        font-size: 1rem;
        padding: 1.25rem 1.5rem;
        color: #ffffff;
        background: transparent;
        border: none;
        width: 100%;
        text-align: left;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
    }

    #page_home .faq-btn:hover {
        color: #c084fc;
    }

    /* FAQ icons */
    #page_home .faq-btn i {
        color: #c084fc;
        font-size: 0.875rem;
        transition: all 0.2s ease;
    }

    #page_home .faq-btn:hover i {
        color: #f472b6;
        transform: scale(1.1);
    }

    /* Rotate icon when open */
    #page_home .faq-btn i.fa-minus {
        transform: rotate(180deg);
        color: #f472b6;
    }

    /* FAQ answers */
    #page_home .faq-answer {
        color: #9ca3af;
        line-height: 1.6;
        font-size: 0.875rem;
        padding: 0 1.5rem 1.25rem 1.5rem;
        border-top: 1px solid rgba(192, 132, 252, 0.2);
    }

    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {
        #page_home .grid.md\\:grid-cols-4 {
            gap: 1rem;
        }
        
        #page_home .grid.md\\:grid-cols-4 > div,
        #page_home .space-y-4 > div {
            border-radius: 10px;
        }
        
        #page_home .faq-btn {
            padding: 1rem 1.25rem;
            font-size: 0.875rem;
        }
    }
    '''
    
    # Check if CSS already exists
    if 'FEATURES - CLEAN CYBERPUNK' in html_content:
        print("  ✅ Cyberpunk CSS already exists - skipping injection")
        return html_content
    
    # Remove any conflicting purple CSS first
    if 'FEATURES & FAQ - MATCHING PROFESSIONAL PURPLE STYLE' in html_content:
        purple_pattern = r'/\* ========== FEATURES & FAQ - MATCHING PROFESSIONAL PURPLE STYLE ========== \*/[\s\S]*?(?=/\*|\.reservation-modal|</style>|$|\n\n)'
        html_content = re.sub(purple_pattern, '', html_content, flags=re.DOTALL)
        print("  🗑️ Removed existing purple CSS before injecting cyberpunk")
    
    # Inject into existing style tag
    if '<style>' in html_content:
        html_content = html_content.replace('</style>', cyberpunk_css + '\n</style>', 1)
        print("  ✅ Injected Cyberpunk CSS into style tag")
    else:
        html_content = html_content.replace('<head>', f'<head><style>{cyberpunk_css}</style>', 1)
        print("  ✅ Created style tag with Cyberpunk CSS")
    
    return html_content


def inject_black_white_css(html_content: str) -> str:
    """Inject black & white dark/light mode CSS - SCOPED to #page_home"""
    
    print("  🎨 Injecting Black & White Dark/Light CSS...")
    
    bw_css = '''
    /* ========== BLACK & WHITE - DARK/LIGHT MODE COMPATIBLE ========== */
    /* NOTE: All styles are scoped to #page_home */
    
    /* Light mode variables (default) */
    :root {
        --bg-section: #f8fafc;
        --bg-card: #ffffff;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #64748b;
        --border-light: #e2e8f0;
        --border-medium: #cbd5e1;
        --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.03);
        --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.05);
        --accent: #3b82f6;
        --accent-light: #eff6ff;
    }
    
    /* Dark mode variables - auto detects system preference */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-section: #0a0a0a;
            --bg-card: #1a1a1a;
            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --border-light: #2d2d2d;
            --border-medium: #404040;
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.2);
            --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.3);
            --accent: #60a5fa;
            --accent-light: #1e293b;
        }
    }
    
    /* ===== SECTION BACKGROUNDS ===== */
    #page_home section.py-20.px-4 {
        background: var(--bg-section) !important;
        position: relative;
    }
    
    /* ===== SECTION HEADERS ===== */
    #page_home section.py-20.px-4 .text-center.mb-12 h2 {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary) !important;
        background: none !important;
        -webkit-background-clip: unset !important;
    }
    
    #page_home section.py-20.px-4 .text-center.mb-12 h2::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 60px;
        height: 3px;
        background: var(--text-primary) !important;
        border-radius: 3px;
    }
    
    /* ===== FEATURE CARDS ===== */
    #page_home .grid.md\\:grid-cols-4 > div {
        background: var(--bg-card) !important;
        backdrop-filter: none !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 20px;
        transition: all 0.3s ease;
    }
    
    #page_home .grid.md\\:grid-cols-4 > div:hover {
        transform: translateY(-4px);
        border-color: var(--border-medium) !important;
        background: var(--bg-card) !important;
        box-shadow: var(--shadow-md);
    }
    
    /* Feature icons */
    #page_home .grid.md\\:grid-cols-4 > div i {
        font-size: 2rem;
        margin-bottom: 1rem;
        color: var(--text-secondary) !important;
        background: none !important;
    }
    
    #page_home .grid.md\\:grid-cols-4 > div:hover i {
        transform: scale(1.05);
        color: var(--text-primary) !important;
    }
    
    /* ===== FAQ SECTION ===== */
    #page_home .space-y-4 > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 20px;
    }
    
    #page_home .faq-btn {
        color: var(--text-primary) !important;
    }
    
    #page_home .faq-btn i {
        color: var(--text-muted) !important;
    }
    
    #page_home .faq-btn:hover i {
        color: var(--accent) !important;
    }
    
    #page_home .faq-answer {
        color: var(--text-secondary) !important;
        border-top: 1px solid var(--border-light) !important;
    }
    
    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {
        #page_home .grid.md\\:grid-cols-4 {
            gap: 1rem;
        }
        
        #page_home .grid.md\\:grid-cols-4 > div,
        #page_home .space-y-4 > div {
            border-radius: 16px;
        }
        
        #page_home .faq-btn {
            padding: 1rem 1.25rem;
            font-size: 0.875rem;
        }
    }
    '''
    
    # Remove any conflicting purple or cyberpunk CSS
    purple_pattern = r'/\* ========== FEATURES & FAQ - MATCHING PROFESSIONAL PURPLE STYLE ========== \*/[\s\S]*?(?=/\*|\.reservation-modal|</style>|$|\n\n)'
    html_content = re.sub(purple_pattern, '', html_content, flags=re.DOTALL)
    
    cyberpunk_pattern = r'/\* ========== FEATURES - CLEAN CYBERPUNK.*?\*/[\s\S]*?(?=/\*|\.reservation-modal|</style>|$|\n\n)'
    html_content = re.sub(cyberpunk_pattern, '', html_content, flags=re.DOTALL)
    
    print("  🗑️ Removed existing theme CSS")
    
    # Inject into existing style tag
    if '<style>' in html_content:
        html_content = html_content.replace('</style>', bw_css + '\n</style>', 1)
        print("  ✅ Injected Black & White CSS")
    else:
        html_content = html_content.replace('<head>', f'<head><style>{bw_css}</style>', 1)
        print("  ✅ Created style tag with Black & White CSS")
    
    return html_content


def smart_style_conditional(html_content: str, user_prompt: str = "") -> str:
    """Smart style router - injects appropriate CSS based on user request.
    
    Detects user intent from the prompt and applies:
    - Cyberpunk/Neon theme if requested
    - Black & White/Dark mode if requested
    - Otherwise returns unchanged (keeps default purple)
    """
    
    # Keywords for black & white / dark mode
    bw_keywords = [
        'dark mode', 'dark background', 'black background', 'black and white',
        'bw', 'black & white', 'black and white theme', 'dark theme',
        'light mode', 'light background', 'monochrome', 'grayscale',
        'black white', 'dark color scheme', 'light color scheme',
        'change background to black', 'b&w', 'black/white', 'remove color'
    ]
    
    # Keywords for cyberpunk / neon
    cyberpunk_keywords = [
        'cyberpunk', 'neon', 'cyber', 'punk', 'neon purple', 'purple neon',
        'glow', 'glowing', 'neon glow', 'cyber theme', 'futuristic',
        'vaporwave', 'synthwave', 'neon light', 'purple glow'
    ]
    
    user_prompt_lower = user_prompt.lower()
    
    # Check what the user requested
    is_bw = any(keyword in user_prompt_lower for keyword in bw_keywords)
    is_cyberpunk = any(keyword in user_prompt_lower for keyword in cyberpunk_keywords)
    
    # Extra check for "black and white" combinations
    if not is_bw:
        if ('black' in user_prompt_lower and 'white' in user_prompt_lower) or \
           ('bw' in user_prompt_lower) or ('grayscale' in user_prompt_lower):
            is_bw = True
    
    print(f"🎨 Smart Style Detection:")
    print(f"   User prompt: '{user_prompt[:120]}...'")
    print(f"   Black & White: {is_bw}")
    print(f"   Cyberpunk/Neon: {is_cyberpunk}")
    
    # Handle Cyberpunk request
    if is_cyberpunk:
        print("🎨 Cyberpunk/Neon theme requested - injecting cyberpunk CSS...")
        return inject_cyberpunk_features_faq_css(html_content)
    
    # Handle Black & White request
    if is_bw:
        print("🎨 Black & White theme requested - injecting...")
        return inject_black_white_css(html_content)
    
    print("🎨 No specific theme requested - keeping default purple styles")
    return html_content