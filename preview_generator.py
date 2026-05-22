from typing import Dict, Any, Optional

import re
import json
import os

from datetime import datetime


from styles import (
    inject_matching_features_faq_css,
    smart_style_conditional
)






def fix_hero_navigation_overlap(html_content: str) -> str:
    """
    Fix hero section to not overlap fixed navigation header
    Adds pt-[72px] to container and changes h-screen to h-[calc(100vh-72px)]
    """
    import re
    
    print("🔧 Fixing hero navigation overlap...")
    
    # Step 1: Fix the page_home div - add pt-[72px] to existing class
    # Find the div and add pt-[72px] to its class attribute
    def fix_page_home(match):
        full_tag = match.group(0)
        class_match = re.search(r'class="([^"]*)"', full_tag)
        if class_match:
            existing_classes = class_match.group(1)
            # Add pt-[72px] if not already there
            if 'pt-[72px]' not in existing_classes:
                new_classes = f'class="{existing_classes} pt-[72px]"'
                full_tag = full_tag.replace(class_match.group(0), new_classes)
        return full_tag
    
    html_content = re.sub(
        r'<div id="page_home"[^>]*class="[^"]*"[^>]*>',
        fix_page_home,
        html_content,
        flags=re.DOTALL
    )
    
    # Step 2: Find the hero section and change h-screen to h-[calc(100vh-72px)]
    # Only modify the section tag, not the entire content
    def fix_hero_section(match):
        full_tag = match.group(0)
        # Replace h-screen with h-[calc(100vh-72px)]
        if 'h-screen' in full_tag:
            full_tag = full_tag.replace('h-screen', 'h-[calc(100vh-72px)]')
        # Ensure flex centering classes exist
        if 'flex items-center justify-center' not in full_tag:
            full_tag = full_tag.replace('relative', 'relative flex items-center justify-center')
        return full_tag
    
    html_content = re.sub(
        r'<section[^>]*class="[^"]*relative[^"]*h-screen[^"]*"[^>]*>',
        fix_hero_section,
        html_content,
        count=1,
        flags=re.DOTALL
    )
    
    print("  ✅ Added pt-[72px] to #page_home container")
    print("  ✅ Changed hero section height to h-[calc(100vh-72px)]")
    
    return html_content






def extract_trust_indicators_from_source(source_content: str) -> list:
    """
    Extract trust badge data directly from raw TSX/JSX source.
    Returns list of dicts: [{icon, value, label}]
    Works on the raw source BEFORE any array processing.
    """
    import re

    indicators = []

    # ========== PATTERN 1: Direct React component structure ==========
    trust_pattern = r'<div className="flex items-center gap-3">\s*<([A-Z][a-zA-Z]+)\s+className="[^"]*"[^>]*/?>\s*<div>\s*<div[^>]*>([^<]+)</div>\s*<div[^>]*>([^<]+)</div>\s*</div>\s*</div>'
    
    matches = re.findall(trust_pattern, source_content, re.DOTALL)
    for match in matches:
        icon_name = match[0]
        value = match[1].strip()
        label = match[2].strip()
        if value and label:
            indicators.append({'icon': icon_name, 'value': value, 'label': label})
            print(f"  ✅ Extracted trust indicator: {icon_name} = {value} {label}")

    if indicators:
        return indicators

    # ========== PATTERN 2: With fill attribute ==========
    trust_pattern2 = r'<([A-Z][a-zA-Z]+)\s+className="[^"]*"\s*/>\s*<div>\s*<div[^>]*>([^<]+)</div>\s*<div[^>]*>([^<]+)</div>'
    matches = re.findall(trust_pattern2, source_content, re.DOTALL)
    for match in matches:
        icon_name = match[0]
        value = match[1].strip()
        label = match[2].strip()
        if value and label and '{' not in value:
            indicators.append({'icon': icon_name, 'value': value, 'label': label})

    if indicators:
        return indicators

    # ========== PATTERN 3: w-10 h-10 icon wrapper + value + label ==========
    stat_block_pattern = (
        r'<div[^>]*className="[^"]*w-10 h-10[^"]*"[^>]*>\s*'
        r'<(\w+)[^/]*/?\s*>\s*</div>\s*'
        r'<div>\s*<div[^>]*>([^<]+)</div>\s*<div[^>]*>([^<]+)</div>'
    )
    for match in re.finditer(stat_block_pattern, source_content, re.DOTALL):
        icon_name = match.group(1)
        value = match.group(2).strip()
        label = match.group(3).strip()
        if value and label and '{' not in value:
            indicators.append({'icon': icon_name, 'value': value, 'label': label})

    if indicators:
        return indicators

    # ========== PATTERN 4: const stats/badges/trustBadges array ==========
    stats_array_pattern = (
        r'const\s+(?:stats|badges|indicators|trustBadges)\s*=\s*\[([\s\S]*?)\]'
    )
    array_match = re.search(stats_array_pattern, source_content)
    if array_match:
        array_content = array_match.group(1)
        item_pattern = (
            r'\{\s*icon:\s*(\w+)\s*,\s*'
            r'(?:label|title|name):\s*["\']([^"\']+)["\']\s*,\s*'
            r'(?:value|count|stat):\s*["\']([^"\']+)["\']\s*\}'
        )
        for match in re.finditer(item_pattern, array_content):
            indicators.append({
                'icon': match.group(1),
                'value': match.group(3).strip(),
                'label': match.group(2).strip()
            })

    # ========== PATTERN 5: Direct JSX with nested divs ==========
    if not indicators:
        section_pattern = r'<div className="absolute bottom-8 left-0 right-0 z-10">(.*?)</div>\s*</section>'
        section_match = re.search(section_pattern, source_content, re.DOTALL)
        if section_match:
            section_content = section_match.group(1)
            indicator_pattern = r'<div className="flex items-center gap-3">.*?<([A-Z][a-zA-Z]+).*?<div[^>]*>([^<]+)</div>.*?<div[^>]*>([^<]+)</div>'
            for match in re.finditer(indicator_pattern, section_content, re.DOTALL):
                icon_name = match.group(1)
                value = match.group(2).strip()
                label = match.group(3).strip()
                if value and label:
                    indicators.append({'icon': icon_name, 'value': value, 'label': label})

    # ========== PATTERN 6: Simple inline trust indicators ==========
    if not indicators:
        print("  🔍 Trying Pattern 6: Simple inline trust indicators...")
        
        container_pattern = r'<div\s+className="flex flex-wrap gap-6 justify-center[^"]*"[^>]*>(.*?)</div>\s*(?:</div>)?\s*(?:\))?\s*;?'
        container_match = re.search(container_pattern, source_content, re.DOTALL)
        
        if container_match:
            container_content = container_match.group(1)
            item_pattern = r'<div\s+className="flex items-center gap-2">\s*<([A-Z][a-zA-Z]+)\s+className="[^"]*"[^>]*/>\s*([^<]+?)\s*</div>'
            matches = re.findall(item_pattern, container_content, re.DOTALL)
            
            for match in matches:
                icon_name = match[0]
                full_text = match[1].strip()
                
                parts = full_text.split()
                if len(parts) >= 2:
                    first_part = parts[0]
                    if re.match(r'^[\d\./\+k\+]+$', first_part) or '4.9' in first_part or '10k' in first_part:
                        value = first_part
                        label = ' '.join(parts[1:])
                    else:
                        value = full_text
                        label = ""
                else:
                    value = full_text
                    label = ""
                
                if value:
                    indicators.append({
                        'icon': icon_name,
                        'value': value,
                        'label': label
                    })
                    print(f"  ✅ Extracted trust indicator (Pattern 6): {icon_name} = {value} {label}")

    # ========== PATTERN 7: Direct span text extraction ==========
    if not indicators:
        print("  🔍 Trying Pattern 7: Direct span text extraction...")
        
        # Look for pattern: <Icon /> <span>Text</span>
        direct_pattern = r'<([A-Z][a-zA-Z]+)\s+className="[^"]*"(?:\s+fill="[^"]*")?\s*/>\s*<span[^>]*>([^<]+)</span>'
        matches = re.findall(direct_pattern, source_content, re.DOTALL)
        
        for icon_name, full_text in matches:
            full_text = full_text.strip()
            parts = full_text.split(maxsplit=1)
            if len(parts) == 2:
                value = parts[0]
                label = parts[1]
            else:
                # Try to detect if it's a number or rating
                if re.match(r'^[\d\./\+k\+]+$', full_text):
                    value = full_text
                    label = ""
                else:
                    value = full_text
                    label = ""
            
            indicators.append({
                'icon': icon_name,
                'value': value,
                'label': label
            })
            print(f"  ✅ Extracted trust indicator (Pattern 7): {icon_name} = {value} {label}")

    # ========== PATTERN 8: Map array trust indicators ==========
    if not indicators:
        print("  🔍 Trying Pattern 8: Map array trust indicators...")
        
        array_def_pattern = r'\[\s*\{\s*icon:\s*(\w+)\s*,\s*val:\s*["\']([^"\']+)["\']\s*,\s*label:\s*["\']([^"\']+)["\']\s*\},?\s*\]'
        
        trust_section_pattern = r'<div\s+className="absolute bottom-8 left-0 right-0 z-10">\s*<div\s+className="container mx-auto px-4 flex flex-wrap justify-center gap-12">\s*\{([\s\S]*?)\.map\([^)]*\)\s*=>\s*\([\s\S]*?\)\s*\)\s*\}'
        trust_section_match = re.search(trust_section_pattern, source_content, re.DOTALL)
        
        if trust_section_match:
            array_content = trust_section_match.group(1)
            item_pattern = r'\{\s*icon:\s*(\w+)\s*,\s*val:\s*["\']([^"\']+)["\']\s*,\s*label:\s*["\']([^"\']+)["\']\s*\}'
            items = re.findall(item_pattern, array_content)
            
            for icon_name, value, label in items:
                indicators.append({
                    'icon': icon_name,
                    'value': value.strip(),
                    'label': label.strip()
                })
                print(f"  ✅ Extracted trust indicator (Pattern 8): {icon_name} = {value} {label}")
        
        if not indicators:
            array_only_pattern = r'\[\s*\{\s*icon:\s*(\w+)\s*,\s*val:\s*["\']([^"\']+)["\']\s*,\s*label:\s*["\']([^"\']+)["\']\s*\},?\s*\]'
            matches = re.findall(array_only_pattern, source_content, re.DOTALL)
            
            for icon_name, value, label in matches:
                indicators.append({
                    'icon': icon_name,
                    'value': value.strip(),
                    'label': label.strip()
                })
                print(f"  ✅ Extracted trust indicator (Pattern 8 fallback): {icon_name} = {value} {label}")

    # ========== PATTERN 9: Direct bottom-8 flex gap-12 pattern (YOUR REACT STRUCTURE) ==========
    if not indicators:
        print("  🔍 Trying Pattern 9: Direct bottom-8 flex gap-12 pattern...")
        
        # Find the bottom-8 div with flex justify-center gap-12
        bottom_div_pattern = r'<div\s+className="absolute bottom-8 left-0 right-0 flex justify-center gap-12"\s*>(.*?)</div>\s*(?:</div>)?\s*(?:\))?\s*;?'
        bottom_match = re.search(bottom_div_pattern, source_content, re.DOTALL)
        
        if bottom_match:
            bottom_content = bottom_match.group(1)
            
            # Match each trust item: <div className="flex items-center gap-2">...content...</div>
            item_pattern = r'<div\s+className="flex items-center gap-2"\s*>(.*?)</div>'
            items = re.findall(item_pattern, bottom_content, re.DOTALL)
            
            for item in items:
                # Extract icon component (Star, Users, Shield, Truck, etc.)
                icon_pattern = r'<([A-Z][a-zA-Z]+)\s+className="[^"]*"(?:\s+fill="[^"]*")?\s*/>'
                icon_match = re.search(icon_pattern, item)
                
                # Extract text content from span
                span_pattern = r'<span[^>]*>([^<]+)</span>'
                span_match = re.search(span_pattern, item)
                
                if icon_match and span_match:
                    icon_name = icon_match.group(1)
                    full_text = span_match.group(1).strip()
                    
                    # Split into value and label (e.g., "4.9/5 Rating" -> value="4.9/5", label="Rating")
                    parts = full_text.split(maxsplit=1)
                    if len(parts) == 2:
                        value = parts[0]
                        label = parts[1]
                    else:
                        value = full_text
                        label = ""
                    
                    indicators.append({
                        'icon': icon_name,
                        'value': value,
                        'label': label
                    })
                    print(f"  ✅ Extracted trust indicator (Pattern 9): {icon_name} = {value} {label}")
        
        # If still not found, try a more lenient pattern for React components
        if not indicators:
            # Look for the pattern: <Icon className="..." /> <span>text</span>
            react_pattern = r'<div\s+className="flex items-center gap-2">\s*<([A-Z][a-zA-Z]+)\s+className="[^"]*"\s*/>\s*<span[^>]*>([^<]+)</span>\s*</div>'
            matches = re.findall(react_pattern, source_content, re.DOTALL)
            
            for icon_name, full_text in matches:
                full_text = full_text.strip()
                parts = full_text.split(maxsplit=1)
                if len(parts) == 2:
                    value = parts[0]
                    label = parts[1]
                else:
                    value = full_text
                    label = ""
                
                indicators.append({
                    'icon': icon_name,
                    'value': value,
                    'label': label
                })
                print(f"  ✅ Extracted trust indicator (Pattern 9 fallback): {icon_name} = {value} {label}")

    return indicators












def build_trust_indicators_html(indicators: list) -> str:
    """
    Build trust indicators HTML - FLEXBOX VERSION with NO absolute positioning.
    Uses simple margin-top for spacing directly after CTA buttons.
    """
    ICON_MAP = {
        'Star': 'star', 'Users': 'users', 'Shield': 'shield-alt',
        'Truck': 'truck', 'Sparkles': 'sparkles', 'Heart': 'heart',
        'Award': 'award', 'Check': 'check', 'CheckCircle': 'check-circle',
        'Utensils': 'utensils', 'Coffee': 'coffee', 'Clock': 'clock',
        'Phone': 'phone', 'Globe': 'globe', 'Zap': 'zap',
        'TrendingUp': 'trending-up', 'ThumbsUp': 'thumbs-up',
        'DollarSign': 'dollar-sign', 'Package': 'package',
    }
    
    COLOR_MAP = {
        'Star': 'text-yellow-400', 'Users': 'text-cyan-400',
        'Shield': 'text-green-400', 'ShieldAlt': 'text-green-400',
        'Truck': 'text-blue-400', 'Award': 'text-amber-400', 
        'Heart': 'text-red-400', 'Zap': 'text-purple-400',
        'Sparkles': 'text-amber-400', 'Utensils': 'text-blue-400',
    }

    if not indicators:
        return ''

    items = []
    for ind in indicators:
        icon_name = ind.get('icon', 'star')
        if icon_name == 'Shield':
            lucide_icon = 'shield-alt'
        else:
            lucide_icon = ICON_MAP.get(icon_name, icon_name.lower())
        color = COLOR_MAP.get(icon_name, 'text-purple-400')
        value = ind.get('value', '')
        label = ind.get('label', '')
        
        star_class = 'text-yellow-400' if icon_name == 'Star' else color
        
        items.append(f'''
                <div class="flex items-center gap-2">
                    <i class="fas fa-{lucide_icon} {star_class} text-xl"></i>
                    <span class="text-white font-bold">{value}</span>
                    <span class="text-gray-400 text-sm">{label}</span>
                </div>''')

    items_html = '\n                '.join(items)

    # mt-6 creates tight spacing (1.5rem) between CTA buttons and indicators
    return f'''
        <div class="mt-6 pb-6">
            <div class="flex flex-wrap items-center justify-center gap-6">
                {items_html}
            </div>
        </div>'''






def inject_trust_indicators(preview_html: str, files: dict, user_prompt: str = '') -> str:
    """
    Extracts trust badges from raw source and injects them into the hero section.
    PRESERVES original hero content - only adds trust indicators if missing.
    """
    import re

    # ── Skip for dashboards ───────────────────────────────────────────────────
    if any(k in user_prompt.lower() for k in
           ['dashboard', 'analytics', 'admin panel', 'kpi']):
        print('📊 Dashboard — skipping trust indicators')
        return preview_html

    # ── Get raw source ────────────────────────────────────────────────────────
    homepage_source = (
        files.get('app/page.tsx', '')
        or files.get('app/page.jsx', '')
        or files.get('pages/index.tsx', '')
        or files.get('pages/index.jsx', '')
        or ''
    )
    if not homepage_source:
        print('⚠️ No homepage source — skipping trust indicators')
        return preview_html

    # ── Extract trust indicators from source ───────────────────────────────────
    indicators = extract_trust_indicators_from_source(homepage_source)
    if not indicators:
        print('⚠️ No trust indicators found in source')
        return preview_html

    print(f'✅ Extracted {len(indicators)} trust indicators')

    # ── Build trust indicators HTML ───────────────────────────────────────────
    trust_html = build_trust_indicators_html(indicators)
    
    # ── CHECK IF TRUST INDICATORS ALREADY EXIST ────────────────────────────────
    if 'flex flex-wrap items-center justify-center gap-6' in preview_html:
        print("  ✅ Trust indicators already present - skipping injection")
        return preview_html
    
    # ── FIND THE CTA BUTTONS SECTION AND ADD TRUST INDICATORS AFTER IT ─────────
    # Pattern for your CTA buttons (Get Started and Learn More)
    cta_pattern = r'(<div class="flex flex-col sm:flex-row gap-4 justify-center mb-10">.*?</div>)'
    
    def add_trust_indicators(match):
        cta_div = match.group(1)
        return cta_div + trust_html
    
    if re.search(cta_pattern, preview_html, re.DOTALL):
        preview_html = re.sub(cta_pattern, add_trust_indicators, preview_html, flags=re.DOTALL)
        print('✅ Trust indicators injected after CTA buttons')
        return preview_html
    
    # ── ALTERNATIVE: Find any div containing buttons in hero ───────────────────
    alt_cta_pattern = r'(<div class="flex[^>]*gap-4[^>]*justify-center[^>]*>.*?</div>)'
    
    if re.search(alt_cta_pattern, preview_html[:5000], re.DOTALL):
        preview_html = re.sub(alt_cta_pattern, add_trust_indicators, preview_html, count=1, flags=re.DOTALL)
        print('✅ Trust indicators injected after alternative CTA div')
        return preview_html
    
    # ── LAST RESORT: Find the hero content div and append trust indicators ─────
    hero_content_pattern = r'(<div class="relative z-10 text-center px-4[^>]*>.*?)(</div>\s*</div>\s*</section>)'
    
    def append_to_hero(match):
        hero_content = match.group(1)
        closing = match.group(2)
        # Check if trust indicators already exist in this section
        if 'flex flex-wrap' in hero_content:
            return match.group(0)
        return hero_content + trust_html + closing
    
    preview_html = re.sub(hero_content_pattern, append_to_hero, preview_html, flags=re.DOTALL)
    print('✅ Trust indicators appended to hero section')

    return preview_html













def generate_navigation_html(brand_name: str, nav_links: list) -> str:
    """
    Generate navigation HTML based on nav_links.
    NO hardcoded Shop/Cart - only what's in nav_links.
    """
    
    # Generate desktop navigation links
    desktop_links = ""
    mobile_links = ""
    
    for href, label in nav_links:
        page_id = href.replace('/', '').replace('-', '_')
        
        # Check if this is a cart link
        is_cart = 'cart' in label.lower() or href == '/cart'
        
        if is_cart:
            # Cart link with badge
            desktop_links += f'''
                        <a href="{href}" class="nav-link relative flex items-center gap-2 group" data-page="{page_id}">
                            <i data-lucide="shopping-cart" class="w-4 h-4 text-purple-400 group-hover:text-purple-600 transition-all duration-300"></i>
                            <span class="text-gray-300 group-hover:text-purple-400">{label}</span>
                            <span data-cart-count class="cart-count-badge hidden absolute -top-2 -right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full items-center justify-center px-1 shadow-lg shadow-purple-500/25">0</span>
                        </a>'''
            
            mobile_links += f'''
                        <div class="flex items-center justify-between w-full px-4 py-2 rounded-lg hover:bg-white/10">
                            <a href="{href}" class="mobile-nav-link flex items-center gap-3" data-page="{page_id}">
                                <i data-lucide="shopping-cart" class="w-4 h-4 text-purple-400"></i>
                                <span class="text-gray-300">{label}</span>
                            </a>
                            <span data-cart-count class="cart-count-badge hidden bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full items-center justify-center px-1">0</span>
                        </div>'''
        else:
            # Regular link (no icon)
            desktop_links += f'''
                        <a href="{href}" class="nav-link group" data-page="{page_id}">
                            <span class="text-gray-300 group-hover:text-purple-400 transition-colors duration-300">{label}</span>
                        </a>'''
            
            mobile_links += f'''
                        <a href="{href}" class="mobile-nav-link block w-full px-4 py-2 rounded-lg hover:bg-white/10" data-page="{page_id}">
                            <span class="text-gray-300">{label}</span>
                        </a>'''
    
    # Return complete navigation HTML
    return f'''
<header>
    <nav class="nav-container">
        <a href="#" class="brand flex items-center gap-2 group" onclick="handleBrandClick(event); return false;">
            <i data-lucide="sparkles" class="w-8 h-8" style="color: #d8a219;"></i>
            <span class="text-white text-xl font-bold">{brand_name}</span>
        </a>
        <div class="hidden md:flex space-x-2 items-center">
            {desktop_links}
        </div>
        <button id="mobile-menu-button" class="md:hidden p-2 rounded-lg hover:bg-white/10 transition-colors">
            <i data-lucide="menu" class="w-6 h-6" style="color: #d8a219;"></i>
        </button>
    </nav>
    
    <div id="mobile-menu" class="hidden md:hidden bg-black/80 backdrop-blur-lg p-4 space-y-2 border-t border-white/10">
        {mobile_links}
    </div>
</header>

<script>
    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenuBtn && mobileMenu) {{
        mobileMenuBtn.addEventListener('click', () => {{
            mobileMenu.classList.toggle('hidden');
        }});
    }}
    
    // Close mobile menu when clicking a link
    document.querySelectorAll('.mobile-nav-link').forEach(link => {{
        link.addEventListener('click', () => {{
            mobileMenu.classList.add('hidden');
        }});
    }});
</script>
'''


















def preserve_faq_count(original_html: str, new_html: str) -> str:
    """Preserve the original FAQ count when regenerating preview"""
    import re
    
    # Count FAQs in original HTML
    original_faq_count = len(re.findall(r'class="faq-btn"', original_html))
    
    if original_faq_count == 0:
        print(f"⚠️ No FAQ items found in original HTML")
        return new_html
    
    # Count FAQs in new HTML
    new_faq_count = len(re.findall(r'class="faq-btn"', new_html))
    
    if new_faq_count >= original_faq_count:
        print(f"✅ FAQ count OK: {original_faq_count} items found")
        return new_html
    
    print(f"⚠️ FAQ count decreased from {original_faq_count} to {new_faq_count} - restoring original count")
    
    # METHOD 1: Extract ALL FAQ items from original HTML using a more robust pattern
    faq_item_pattern = r'<div[^>]*class="[^"]*bg-white/5[^"]*rounded-2xl[^"]*"[^>]*>.*?<button[^>]*class="faq-btn[^"]*"[^>]*>.*?</button>.*?<div[^>]*class="faq-answer[^"]*"[^>]*>.*?</div>.*?</div>'
    
    original_items = re.findall(faq_item_pattern, original_html, re.DOTALL)
    
    if len(original_items) >= original_faq_count:
        print(f"  📦 Extracted {len(original_items)} individual FAQ items from original")
        
        # Find the FAQ container in new HTML (the div with space-y-4 class)
        container_pattern = r'(<div[^>]*class="[^"]*space-y-4[^"]*"[^>]*>)'
        container_match = re.search(container_pattern, new_html, re.DOTALL)
        
        if container_match:
            container_opening = container_match.group(1)
            
            # Find where this container ends
            search_pos = new_html.find(container_opening) + len(container_opening)
            div_count = 1
            end_pos = -1
            
            for i in range(search_pos, len(new_html)):
                if new_html[i:i+5] == '<div ':
                    div_count += 1
                elif new_html[i:i+6] == '</div>':
                    div_count -= 1
                    if div_count == 0:
                        end_pos = i + 6
                        break
            
            if end_pos != -1:
                # Rebuild with ALL original FAQ items
                rebuilt_container = container_opening + '\n' + '\n'.join(original_items) + '\n</div>'
                new_html = new_html[:search_pos - len(container_opening)] + rebuilt_container + new_html[end_pos:]
                print(f"  ✅ Rebuilt FAQ container with {len(original_items)} items")
                return new_html
    
    # METHOD 2: Find the FAQ section by parent section
    faq_section_pattern = r'(<section[^>]*class="[^"]*py-20[^"]*"[^>]*>.*?<h2[^>]*>FAQ.*?</section>)'
    original_section = re.search(faq_section_pattern, original_html, re.DOTALL | re.IGNORECASE)
    
    if original_section:
        new_section = re.search(faq_section_pattern, new_html, re.DOTALL | re.IGNORECASE)
        if new_section:
            # Replace the entire FAQ section
            new_html = new_html.replace(new_section.group(0), original_section.group(0))
            print(f"  ✅ Replaced entire FAQ section with {original_faq_count} items")
            return new_html
    
    # METHOD 3: Direct string replacement - find the FAQ container content
    if 'space-y-4' in new_html:
        # Find the FAQ section heading to locate the right container
        faq_heading_pattern = r'<h2[^>]*>FAQ</h2>\s*<div[^>]*class="[^"]*space-y-4[^"]*"[^>]*>[\s\S]*?</div>'
        
        # Get the original FAQ container content
        original_container_match = re.search(r'<h2[^>]*>FAQ</h2>\s*<div[^>]*class="[^"]*space-y-4[^"]*"[^>]*>([\s\S]*?)</div>', original_html, re.DOTALL)
        
        if original_container_match:
            original_container_content = original_container_match.group(1)
            
            # Replace in new HTML
            new_html = re.sub(
                r'(<h2[^>]*>FAQ</h2>\s*<div[^>]*class="[^"]*space-y-4[^"]*"[^>]*>)[\s\S]*?(</div>)',
                r'\1' + original_container_content + r'\2',
                new_html,
                flags=re.DOTALL
            )
            print(f"  ✅ Replaced FAQ container content with {original_faq_count} items")
            return new_html
    
    return new_html











def remove_hero_image_from_html(html_content: str) -> str:
    """Remove hero section background image from HTML preview"""
    import re
    
    print("🖼️ Removing hero image from preview...")
    
    # Pattern 1: Remove img tag with image_1.jpg or Cloudinary URL in hero section
    html_content = re.sub(
        r'<img[^>]*src=["\'][^"\']*(?:image_1\.jpg|cloudinary\.com[^"\']*image/upload)[^"\']*["\'][^>]*class="[^"]*absolute inset-0[^"]*"[^>]*/?>',
        '',
        html_content,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # Pattern 2: Remove any img tag that's likely a hero background
    html_content = re.sub(
        r'<img[^>]*class="[^"]*absolute inset-0 w-full h-full object-cover[^"]*"[^>]*/?>',
        '',
        html_content,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # Pattern 3: Remove dark overlay div that usually follows hero image
    html_content = re.sub(
        r'<div[^>]*class="[^"]*absolute inset-0 bg-black/50[^"]*"[^>]*></div>',
        '',
        html_content,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # Pattern 4: Remove gradient overlays
    html_content = re.sub(
        r'<div[^>]*class="[^"]*absolute inset-0 bg-gradient[^"]*"[^>]*></div>',
        '',
        html_content,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # Pattern 5: Remove any img tag with image_1.jpg anywhere
    html_content = re.sub(
        r'<img[^>]*image_1\.jpg[^>]*/?>',
        '',
        html_content,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # Pattern 6: Remove the parent section if it becomes empty
    html_content = re.sub(
        r'<section[^>]*class="[^"]*relative h-screen[^"]*"[^>]*>\s*</section>',
        '',
        html_content,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    print("✅ Hero image removed")
    return html_content













def inject_hero_padding_fix(html_content: str) -> str:
    """Inject CSS to push hero content below fixed header"""
    import re
    
    print("🔧 INJECTING HERO PADDING FIX...")
    
    hero_padding_css = '''
    
    
    
    /* Push hero content below fixed header */
.relative.z-10 {
    padding-top: 110px;
}
    
    
    
    
    
    @media (max-width: 768px) {
        .relative.z-10 {
            padding-top: 72px;
        }
    }
    '''
    
    # Check if the CSS already exists
    if 'Push hero content below fixed header' in html_content:
        print("  ✅ Hero padding fix already exists - skipping injection")
        return html_content
    
    # Inject into existing style tag
    if '<style>' in html_content:
        html_content = html_content.replace('</style>', hero_padding_css + '\n</style>', 1)
        print("  ✅ Injected hero padding fix into style tag")
    else:
        # Create style tag if doesn't exist
        html_content = html_content.replace('<head>', f'<head><style>{hero_padding_css}</style>', 1)
        print("  ✅ Created style tag with hero padding fix")
    
    return html_content









def remove_react_onerror_handlers(html_content: str) -> str:
    """Remove React-style onError handlers from HTML (safe and minimal)"""
    import re
    
    # Only target the exact onError pattern
    # Match: onError={(e) => { code here }}
    pattern = r'onError=\{\s*\([^)]*\)\s*=>\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*\}'
    
    # Remove the attribute (replace with empty string)
    cleaned_html = re.sub(pattern, '', html_content)
    
    print("  🧹 Removed React onError handlers")
    return cleaned_html









def render_dashboard_from_source(content: str) -> str:
    """
    Extract kpiData and charts from React dashboard component and render as HTML
    """
    import re
    
    print("📊 Rendering dashboard from source...")
    
    # Step 1: Extract kpiData array
    kpi_pattern = r'const\s+kpiData\s*=\s*\[\s*((?:[^\[\]]*?\{[^}]*\}[^\[\]]*?)*?)\s*\]'
    kpi_match = re.search(kpi_pattern, content, re.DOTALL)
    
    kpi_cards_html = ""
    chart_html = ""
    
    if kpi_match:
        kpi_content = kpi_match.group(1)
        
        # Extract each KPI item
        kpi_items = re.findall(
            r'name:\s*[\'"]([^\'"]+)[\'"]\s*,\s*value:\s*[\'"]([^\'"]+)[\'"]\s*,\s*change:\s*[\'"]([^\'"]+)[\'"]',
            kpi_content
        )
        
        if kpi_items:
            print(f"  ✅ Found {len(kpi_items)} KPI items")
            
            # Build KPI cards HTML
            kpi_cards_html = '<div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">\n'
            
            for name, value, change in kpi_items:
                # Determine color based on change (positive/negative)
                is_positive = '+' in change
                color_class = 'text-green-400' if is_positive else 'text-red-400'
                
                # Map name to icon
                icon_map = {
                    'Revenue': 'dollar-sign',
                    'Users': 'users',
                    'Orders': 'shopping-cart',
                    'Bounce Rate': 'activity'
                }
                icon = icon_map.get(name, 'chart-line')
                
                kpi_cards_html += f'''
            <div class="bg-white/5 p-6 rounded-2xl border border-white/10 hover:border-purple-500/50 transition-all">
                <div class="flex justify-between items-start mb-2">
                    <p class="text-gray-400 text-sm">{name}</p>
                    <i data-lucide="{icon}" class="w-5 h-5 text-purple-400"></i>
                </div>
                <h3 class="text-2xl font-bold mt-1">{value}</h3>
                <p class="{color_class} text-sm mt-2">{change}</p>
            </div>'''
            
            kpi_cards_html += '\n        </div>'
        else:
            print(f"  ⚠️ No KPI items extracted, using defaults")
            kpi_cards_html = get_default_kpi_cards()
    else:
        print(f"  ⚠️ No kpiData array found, using defaults")
        kpi_cards_html = get_default_kpi_cards()
    
    # Step 2: Extract chart data
    chart_data_pattern = r'const\s+data\s*=\s*\[\s*((?:[^\[\]]*?\{[^}]*\}[^\[\]]*?)*?)\s*\]'
    chart_match = re.search(chart_data_pattern, content, re.DOTALL)
    
    labels = []
    values = []
    
    if chart_match:
        chart_content = chart_match.group(1)
        chart_items = re.findall(r'name:\s*[\'"]([^\'"]+)[\'"]\s*,\s*val:\s*(\d+)', chart_content)
        
        if chart_items:
            labels = [item[0] for item in chart_items]
            values = [item[1] for item in chart_items]
            print(f"  ✅ Found chart data: {labels} = {values}")
    
    if not labels:
        labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        values = [400, 300, 600, 500, 700, 650]
    
    # Step 3: Build chart HTML
    chart_html = f'''
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div class="bg-white/5 p-6 rounded-2xl border border-white/10">
            <h3 class="text-lg font-bold mb-4">Revenue Trend</h3>
            <canvas id="revenueChart" height="200"></canvas>
        </div>
        <div class="bg-white/5 p-6 rounded-2xl border border-white/10">
            <h3 class="text-lg font-bold mb-4">User Growth</h3>
            <canvas id="userChart" height="200"></canvas>
        </div>
    </div>
    
    <script>
        // Revenue Chart
        const revenueCtx = document.getElementById('revenueChart')?.getContext('2d');
        if (revenueCtx) {{
            new Chart(revenueCtx, {{
                type: 'line',
                data: {{
                    labels: {labels},
                    datasets: [{{
                        label: 'Revenue',
                        data: {values},
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        fill: true,
                        tension: 0.3
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {{
                        legend: {{ labels: {{ color: '#9ca3af' }} }}
                    }},
                    scales: {{
                        y: {{ ticks: {{ color: '#9ca3af' }}, beginAtZero: true }},
                        x: {{ ticks: {{ color: '#9ca3af' }} }}
                    }}
                }}
            }});
        }}
        
        // User Chart
        const userCtx = document.getElementById('userChart')?.getContext('2d');
        if (userCtx) {{
            new Chart(userCtx, {{
                type: 'bar',
                data: {{
                    labels: {labels},
                    datasets: [{{
                        label: 'Users',
                        data: [1850, 2100, 2340, 2580, 2710, 2847],
                        backgroundColor: '#c084fc',
                        borderRadius: 8
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {{
                        legend: {{ labels: {{ color: '#9ca3af' }} }}
                    }},
                    scales: {{
                        y: {{ ticks: {{ color: '#9ca3af' }}, beginAtZero: true }},
                        x: {{ ticks: {{ color: '#9ca3af' }} }}
                    }}
                }}
            }});
        }}
    </script>
    '''
    
    # Step 4: Build recent activity HTML
    activity_html = '''
    <div class="bg-white/5 p-6 rounded-2xl border border-white/10">
        <h3 class="text-lg font-bold mb-4">Recent Activity</h3>
        <div class="space-y-3">
            <div class="flex items-center justify-between py-2 border-b border-white/10">
                <div class="flex items-center gap-3">
                    <div class="w-2 h-2 bg-green-400 rounded-full"></div>
                    <span class="text-sm">New user registered</span>
                </div>
                <span class="text-xs text-gray-500">5 minutes ago</span>
            </div>
            <div class="flex items-center justify-between py-2 border-b border-white/10">
                <div class="flex items-center gap-3">
                    <div class="w-2 h-2 bg-blue-400 rounded-full"></div>
                    <span class="text-sm">Order #1234 completed</span>
                </div>
                <span class="text-xs text-gray-500">32 minutes ago</span>
            </div>
            <div class="flex items-center justify-between py-2 border-b border-white/10">
                <div class="flex items-center gap-3">
                    <div class="w-2 h-2 bg-purple-400 rounded-full"></div>
                    <span class="text-sm">Revenue target reached 75%</span>
                </div>
                <span class="text-xs text-gray-500">1 hour ago</span>
            </div>
            <div class="flex items-center justify-between py-2">
                <div class="flex items-center gap-3">
                    <div class="w-2 h-2 bg-yellow-400 rounded-full"></div>
                    <span class="text-sm">New feature deployed</span>
                </div>
                <span class="text-xs text-gray-500">3 hours ago</span>
            </div>
        </div>
    </div>
    '''
    
    # Step 5: Build complete dashboard HTML
    dashboard_html = f'''
    <div class="p-8">
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-3xl font-bold">Overview</h1>
            <p class="text-gray-400" id="currentDateTime"></p>
        </div>
        
        {kpi_cards_html}
        
        {chart_html}
        
        {activity_html}
    </div>
    
    <script>
        function updateDateTime() {{
            const now = new Date();
            const options = {{ year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' }};
            const dateTimeEl = document.getElementById('currentDateTime');
            if (dateTimeEl) dateTimeEl.textContent = now.toLocaleDateString('en-US', options);
        }}
        updateDateTime();
        setInterval(updateDateTime, 60000);
    </script>
    '''
    
    print(f"  ✅ Dashboard rendered with {len(kpi_items) if kpi_items else 4} KPI cards")
    return dashboard_html


def get_default_kpi_cards() -> str:
    """Return default KPI cards if extraction fails"""
    return '''
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="bg-white/5 p-6 rounded-2xl border border-white/10">
            <div class="flex justify-between items-start mb-2">
                <p class="text-gray-400 text-sm">Revenue</p>
                <i data-lucide="dollar-sign" class="w-5 h-5 text-green-400"></i>
            </div>
            <h3 class="text-2xl font-bold mt-1">$48,293</h3>
            <p class="text-green-400 text-sm mt-2">+12.5%</p>
        </div>
        <div class="bg-white/5 p-6 rounded-2xl border border-white/10">
            <div class="flex justify-between items-start mb-2">
                <p class="text-gray-400 text-sm">Users</p>
                <i data-lucide="users" class="w-5 h-5 text-blue-400"></i>
            </div>
            <h3 class="text-2xl font-bold mt-1">12,402</h3>
            <p class="text-green-400 text-sm mt-2">+8.2%</p>
        </div>
        <div class="bg-white/5 p-6 rounded-2xl border border-white/10">
            <div class="flex justify-between items-start mb-2">
                <p class="text-gray-400 text-sm">Orders</p>
                <i data-lucide="shopping-cart" class="w-5 h-5 text-purple-400"></i>
            </div>
            <h3 class="text-2xl font-bold mt-1">843</h3>
            <p class="text-green-400 text-sm mt-2">+5.3%</p>
        </div>
        <div class="bg-white/5 p-6 rounded-2xl border border-white/10">
            <div class="flex justify-between items-start mb-2">
                <p class="text-gray-400 text-sm">Bounce Rate</p>
                <i data-lucide="activity" class="w-5 h-5 text-red-400"></i>
            </div>
            <h3 class="text-2xl font-bold mt-1">24.8%</h3>
            <p class="text-red-400 text-sm mt-2">-2.1%</p>
        </div>
    </div>
    '''

















def enforce_strict_dashboard_rules(html_content: str) -> str:
    """Ultra-strict enforcement for dashboard projects - removes everything not allowed"""
    import re
    
    print("🔒 ENFORCING STRICT DASHBOARD RULES...")
    
    # 1. Remove any footer
    html_content = re.sub(r'<footer.*?</footer>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. Remove hero sections with background images
    html_content = re.sub(r'<section[^>]*h-screen[^>]*>.*?<img[^>]*>.*?</section>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<section[^>]*relative[^>]*>.*?<img[^>]*background|hero-bg.*?</section>', '', html_content, flags=re.DOTALL)
    
    # 3. Remove forbidden elements
    remove_patterns = [
        r'reservation-modal',
        r'quickReserveBtn',
        r'cart-sidebar',
        r'checkout-modal',
        r'success-modal',
        r'trust badge',
        r'Book a Table',
        r'reservation',
        r'testimonial',
        r'4\.9/5 Rating',
        r'50k\+ Customers'
    ]
    
    for pattern in remove_patterns:
        html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE)
    
    # 4. Force correct navigation (only 3 links)
    nav_pattern = r'<nav.*?</nav>'
    strict_nav = '''
    <nav class="bg-zinc-950 border-b border-white/10 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <i class="fas fa-chart-line text-3xl text-amber-500"></i>
                <span class="text-2xl font-bold">Dashboard</span>
            </div>
            <div class="flex gap-10 text-sm font-medium">
                <a href="#" onclick="showPage('home')" class="nav-link active flex items-center gap-2" data-page="home">
                    <i class="fas fa-home"></i> Overview
                </a>
                <a href="#" onclick="showPage('analytics')" class="nav-link flex items-center gap-2" data-page="analytics">
                    <i class="fas fa-chart-bar"></i> Analytics
                </a>
                <a href="#" onclick="showPage('settings')" class="nav-link flex items-center gap-2" data-page="settings">
                    <i class="fas fa-cog"></i> Settings
                </a>
            </div>
            <div id="current-datetime" class="text-sm text-gray-400"></div>
        </div>
    </nav>
    '''
    html_content = re.sub(nav_pattern, strict_nav, html_content, flags=re.DOTALL)
    
    # 5. Remove any remaining unwanted sections
    html_content = re.sub(r'id="page_(shop|cart|reservations|menu|login|signup)"', '', html_content)
    
    print("✅ Strict dashboard rules fully enforced")
    return html_content














def detect_dashboard_from_content(page_contents: Dict[str, Any], user_prompt: str = "") -> bool:
    """
    Detect if this is a dashboard/analytics project by checking extracted page content.
    Returns True if dashboard indicators are found.
    """
    # Get home page content (already extracted HTML)
    home_content = page_contents.get('page', '')
    
    # Check for dashboard indicators in the extracted content
    dashboard_indicators = [
        'kpiData' in home_content,
        'ResponsiveContainer' in home_content,
        'recharts' in home_content,
        'LineChart' in home_content and 'CartesianGrid' in home_content,
        'BarChart' in home_content and 'XAxis' in home_content,
        'KPI' in home_content and ('Revenue' in home_content or 'Users' in home_content),
        'DollarSign' in home_content and 'Users' in home_content and 'Activity' in home_content,
    ]
    
    is_dashboard = any(dashboard_indicators)
    
    # Also check user prompt as fallback
    if not is_dashboard:
        prompt_keywords = ['dashboard', 'analytics', 'kpi', 'metrics', 'overview', 'reports', 'monitoring']
        is_dashboard = any(keyword in user_prompt.lower() for keyword in prompt_keywords)
    
    # Print debug info
    if is_dashboard:
        print(f"📊 DASHBOARD DETECTED!")
        for indicator in dashboard_indicators:
            if indicator:
                print(f"   ✅ Found: {indicator}")
    
    return is_dashboard















def is_dashboard_project(user_prompt: str, files: Dict[str, Any]) -> bool:
    """Detect if this is a dashboard/analytics project"""
    
    dashboard_keywords = [
        'dashboard', 'analytics', 'admin', 'metrics', 'statistics',
        'insights', 'overview', 'reports', 'monitoring', 'kpi',
        'data visualization', 'chart', 'analytics dashboard'
    ]
    
    # Check user prompt
    if any(keyword in user_prompt.lower() for keyword in dashboard_keywords):
        return True
    
    # Check file contents for dashboard indicators
    for file_path, file_content in files.items():
        if 'recharts' in file_content or 'ResponsiveContainer' in file_content:
            return True
        if 'KPI' in file_content or 'Revenue' in file_content:
            return True
    
    return False
















def preserve_dashboard_content(extracted: str, route_name: str) -> str:
    """Special preservation for dashboard pages to keep all charts and functionality"""
    
    if route_name not in ('page', 'home', 'dashboard', 'overview'):
        return extracted
    
    print("📊 Preserving dashboard content with charts...")
    
    # Keep recharts components - don't convert or remove them
    # These should remain as React components in the HTML preview
    
    # Ensure date display is preserved
    if 'new Date().toLocaleString()' in extracted:
        extracted = extracted.replace(
            'new Date().toLocaleString()',
            'new Date().toLocaleString()'
        )
    
    # Keep all KPI cards
    kpi_pattern = r'<div class="grid grid-cols-4 gap-6">[\s\S]*?</div>'
    if not re.search(kpi_pattern, extracted):
        print("   ⚠️ KPI cards missing - preserving from source")
    
    # Ensure chart containers exist
    if 'ResponsiveContainer' not in extracted:
        print("   ⚠️ Charts missing - preserving from source")
    
    # Keep analytics page export button
    if 'analytics' in extracted and 'Export CSV' not in extracted:
        print("   ⚠️ Export button missing - preserving from source")
    
    # Keep settings page form
    if 'settings' in extracted and 'input' not in extracted:
        print("   ⚠️ Settings form missing - preserving from source")
    
    print("✅ Dashboard content preserved")
    return extracted










def inject_restaurant_features(html_content: str, brand_name: str, user_prompt: str = "", force_skip: bool = False) -> str:
    """Inject restaurant-specific features like booking modal, menu cards, etc."""
    
    # Force skip if requested
    if force_skip:
        print("🚫 Force skip - restaurant features injection disabled")
        return html_content
    
    # ========== SKIP FOR DASHBOARD PROJECTS ==========
    dashboard_keywords = ['dashboard', 'analytics', 'admin', 'metrics', 'statistics', 'insights', 'overview', 'reports', 'monitoring', 'kpi']
    if any(keyword in user_prompt.lower() for keyword in dashboard_keywords):
        print("📊 Dashboard detected - skipping restaurant features injection")
        return html_content
    
    # Detect if this is a restaurant website
    restaurant_keywords = ['restaurant', 'cafe', 'dining', 'menu', 'culinary', 'chef', 'bistro', 'cuisine', 'fine dining']
    is_restaurant = any(keyword in user_prompt.lower() for keyword in restaurant_keywords)
    
    # Also check HTML content for restaurant indicators
    if not is_restaurant:
        restaurant_html_indicators = ['menu', 'reservation', 'booking', 'table', 'dining', 'chef']
        is_restaurant = any(indicator in html_content.lower() for indicator in restaurant_html_indicators)
    
    if not is_restaurant:
        print("🍽️ Not a restaurant website - skipping restaurant features injection")
        return html_content
    
    print("🍽️ Restaurant detected - injecting restaurant features...")
    
    # ========== 1. INJECT RESERVATION MODAL CSS ==========
    restaurant_css = '''
    /* Restaurant Reservation Modal Styles */
    .reservation-modal {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(12px);
        z-index: 1000;
        align-items: center;
        justify-content: center;
    }
    
    .reservation-modal.active {
        display: flex;
    }
    
    .reservation-modal-content {
        background: linear-gradient(135deg, #1a1a2e, #0f0f12);
        border-radius: 28px;
        padding: 2rem;
        max-width: 500px;
        width: 90%;
        text-align: center;
        border: 1px solid rgba(139, 92, 246, 0.3);
        animation: modalSlideIn 0.3s ease-out;
    }
    
    @keyframes modalSlideIn {
        from {
            transform: translateY(-50px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    .reservation-success-icon {
        width: 80px;
        height: 80px;
        background: linear-gradient(135deg, #10b981, #059669);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1.5rem;
    }
    
    .reservation-success-icon i {
        font-size: 40px;
        color: white;
    }
    
    .reservation-modal h3 {
        font-size: 1.8rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #c084fc, #f472b6);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    '''
    
    # Inject CSS into style tag
    if '<style>' in html_content:
        html_content = html_content.replace('</style>', restaurant_css + '\n</style>', 1)
    else:
        html_content = html_content.replace('<head>', f'<head><style>{restaurant_css}</style>', 1)
    
    # ========== 2. INJECT RESERVATION MODAL HTML ==========
    reservation_modal = f'''
    <!-- Reservation Success Modal -->
    <div id="reservationModal" class="reservation-modal">
        <div class="reservation-modal-content">
            <div class="reservation-success-icon">
                <i class="fas fa-check"></i>
            </div>
            <h3>Table Reserved! 🎉</h3>
            <p>Your table has been successfully booked for <strong><span id="reservationDate"></span></strong> at <strong><span id="reservationTime"></span></strong> for <strong><span id="reservationGuests"></span></strong> guest(s).</p>
            <p class="text-gray-400 text-sm mt-2">A confirmation has been sent to your email.</p>
            <button class="modal-close-btn" onclick="closeReservationModal()" style="margin-top: 1rem; background: linear-gradient(135deg, #8b5cf6, #ec4899); color: white; border: none; padding: 0.75rem 2rem; border-radius: 9999px; font-weight: 600; cursor: pointer;">Wonderful!</button>
        </div>
    </div>
    
    <!-- Quick Reservation Button (Floating) -->
    <button id="quickReserveBtn" class="fixed bottom-8 right-8 z-50 bg-gradient-to-r from-amber-500 to-orange-600 text-white px-6 py-3 rounded-full shadow-lg shadow-amber-500/30 hover:scale-105 transition-all duration-300 flex items-center gap-2">
        <i class="fas fa-calendar-check"></i>
        Book a Table
    </button>
    '''
    
    # Inject modal before closing body
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', reservation_modal + '\n</body>', 1)
    
    # ========== 3. INJECT RESTAURANT JAVASCRIPT ==========
    restaurant_js = '''
    <script>
    // Restaurant Reservation Functions
    function openReservationModal() {
        const modal = document.getElementById('reservationModal');
        if (modal) modal.classList.add('active');
    }
    
    function closeReservationModal() {
        const modal = document.getElementById('reservationModal');
        if (modal) modal.classList.remove('active');
    }
    
    function showReservationSuccess(date, time, guests, name, email) {
        const modal = document.getElementById('reservationModal');
        const dateSpan = document.getElementById('reservationDate');
        const timeSpan = document.getElementById('reservationTime');
        const guestsSpan = document.getElementById('reservationGuests');
        
        if (dateSpan) dateSpan.textContent = date;
        if (timeSpan) timeSpan.textContent = time;
        if (guestsSpan) guestsSpan.textContent = guests;
        
        if (modal) modal.classList.add('active');
        
        // Save to localStorage
        const reservation = {
            id: Date.now(),
            name: name,
            email: email,
            guests: guests,
            date: date,
            time: time,
            createdAt: new Date().toISOString()
        };
        
        let reservations = JSON.parse(localStorage.getItem('restaurant_reservations') || '[]');
        reservations.push(reservation);
        localStorage.setItem('restaurant_reservations', JSON.stringify(reservations));
        
        console.log('✅ Reservation saved:', reservation);
    }
    
    // Handle booking form submission
    function handleRestaurantBooking(event) {
        event.preventDefault();
        
        const name = document.getElementById('reservationName')?.value;
        const email = document.getElementById('reservationEmail')?.value;
        const guests = document.getElementById('reservationGuestsSelect')?.value;
        const date = document.getElementById('reservationDateSelect')?.value;
        const time = document.getElementById('reservationTimeSelect')?.value;
        
        if (!name || !email || !guests || !date || !time) {
            alert('Please fill in all required fields.');
            return;
        }
        
        if (!email.includes('@')) {
            alert('Please enter a valid email address.');
            return;
        }
        
        const today = new Date().toISOString().split('T')[0];
        if (date < today) {
            alert('Please select a future date.');
            return;
        }
        
        // Format date for display
        const formattedDate = new Date(date).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        showReservationSuccess(formattedDate, time, guests, name, email);
        
        // Reset form
        const form = document.getElementById('restaurantBookingForm');
        if (form) form.reset();
    }
    
    // Quick reserve button
    document.addEventListener('DOMContentLoaded', function() {
        const quickBtn = document.getElementById('quickReserveBtn');
        if (quickBtn) {
            quickBtn.addEventListener('click', function() {
                const reservationsSection = document.getElementById('page_reservations');
                if (reservationsSection) {
                    reservationsSection.scrollIntoView({ behavior: 'smooth' });
                    if (typeof showPage === 'function') {
                        showPage('reservations');
                    }
                }
            });
        }
        
        // Set minimum date for date pickers
        const today = new Date().toISOString().split('T')[0];
        document.querySelectorAll('input[type="date"]').forEach(input => {
            if (!input.value) {
                input.min = today;
            }
        });
        
        // Initialize booking form
        const bookingForm = document.getElementById('restaurantBookingForm');
        if (bookingForm && !bookingForm.onsubmit) {
            bookingForm.onsubmit = handleRestaurantBooking;
        }
    });
    
    // Close modal on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const modal = document.getElementById('reservationModal');
            if (modal && modal.classList.contains('active')) {
                closeReservationModal();
            }
        }
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('reservationModal');
        if (event.target === modal) {
            closeReservationModal();
        }
    });
    </script>
    '''
    
    # Inject JavaScript
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', restaurant_js + '\n</body>', 1)
    
    print(f"🍽️ Injected restaurant features: modal, floating button, and JavaScript")
    
    # CRITICAL: Return the modified html_content
    return html_content









def fix_restaurant_reservation_form(html_content: str) -> str:
    """Bulletproof fix for restaurant reservation forms - ensures proper IDs and submit handling"""
    
    # Check if this is a restaurant page with reservation form
    if 'page_reservations' not in html_content:
        return html_content
    
    print("🍽️ Fixing restaurant reservation form...")
    
    # ========== METHOD 1: Find and replace the entire reservation form ==========
    # Pattern to find the reservation page content
    reservation_page_pattern = r'(<div id="page_reservations"[^>]*>)(.*?)(</div>\s*(?=<div id="page_|$|<footer|</body>))'
    
    def fix_reservation_form(match):
        page_opening = match.group(1)
        page_content = match.group(2)
        page_closing = match.group(3)
        
        # Check if the form already has the correct IDs
        if 'reservationName' in page_content and 'reservationEmail' in page_content:
            print("  ✅ Reservation form already has correct IDs")
            return match.group(0)
        
        # Check if there's a form element
        form_match = re.search(r'<form[^>]*>([\s\S]*?)</form>', page_content, re.DOTALL)
        if not form_match:
            print("  ⚠️ No form found in reservations page")
            return match.group(0)
        
        # Extract the existing form elements
        existing_form = form_match.group(0)
        existing_inputs = form_match.group(1)
        
        # Create a completely new form with proper IDs
        new_form = '''        <form id="restaurantBookingForm" class="bg-white/5 p-8 rounded-2xl border border-white/10 space-y-4">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">Full Name *</label>
                    <input type="text" id="reservationName" name="name" placeholder="Your full name" required 
                           class="w-full p-3 bg-black/20 rounded-lg border border-white/10 text-white placeholder-gray-400 focus:border-amber-500 focus:outline-none transition">
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">Email Address *</label>
                    <input type="email" id="reservationEmail" name="email" placeholder="your@email.com" required 
                           class="w-full p-3 bg-black/20 rounded-lg border border-white/10 text-white placeholder-gray-400 focus:border-amber-500 focus:outline-none transition">
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">Phone Number</label>
                    <input type="tel" id="reservationPhone" name="phone" placeholder="(555) 123-4567" 
                           class="w-full p-3 bg-black/20 rounded-lg border border-white/10 text-white placeholder-gray-400 focus:border-amber-500 focus:outline-none transition">
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-1">Date *</label>
                        <input type="date" id="reservationDateSelect" name="date" required 
                               class="w-full p-3 bg-black/20 rounded-lg border border-white/10 text-white focus:border-amber-500 focus:outline-none transition">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-1">Time *</label>
                        <select id="reservationTimeSelect" name="time" required 
                                class="w-full p-3 bg-black/20 rounded-lg border border-white/10 text-white focus:border-amber-500 focus:outline-none transition">
                            <option value="">Select Time</option>
                            <option value="5:00 PM">5:00 PM</option>
                            <option value="6:00 PM">6:00 PM</option>
                            <option value="7:00 PM">7:00 PM</option>
                            <option value="8:00 PM">8:00 PM</option>
                            <option value="9:00 PM">9:00 PM</option>
                        </select>
                    </div>
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">Number of Guests *</label>
                    <select id="reservationGuestsSelect" name="guests" required 
                            class="w-full p-3 bg-black/20 rounded-lg border border-white/10 text-white focus:border-amber-500 focus:outline-none transition">
                        <option value="1">1 Guest</option>
                        <option value="2">2 Guests</option>
                        <option value="3">3 Guests</option>
                        <option value="4">4 Guests</option>
                        <option value="5">5 Guests</option>
                        <option value="6">6 Guests</option>
                        <option value="7">7 Guests</option>
                        <option value="8">8+ Guests</option>
                    </select>
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">Special Requests</label>
                    <textarea id="reservationRequests" name="requests" rows="3" 
                              placeholder="Dietary restrictions, special occasions, etc."
                              class="w-full p-3 bg-black/20 rounded-lg border border-white/10 text-white placeholder-gray-400 focus:border-amber-500 focus:outline-none transition"></textarea>
                </div>
            </div>
            
            <button type="submit" class="w-full py-3 bg-gradient-to-r from-amber-500 to-orange-600 rounded-lg font-bold text-white hover:opacity-90 hover:scale-105 transition-all duration-300">
                <i class="fas fa-check-circle mr-2"></i>Confirm Reservation
            </button>
        </form>'''
        
        # Replace the form in the page content
        fixed_content = page_content.replace(existing_form, new_form)
        
        # Also ensure the page has proper container classes
        if 'container mx-auto' not in fixed_content:
            fixed_content = re.sub(
                r'(<div class="min-h-screen[^>]*>)',
                r'\1<div class="container mx-auto max-w-xl">',
                fixed_content
            )
            fixed_content = fixed_content.replace('</div>', '</div>', 1)  # Close the container
        
        print("  ✅ Replaced reservation form with bulletproof version")
        return page_opening + fixed_content + page_closing
    
    # Apply the fix
    html_content = re.sub(reservation_page_pattern, fix_reservation_form, html_content, flags=re.DOTALL)
    
    # ========== METHOD 2: Ensure the JavaScript is properly wired ==========
    # Check if handleRestaurantBooking function exists and is connected
    if 'handleRestaurantBooking' in html_content:
        # Make sure the form onsubmit is set
        html_content = re.sub(
            r'<form[^>]*id="restaurantBookingForm"[^>]*>',
            '<form id="restaurantBookingForm" onsubmit="handleRestaurantBooking(event); return false;" class="bg-white/5 p-8 rounded-2xl border border-white/10 space-y-4">',
            html_content
        )
        print("  ✅ Connected form to handleRestaurantBooking function")
    
    # ========== METHOD 3: Add missing JavaScript for form handling if needed ==========
    if 'handleRestaurantBooking' not in html_content:
        print("  ⚠️ handleRestaurantBooking function missing - adding it")
        
        reservation_handler = '''
    <script>
    // Restaurant Reservation Handler - Auto-injected
    document.addEventListener('DOMContentLoaded', function() {
        const bookingForm = document.getElementById('restaurantBookingForm');
        if (bookingForm && !bookingForm.hasAttribute('data-handler-bound')) {
            bookingForm.setAttribute('data-handler-bound', 'true');
            bookingForm.onsubmit = function(event) {
                event.preventDefault();
                
                const name = document.getElementById('reservationName')?.value;
                const email = document.getElementById('reservationEmail')?.value;
                const guests = document.getElementById('reservationGuestsSelect')?.value;
                const date = document.getElementById('reservationDateSelect')?.value;
                const time = document.getElementById('reservationTimeSelect')?.value;
                
                if (!name || !email || !guests || !date || !time) {
                    alert('❌ Please fill in all required fields.');
                    return false;
                }
                
                if (!email.includes('@')) {
                    alert('❌ Please enter a valid email address.');
                    return false;
                }
                
                const today = new Date().toISOString().split('T')[0];
                if (date < today) {
                    alert('❌ Please select a future date.');
                    return false;
                }
                
                // Format date for display
                const formattedDate = new Date(date).toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
                
                // Show success modal
                const modal = document.getElementById('reservationModal');
                const dateSpan = document.getElementById('reservationDate');
                const timeSpan = document.getElementById('reservationTime');
                const guestsSpan = document.getElementById('reservationGuests');
                
                if (dateSpan) dateSpan.textContent = formattedDate;
                if (timeSpan) timeSpan.textContent = time;
                if (guestsSpan) guestsSpan.textContent = guests;
                
                if (modal) modal.classList.add('active');
                
                // Save to localStorage
                const reservation = {
                    id: Date.now(),
                    name: name,
                    email: email,
                    guests: guests,
                    date: date,
                    time: time,
                    createdAt: new Date().toISOString()
                };
                
                let reservations = JSON.parse(localStorage.getItem('restaurant_reservations') || '[]');
                reservations.push(reservation);
                localStorage.setItem('restaurant_reservations', JSON.stringify(reservations));
                
                console.log('✅ Reservation saved:', reservation);
                
                // Reset form
                bookingForm.reset();
                
                return false;
            };
            console.log('✅ Restaurant booking form initialized');
        }
    });
    </script>
    '''
        
        # Inject the handler before closing body
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', reservation_handler + '\n</body>', 1)
        print("  ✅ Injected missing reservation handler")
    
    # ========== METHOD 4: Fix date picker min date ==========
    date_fix_script = '''
    <script>
    // Set minimum date for all date pickers
    (function() {
        const today = new Date().toISOString().split('T')[0];
        document.querySelectorAll('input[type="date"]').forEach(function(input) {
            if (!input.min && !input.value) {
                input.min = today;
            }
        });
    })();
    </script>
    '''
    
    if '</body>' in html_content and 'date picker' not in html_content:
        html_content = html_content.replace('</body>', date_fix_script + '\n</body>', 1)
        print("  ✅ Injected date picker min date fix")
    
    return html_content





















































def remove_duplicate_cart_systems(html: str) -> str:
    """Remove any custom cart systems, keep only the MASTER CART SYSTEM"""
    import re
    
    # Pattern to find custom cart system (the one with 'items = []' and 'totalItems = 0')
    custom_cart_pattern = r'// Cart System \(placeholders for backend integration\)[\s\S]*?function openCheckoutModal\(\) \{[^}]*\}[^}]*\}'
    
    # Remove it
    html = re.sub(custom_cart_pattern, '', html, flags=re.DOTALL)
    
    # Also remove any duplicate 'let cart = []' that appears before master system
    duplicate_cart = r'let cart = \[\];\s*// Assume this is managed by backend'
    html = re.sub(duplicate_cart, '', html, flags=re.DOTALL)
    
    # Remove duplicate updateCartPage function (keep the master one)
    duplicate_update = r'function updateCartPage\(\) \{[^}]*cart\.length[\s\S]*?\}\s*function showToast'
    html = re.sub(duplicate_update, '', html, flags=re.DOTALL)
    
    print("🧹 Removed duplicate cart systems")
    return html

def ensure_master_cart_only(html: str) -> str:
    """Ensure only ONE cart system exists - the MASTER one"""
    import re
    
    # Check if MASTER CART SYSTEM exists
    if '// ========== MASTER CART SYSTEM ==========' not in html:
        print("⚠️ MASTER CART SYSTEM not found - adding it")
        # Master system will be added by your existing injection
        return html
    
    # Remove ANY script that contains 'let items = []' (custom system indicator)
    html = re.sub(
        r'<script[^>]*>[\s\S]*?let items\s*=\s*\[\][\s\S]*?</script>',
        '',
        html,
        flags=re.DOTALL
    )
    
    # Remove ANY script that contains 'totalItems = 0' before master system
    html = re.sub(
        r'<script[^>]*>(?:(?!MASTER CART SYSTEM)[\s\S])*?totalItems\s*=\s*0[\s\S]*?</script>',
        '',
        html,
        flags=re.DOTALL
    )
    
    print("🧹 Ensured only MASTER CART SYSTEM remains")
    return html

def fix_duplicate_functions(html: str) -> str:
    """Remove duplicate function definitions"""
    import re
    
    # Find all function definitions
    func_pattern = r'function\s+(\w+)\s*\('
    functions = re.findall(func_pattern, html)
    
    # Find duplicates
    from collections import Counter
    duplicates = [name for name, count in Counter(functions).items() if count > 1]
    
    for func_name in duplicates:
        # Remove the first occurrence (keep the last/master one)
        pattern = rf'function\s+{func_name}\s*\([^{{]*\)\s*\{{[^{{}}]*(?:\{{[^{{}}]*\}}[^{{}}]*)*\}}'
        matches = re.findall(pattern, html, re.DOTALL)
        if len(matches) > 1:
            # Keep the last one (master), remove others
            for match in matches[:-1]:
                html = html.replace(match, '', 1)
            print(f"🧹 Removed duplicate function: {func_name}")
    
    return html
















def replace_map_block(content: str, array_name: str, replacement: str) -> str:
    """Replace {arrayName.map(...)} block by counting braces - handles nested JSX"""
    import re
    
    # First, find the map block
    start_pattern = rf'\{{\s*{array_name}\.map\('
    match = re.search(start_pattern, content)
    if not match:
        print(f"  ❌ Could not find {array_name}.map() block to replace")
        return content
    
    start = match.start()
    brace_count = 0
    i = start
    
    while i < len(content):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end = i + 1
                
                # Now look for the parent grid container that contains this map block
                # Search backwards for the opening grid div
                grid_start = -1
                search_pos = start - 1
                nested_count = 0
                
                while search_pos >= 0:
                    # Look for grid container opening
                    if content[search_pos:search_pos+5] == '<div ':
                        # Check if this div has grid classes
                        div_end = content.find('>', search_pos)
                        if div_end != -1:
                            div_content = content[search_pos:div_end]
                            if 'grid' in div_content and 'md:grid-cols' in div_content:
                                # Found a grid container
                                if nested_count == 0:
                                    grid_start = search_pos
                                    break
                                else:
                                    nested_count -= 1
                    # Check for closing div to handle nesting
                    elif content[search_pos:search_pos+6] == '</div>':
                        nested_count += 1
                    search_pos -= 1
                
                # If we found a grid container, find its closing tag
                if grid_start != -1:
                    # Find the matching closing </div> for this grid
                    div_count = 1
                    search_pos = grid_start
                    grid_end = -1
                    
                    while search_pos < len(content):
                        if content[search_pos:search_pos+5] == '<div ' and search_pos != grid_start:
                            div_count += 1
                        elif content[search_pos:search_pos+6] == '</div>':
                            div_count -= 1
                            if div_count == 0:
                                grid_end = search_pos + 6
                                break
                        search_pos += 1
                    
                    if grid_end != -1:
                        # Replace the entire grid container
                        content = content[:grid_start] + replacement + content[grid_end:]
                        print(f"  ✅ Replaced entire grid container with {replacement.count('bg-white/5')} cards")
                        return content
                
                # Fallback: just replace the map block
                content = content[:start] + replacement + content[end:]
                print(f"  ✅ Replaced {array_name}.map() block (pos {start}→{end})")
                return content
        i += 1
    
    print(f"  ❌ Could not find closing brace for {array_name}.map()")
    return content















def render_array_to_html(content: str) -> str:
    """Convert React arrays to HTML BEFORE sending to AI - handles arrays both inside and outside components"""
    
    import re

    ICON_MAP = {
        # Core
        'Cpu': 'cpu', 'Zap': 'zap', 'Globe': 'globe', 'Shield': 'shield',
        'Rocket': 'rocket', 'Sparkles': 'sparkles', 'Heart': 'heart', 'Star': 'star',
        # Shopping / E-commerce
        'ShoppingBag': 'shopping-bag', 'ShoppingCart': 'shopping-cart',
        'Package': 'package', 'Truck': 'truck', 'CreditCard': 'credit-card',
        'DollarSign': 'dollar-sign', 'Tag': 'tag', 'Gift': 'gift',
        # People
        'Users': 'users', 'User': 'user', 'UserCheck': 'user-check',
        # Communication
        'Mail': 'mail', 'Phone': 'phone', 'Send': 'send',
        'MessageCircle': 'message-circle', 'MessageSquare': 'message-square',
        # Navigation
        'MapPin': 'map-pin', 'Map': 'map', 'Navigation': 'navigation',
        'Compass': 'compass', 'ArrowRight': 'arrow-right', 'ArrowLeft': 'arrow-left',
        'ArrowUp': 'arrow-up', 'ArrowDown': 'arrow-down', 'ExternalLink': 'external-link',
        'Link': 'link', 'Share': 'share',
        # UI Controls
        'Plus': 'plus', 'Minus': 'minus', 'X': 'x', 'Menu': 'menu',
        'Search': 'search', 'Filter': 'filter', 'Settings': 'settings',
        'Bell': 'bell', 'Eye': 'eye', 'EyeOff': 'eye-off',
        'Lock': 'lock', 'Unlock': 'unlock',
        # Status / Feedback
        'Check': 'check', 'CheckCircle': 'check-circle', 'AlertCircle': 'alert-circle',
        'AlertTriangle': 'alert-triangle', 'Info': 'info', 'HelpCircle': 'help-circle',
        'ThumbsUp': 'thumbs-up', 'Award': 'award',
        # Tech
        'Code': 'code', 'Terminal': 'terminal', 'Database': 'database',
        'Server': 'server', 'Cloud': 'cloud', 'Wifi': 'wifi',
        'Monitor': 'monitor', 'Smartphone': 'smartphone', 'Tablet': 'tablet',
        'Layers': 'layers', 'Layout': 'layout', 'Battery': 'battery',
        # Data
        'TrendingUp': 'trending-up', 'BarChart': 'bar-chart',
        'PieChart': 'pie-chart', 'Activity': 'activity',
        # Media
        'Camera': 'camera', 'Image': 'image', 'Video': 'video',
        'Music': 'music', 'Headphones': 'headphones',
        # Files
        'Book': 'book', 'BookOpen': 'book-open', 'FileText': 'file-text',
        'Folder': 'folder', 'Download': 'download', 'Upload': 'upload',
        # Time
        'Clock': 'clock', 'Calendar': 'calendar',
        # Business
        'Briefcase': 'briefcase', 'Building': 'building',
        'GraduationCap': 'graduation-cap', 'Lightbulb': 'lightbulb',
        'Target': 'target', 'Home': 'home',
        # Health / Fitness
        'Dumbbell': 'dumbbell', 'Flame': 'flame',
        # Nature / Garden
        'Sprout': 'sprout', 'Leaf': 'leaf', 'Flower': 'flower',
        'Flower2': 'flower-2', 'Trees': 'trees', 'Mountain': 'mountain',
        'Waves': 'waves', 'Fish': 'fish', 'Bug': 'bug',
        # Weather
        'Sun': 'sun', 'Moon': 'moon', 'Wind': 'wind',
        'Droplets': 'droplets', 'CloudRain': 'cloud-rain',
        'Thermometer': 'thermometer', 'Umbrella': 'umbrella',
        'Snowflake': 'snowflake',
        # Food & Lifestyle
        'Coffee': 'coffee', 'Scissors': 'scissors',
        'Tool': 'tool', 'Wrench': 'wrench',
        # Fitness specific
        'Trophy': 'trophy', 'Medal': 'medal', 'Activity': 'activity',
    }








    # ========== STEP 1: PRESERVE TRUST INDICATORS ==========
    trust_pattern = r'(<div\s+className="(?:absolute\s+)?(?:bottom-\d+\s+left-0\s+right-0\s+)?flex(?:\s+flex-wrap)?\s+(?:justify-center|gap-\d+)[^"]*"[^>]*>)([\s\S]*?)(</div>)'

    def preserve_trust_indicators(match):
        opening = match.group(1)
        inner = match.group(2)
        closing = match.group(3)

        opening = opening.replace('className=', 'class=')

        inner = re.sub(r'<Star\s+className="([^"]*)"\s*/>', r'<i class="fas fa-star \1"></i>', inner)
        inner = re.sub(r'<Star\s+className="([^"]+)"/>', r'<i class="fas fa-star \1"></i>', inner)
        inner = re.sub(r'<Star\s+className=\'([^\']+)\'/>', r'<i class="fas fa-star \1"></i>', inner)

        inner = re.sub(r'<Users\s+className="([^"]*)"\s*/>', r'<i class="fas fa-users \1"></i>', inner)
        inner = re.sub(r'<Users\s+className="([^"]+)"/>', r'<i class="fas fa-users \1"></i>', inner)
        inner = re.sub(r'<Users\s+className=\'([^\']+)\'/>', r'<i class="fas fa-users \1"></i>', inner)

        inner = re.sub(r'<Shield\s+className="([^"]*)"\s*/>', r'<i class="fas fa-shield-alt \1"></i>', inner)
        inner = re.sub(r'<Shield\s+className="([^"]+)"/>', r'<i class="fas fa-shield-alt \1"></i>', inner)
        inner = re.sub(r'<Shield\s+className=\'([^\']+)\'/>', r'<i class="fas fa-shield-alt \1"></i>', inner)

        return opening + inner + closing

    content = re.sub(trust_pattern, preserve_trust_indicators, content, flags=re.DOTALL)


        
        
        
        
        
        
    # ========== STEP 1.5: SAVE AND RESTORE TRUST INDICATORS ==========
    # Save trust indicators HTML before array processing
    saved_trust_html = ""
    
    # Find and save the trust indicators div
    trust_save_pattern = r'(<div\s+class="absolute bottom-8 left-0 right-0[^>]*>.*?<div\s+class="container mx-auto px-4 flex flex-wrap justify-center gap-12">.*?</div>\s*</div>)'
    trust_match = re.search(trust_save_pattern, content, re.DOTALL)
    
    if trust_match:
        saved_trust_html = trust_match.group(1)
        print(f"  ✅ Saved trust indicators for later restoration")
        
        # Temporarily replace with a marker
        content = content.replace(saved_trust_html, "{{TRUST_INDICATORS_MARKER}}")
        
        
        
        
        
        
        
        
        
        
        
        
        
        

    # ========== STEP 2: CONVERT HERO BADGE ICONS ==========
    # Convert Star in badge/pill
    content = re.sub(r'<Star\s+className="([^"]*)"\s*/>', r'<i class="fas fa-star \1"></i>', content)
    content = re.sub(r'<Sparkles\s+className="([^"]*)"\s*/>', r'<i class="fas fa-sparkles \1"></i>', content)















    # ========== STEP 3: FEATURES ARRAY ==========
    features_html = None
    
    # Pattern that finds 'const features = [...]' ANYWHERE in the file (including inside component)
    # Uses [\s\S]*? to match across line breaks
    features_match = re.search(r'(?:const|let)\s+features\s*=\s*\[([\s\S]*?)\];?\s*(?=\n\s*(?:const|let|export|return|\}))', content, re.DOTALL)
    
    # Fallback: find inside the component function
    if not features_match:
        features_match = re.search(r'export\s+default\s+function\s+\w+\s*\([^)]*\)\s*\{[\s\S]*?(?:const|let)\s+features\s*=\s*\[([\s\S]*?)\];', content, re.DOTALL)

    if features_match:
        features_content = features_match.group(1)
        
        # Try pattern WITHOUT icon (title, desc) - most common
        feature_pattern_no_icon = r'\{\s*title:\s*["\']([^"\']+)["\']\s*,\s*desc:\s*["\']([^"\']+)["\']'
        features = re.findall(feature_pattern_no_icon, features_content)
        
        # If not found, try with icon (icon, title, desc)
        if not features:
            feature_pattern_with_icon = r'\{\s*icon:\s*(\w+)\s*,\s*title:\s*["\']([^"\']+)["\']\s*,\s*desc:\s*["\']([^"\']+)["\']'
            features = re.findall(feature_pattern_with_icon, features_content)
        
        # If still not found, try with name/description (for projects, etc.)
        if not features:
            feature_pattern_name_desc = r'\{\s*name:\s*["\']([^"\']+)["\']\s*,\s*description:\s*["\']([^"\']+)["\']'
            features = re.findall(feature_pattern_name_desc, features_content)

        if features:
            features_html = '<div class="grid md:grid-cols-4 gap-6">\n'
            for match in features:
                if len(match) == 2:  # title, desc format
                    title, desc = match
                    lucide_icon = 'sparkles'
                else:  # icon, title, desc format
                    icon_name, title, desc = match
                    lucide_icon = ICON_MAP.get(icon_name, 'sparkles')
                
                features_html += f'''
    <div class="bg-white/5 p-6 rounded-2xl border border-white/10 hover:border-purple-500/50 transition-all">
        <i data-lucide="{lucide_icon}" class="w-10 h-10 mb-4 text-purple-400"></i>
        <h3 class="text-xl font-bold mb-2">{title}</h3>
        <p class="text-gray-400 text-sm">{desc}</p>
    </div>'''
            features_html += '\n</div>'
            print(f"  ✅ Rendered {len(features)} features from source array")
        else:
            print(f"  ⚠️ Features array found but no items extracted")
            # Debug: print first 200 chars of features content
            print(f"  📄 Features content preview: {features_content[:200]}...")
    else:
        print(f"  ⚠️ No features array found in source")

    if features_html:
        content = replace_map_block(content, 'features', features_html)












        # ========== STEP 4: FAQS ARRAY ==========
        faqs_html = None

        # Debug: Check if FAQ section exists
        if 'FAQ' in content and 'map' in content:
            print(f"  🔍 FAQ section detected in content")
            # Print a snippet for debugging
            faq_snippet = re.search(r'<section\s+className="py-20 px-4">.*?FAQ.*?</section>', content, re.DOTALL)
            if faq_snippet:
                print(f"  📄 FAQ snippet: {faq_snippet.group(0)[:200]}...")

        # ========== STEP 4.0: HANDLE INLINE PLACEHOLDER FAQ (NO ARRAY) ==========
        # More flexible pattern that matches any FAQ section with inline map
        inline_faq_pattern = r'<section\s+className="py-20 px-4">\s*<div\s+className="container mx-auto max-w-3xl">\s*<h2\s+className="text-4xl font-bold text-center mb-12">FAQ</h2>\s*\{\[.*?\]\.map\([^)]*\)\s*=>\s*\(?\s*<div[^>]*>(.*?)</div>\s*\)?\s*\}'
        
        inline_match = re.search(inline_faq_pattern, content, re.DOTALL)
        
        if inline_match:
            question_template = inline_match.group(1)
            
            # Extract the number range from the source (e.g., [1,2,3,4])
            range_match = re.search(r'\[([0-9,\s]+)\]', content[inline_match.start():inline_match.end()])
            if range_match:
                numbers_str = range_match.group(1)
                numbers = re.findall(r'\d+', numbers_str)
                total_items = len(numbers) if numbers else 4
            else:
                total_items = 4
            
            # Generate proper accordion FAQ HTML
            faqs_html = '<div class="space-y-4">\n'
            for i in range(1, total_items + 1):
                question_text = question_template.replace('{i}', str(i))
                question_text = re.sub(r'\{[^}]+\}', str(i), question_text)
                # Remove any key={i} or other JSX attributes
                question_text = re.sub(r'key=\{[^}]+\}', '', question_text)
                question_text = question_text.strip()
                
                faqs_html += f'''
    <div class="bg-gradient-to-br from-white/5 to-white/3 rounded-2xl border border-white/10 overflow-hidden">
        <button class="faq-btn w-full px-6 py-4 flex justify-between items-center text-left hover:bg-white/5 transition-colors">
            <span class="font-semibold text-white">{question_text}</span>
            <i class="fas fa-plus text-purple-400"></i>
        </button>
        <div class="faq-answer hidden px-6 pb-4 text-gray-400">
            Answer for {question_text}
        </div>
    </div>'''
            faqs_html += '\n</div>'
            
            # Replace the entire placeholder section
            new_faq_section = f'''<section class="py-20 px-4">
        <div class="container mx-auto max-w-3xl">
          <h2 class="text-4xl font-bold text-center mb-12 gradient-text">FAQ</h2>
          {faqs_html}
        </div>
      </section>'''
            
            content = re.sub(inline_faq_pattern, new_faq_section, content, flags=re.DOTALL)
            print(f"  ✅ Converted inline placeholder FAQ to accordion with {total_items} items")

        # ========== STEP 4.1: Try to find faqs array ANYWHERE in the file ==========
        if not faqs_html:
            faqs_match = re.search(r'(?:const|let)\s+faqs\s*=\s*\[([\s\S]*?)\];?\s*(?=\n\s*(?:const|let|return|\}))', content, re.DOTALL)
            
            # Fallback: find inside the component function
            if not faqs_match:
                faqs_match = re.search(r'export\s+default\s+function\s+\w+\s*\([^)]*\)\s*\{[\s\S]*?(?:const|let)\s+faqs\s*=\s*\[([\s\S]*?)\];', content, re.DOTALL)
            
            # Try 'faq' singular as fallback
            if not faqs_match:
                faqs_match = re.search(r'(?:const|let)\s+faq\s*=\s*\[([\s\S]*?)\];', content, re.DOTALL)

            if faqs_match:
                faqs_content = faqs_match.group(1)
                faq_pattern = r'\{\s*(?:q|question):\s*["\']([^"\']+)["\']\s*,\s*(?:a|answer):\s*["\']([^"\']+)["\']\s*\}'
                faqs = re.findall(faq_pattern, faqs_content)

                if faqs:
                    faqs_html = '<div class="space-y-4">\n'
                    for q, a in faqs:
                        faqs_html += f'''
    <div class="bg-white/5 rounded-2xl border border-white/10 overflow-hidden">
        <button class="faq-btn w-full px-6 py-4 flex justify-between items-center text-left hover:bg-white/5 transition-colors">
            <span class="font-semibold text-white">{q}</span>
            <i class="fas fa-plus text-purple-400"></i>
        </button>
        <div class="faq-answer hidden px-6 pb-4 text-gray-400">{a}</div>
    </div>'''
                    faqs_html += '\n</div>'
                    print(f"  ✅ Rendered {len(faqs)} FAQs from source array")
                else:
                    print(f"  ⚠️ FAQs array found but no items extracted")
            else:
                print(f"  ⚠️ No faqs array found in source")

        if faqs_html:
            # ⭐ CRITICAL FIX: Find and replace the ENTIRE FAQ section, not just the map block
            # Look for the FAQ section by its structure
            faq_section_pattern = r'(<section[^>]*class="[^"]*py-20[^"]*"[^>]*>.*?<h2[^>]*>FAQ.*?<div class="space-y-4">)[\s\S]*?(</div>\s*</div>\s*</section>)'
            faq_section_match = re.search(faq_section_pattern, content, re.DOTALL)
            
            if faq_section_match:
                # Replace the entire FAQ container content
                new_section = faq_section_match.group(1) + faqs_html + faq_section_match.group(2)
                content = content.replace(faq_section_match.group(0), new_section)
                print(f"  ✅ Replaced entire FAQ section with {faqs_html.count('faq-btn')} items")
            else:
                # Fallback: try to replace just the map block
                content = replace_map_block(content, 'faqs', faqs_html)
        else:
            # If no FAQ was generated, remove the entire FAQ section
            content = re.sub(r'<section\s+className="py-20 px-4">\s*<div\s+className="container mx-auto max-w-3xl">\s*<h2\s+className="text-4xl font-bold text-center mb-12">FAQ</h2>.*?</div>\s*</section>', '', content, flags=re.DOTALL)
            print(f"  ✅ Removed empty FAQ section (no content)")












    # ========== STEP 6: RESTORE TRUST INDICATORS ==========
    if saved_trust_html:
        content = content.replace("{{TRUST_INDICATORS_MARKER}}", saved_trust_html)
        print(f"  ✅ Restored trust indicators after array processing")

    # ========== STEP 5: CLEANUP ==========
    content = re.sub(r'(?:const|let)\s+features\s*=\s*\[[\s\S]*?\];?\s*', '', content, flags=re.DOTALL)
    content = re.sub(r'(?:const|let)\s+faqs\s*=\s*\[[\s\S]*?\];?\s*', '', content, flags=re.DOTALL)
    content = re.sub(r'(?:const|let)\s+faq\s*=\s*\[[\s\S]*?\];?\s*', '', content, flags=re.DOTALL)

    return content






def fix_shop_page_buttons(html_content: str) -> str:
    """Convert generic shop buttons to add-to-cart-btn with proper attributes"""
    
    import re
    
    # Pattern to find product cards
    product_card_pattern = r'<div[^>]*class="[^"]*bg-zinc-900[^"]*"[^>]*>.*?<h3[^>]*>(.*?)</h3>.*?<p[^>]*>\$?([\d.]+)</p>.*?<button[^>]*>(.*?)</button>'
    
    def fix_product_card(match):
        product_name = match.group(1).strip()
        product_price = match.group(2).strip()
        button_text = match.group(3).strip()
        
        # Clean price
        clean_price = re.sub(r'[^0-9.]', '', product_price)
        try:
            price_float = float(clean_price)
        except:
            price_float = 0
        
        # Generate product ID from name
        product_id = product_name.lower().replace(' ', '_')
        
        # Return fixed card with proper button
        return f'''
            <div class="bg-white/5 p-6 rounded-xl border border-white/10 hover:border-purple-500/50 transition-all group">
                <div class="w-full h-40 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-lg mb-4 flex items-center justify-center">
                    <i class="fas fa-gem text-5xl text-purple-400 group-hover:scale-110 transition-transform"></i>
                </div>
                <h3 class="text-xl font-bold text-white">{product_name}</h3>
                <p class="text-purple-400 text-2xl font-bold mt-2">${price_float:.2f}</p>
                <button class="add-to-cart-btn mt-4 w-full py-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg text-white font-semibold hover:opacity-90 transition" 
                        data-id="{product_id}" 
                        data-name="{product_name}" 
                        data-price="{price_float}">
                    <i class="fas fa-cart-plus mr-2"></i> Add to Cart
                </button>
            </div>
        '''
    
    # Apply fix to shop page only
    if 'id="page_shop"' in html_content:
        # Extract shop page section
        shop_match = re.search(r'(<div id="page_shop"[^>]*>)(.*?)(</div>)', html_content, re.DOTALL)
        if shop_match:
            shop_content = shop_match.group(2)
            # Fix all product cards
            fixed_shop_content = re.sub(product_card_pattern, fix_product_card, shop_content, flags=re.DOTALL)
            # Replace shop page with fixed version
            html_content = html_content.replace(shop_match.group(0), shop_match.group(1) + fixed_shop_content + shop_match.group(3))
            print("  ✅ Fixed shop page buttons - added add-to-cart-btn class and data attributes")
    
    return html_content





















def clean_html_response(text: str) -> str:
    """Aggressively clean HTML response from AI"""
    text = text.strip()
    
    # Remove markdown code blocks
    if text.startswith("```html"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    
    text = text.strip()
    
    # Remove any standalone "html" word at the beginning
    if text.lower().startswith("html"):
        text = text[4:].strip()
    elif text.lower().startswith("html\n"):
        text = text[5:].strip()
    elif text.lower().startswith("html\r\n"):
        text = text[6:].strip()
    
    # Unescape common characters
    text = text.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace("\\'", "'")
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Ensure it starts with proper HTML doctype
    if not text.startswith("<!DOCTYPE") and not text.lower().startswith("<html"):
        html_match = re.search(r'<!DOCTYPE\s+html[\s\S]*|<\s*html[\s\S]*', text, re.IGNORECASE)
        if html_match:
            text = html_match.group(0)
        else:
            # Fallback wrapper
            text = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scorpio Preview</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    {text}
</body>
</html>"""
    
    # Final cleanup of "html" artifacts
    text = re.sub(r'^\s*html\s*[\n\r]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*"html"\s*[\n\r]', '', text, flags=re.IGNORECASE)
    
    return text.strip()



















def enforce_body_background(html: str) -> str:
    """Force correct body background gradient - replace solid black with gradient"""
    
    # Replace solid black background with gradient
    # Pattern 1: background: #000;
    html = re.sub(
        r'body\s*\{\s*[^}]*background:\s*#000;?\s*[^}]*\}',
        '''body {
            font-family: 'Inter', system-ui, sans-serif;
            background: linear-gradient(135deg, #0f0f12 0%, #1a1a2e 100%);
            color: #e2e8f0;
            min-height: 100vh;
        }''',
        html,
        flags=re.DOTALL
    )
    
    # Pattern 2: background: #000000;
    html = re.sub(
        r'body\s*\{\s*[^}]*background:\s*#000000;?\s*[^}]*\}',
        '''body {
            font-family: 'Inter', system-ui, sans-serif;
            background: linear-gradient(135deg, #0f0f12 0%, #1a1a2e 100%);
            color: #e2e8f0;
            min-height: 100vh;
        }''',
        html,
        flags=re.DOTALL
    )
    
    # Pattern 3: bg-black class
    html = re.sub(
        r'<body\s+class="[^"]*bg-black[^"]*"',
        '<body',
        html
    )
    html = re.sub(
        r'<body\s+class="[^"]*bg-zinc-900[^"]*"',
        '<body',
        html
    )
    
    # Pattern 4: If no proper background exists, inject the style
    if 'linear-gradient(135deg, #0f0f12' not in html and 'from-purple-950' not in html:
        # Find the style tag and add body style
        style_match = re.search(r'(<style[^>]*>)(.*?)(</style>)', html, re.DOTALL)
        if style_match:
            body_style = '''
body {
    font-family: 'Inter', system-ui, sans-serif;
    background: linear-gradient(135deg, #0f0f12 0%, #1a1a2e 100%);
    color: #e2e8f0;
    min-height: 100vh;
}
'''
            new_css = style_match.group(1) + body_style + style_match.group(2) + style_match.group(3)
            html = html.replace(style_match.group(0), new_css)
    
    return html




























async def generate_preview_internal(
    files: Dict[str, Any],
    project_name: str,
    existing_image_url: str = None,
    user_prompt: str = "",
    project_type: str = "",
    
    model_router=None,           # ← add this
    get_cloudinary_url_for_preview=None  # ← add this
    
) -> Dict[str, Any]:
    
    
    # ✅ Initialize preview_result at the very beginning
    preview_result = None
    
    
    
    
    
    # ✅ CHECK IF HERO WAS REMOVED
    hero_removed = files.get("__hero_removed__") == "true"
    
    if hero_removed:
        print(f"🚫 Hero image was previously removed - skipping Cloudinary URL injection")
        existing_image_url = None
        # Also remove from files to be safe
        files.pop("__cloudinary_image_url__", None)
    
    
    
    
    
    
    
    
    # ✅ ADD THE PROJECT TYPE DETECTION CODE RIGHT HERE
    # ========== PROJECT TYPE DETECTION ==========
    project_type = ""  # Initialize
    
    # If project_type not provided, try to get from files
    if not project_type:
        project_type = files.get("__project_type__", "")
    
    # If still no project_type, detect from navigation and content
    if not project_type:
        nav_content = files.get("components/Navigation.tsx", "")
        homepage_content = files.get("app/page.tsx", "")
        all_content = nav_content + homepage_content
        
        # ========== CHECK FOR SAAS FIRST (MOST SPECIFIC) ==========
        saas_keywords = ['features', 'pricing', 'saas', 'platform', 'analytics', 'ai', 'cloud', 
                        'software', 'academy', 'learning', 'subscription', 'enterprise']
        if any(keyword in all_content.lower() for keyword in saas_keywords):
            project_type = "saas"
            print(f"📌 Detected SaaS project type from content")
        
        # ========== CHECK FOR DASHBOARD ==========
        elif any(keyword in all_content.lower() for keyword in ['dashboard', 'analytics', 'kpi', 'metrics', 'recharts']):
            project_type = "dashboard"
            print(f"📌 Detected Dashboard project type")
        
        # ========== CHECK FOR E-COMMERCE ==========
        elif "shop" in nav_content.lower() or "cart" in nav_content.lower() or "products" in all_content.lower():
            project_type = "ecommerce"
            print(f"📌 Detected E-commerce project type")
        
        # ========== CHECK FOR GYM/FITNESS ==========
        elif "classes" in nav_content.lower() or "trainers" in nav_content.lower() or "workout" in all_content.lower():
            project_type = "gym"
            print(f"📌 Detected Gym/Fitness project type")
        
        # ========== CHECK FOR RESTAURANT (LAST - LEAST SPECIFIC) ==========
        elif "menu" in nav_content.lower() or "reservations" in nav_content.lower() or "restaurant" in all_content.lower():
            project_type = "restaurant"
            print(f"📌 Detected Restaurant project type")
        
        # ========== CHECK FOR SCHOOL/EDUCATION ==========
        elif "programs" in nav_content.lower() or "admissions" in nav_content.lower() or "courses" in all_content.lower():
            project_type = "school"
            print(f"📌 Detected School/Education project type")
        
        # ========== DEFAULT ==========
        else:
            project_type = "general"
            print(f"📌 Using General project type")
    
    print(f"📌 Generating preview for project type: {project_type}")
    # ========== END PROJECT TYPE DETECTION ==========
    
    
    
    
    
    
    
    
    
    
    
    # ========== BRAND STYLING CONFIGURATION ==========
    BRAND_ICON_COLOR = "#d8a219"  # Golden color
    BRAND_ICON_TAILWIND = "text-amber-500"
    BRAND_NAME_COLOR = "text-white"
    BRAND_NAME_SIZE = "text-xl font-bold"
    # ================================================ 
    
    
    
    
    
    
    
    
    
    
    
    
    import re  # ⭐ ADD THIS LINE - MUST BE FIRST
    """Generate beautiful HTML preview - extracts ALL pages and footer content"""
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
      # ========== ADD THIS HELPER FUNCTION HERE ==========
    def inject_cart_icon_into_html(html_content: str, user_prompt: str = "") -> str:
        """Force inject cart icon into navigation only for e-commerce websites"""
        
        # ========== CHECK IF THIS IS E-COMMERCE ==========
        is_ecommerce = False
        
        # Check HTML for shop page (not just cart)
        has_shop_div = 'id="page_shop"' in html_content or 'data-page="shop"' in html_content
        has_cart_div = 'id="page_cart"' in html_content or 'data-page="cart"' in html_content
        
        if has_shop_div and has_cart_div:
            is_ecommerce = True
            print("🛒 E-commerce detected: Shop and Cart divs found")
        
        # Check user prompt for gym keywords (skip injection)
        if user_prompt:
            gym_keywords = ['gym', 'fitness', 'workout', 'trainer', 'classes', 'membership', 'yoga', 'hiit', 'pilates']
            if any(keyword in user_prompt.lower() for keyword in gym_keywords):
                print("🚫 Gym/Fitness website detected - skipping cart icon injection")
                return html_content
        
        # If not e-commerce, return unchanged
        if not is_ecommerce:
            print("🚫 Not an e-commerce website - skipping cart icon injection")
            return html_content
        
        print("✅ E-commerce confirmed - injecting cart icon")
        
        # Pattern to find the cart link
        cart_link_pattern = r'<a[^>]*data-page="cart"[^>]*>(.*?)</a>'
        
        def fix_cart_link(match):
            cart_html = match.group(0)
            
            # Check if icon already exists
            if 'data-lucide="shopping-cart"' in cart_html:
                return cart_html  # Already has icon, leave it
            
            # Check if it has href="cart"
            if 'href="cart"' not in cart_html:
                cart_html = cart_html.replace('href="#"', 'href="cart"')
            
            # Check if it has flex classes
            if 'flex' not in cart_html and 'items-center' not in cart_html:
                if 'class="' in cart_html:
                    cart_html = cart_html.replace('class="', 'class="flex items-center gap-2 group ')
                else:
                    cart_html = cart_html.replace('<a ', '<a class="flex items-center gap-2 group" ')
            
            # Extract the text content (usually "Cart")
            text_match = re.search(r'>\s*(Cart|cart|CART)\s*<', cart_html, re.IGNORECASE)
            cart_text = text_match.group(1) if text_match else "Cart"
            
            # Extract badge if exists
            badge_match = re.search(r'<span[^>]*data-cart-count[^>]*>.*?</span>', cart_html, re.DOTALL)
            badge_html = badge_match.group(0) if badge_match else '<span data-cart-count class="cart-count-badge hidden absolute -top-2 -right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full items-center justify-center px-1 shadow-lg shadow-purple-500/25">0</span>'
            
            # Build the corrected cart link
            corrected_link = f'''<a href="cart" class="nav-link relative flex items-center gap-2 group" data-page="cart">
                <i data-lucide="shopping-cart" class="w-4 h-4 text-purple-400"></i>
                <span class="text-gray-300 group-hover:text-purple-400">{cart_text}</span>
                {badge_html}
            </a>'''
            
            return corrected_link
        
        # Apply the fix
        fixed_html = re.sub(cart_link_pattern, fix_cart_link, html_content, flags=re.DOTALL)
        return fixed_html
  
  
  
  
  
    
    
    
    try:
        print(f"🤖 AI generating beautiful HTML preview for: {project_name}")




























        # ========== ADD FONT AWESOME CDN TO HEAD ==========
        font_awesome_cdn = '''
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
        '''
        
        
        
          # ========== FUNCTION TO CONVERT FOOTER TO FONT AWESOME ==========
        def convert_footer_to_fontawesome(footer_html: str) -> str:
            """Convert Lucide icons in footer to Font Awesome icons"""
            if not footer_html:
                return footer_html
            
            # Map React/Lucide icon names to Font Awesome classes
            icon_map = {
                'Instagram': 'fab fa-instagram',
                'Facebook': 'fab fa-facebook',
                'Twitter': 'fab fa-twitter',
                'Mail': 'fas fa-envelope',
                'Phone': 'fas fa-phone',
                'MapPin': 'fas fa-map-marker-alt',
                'Send': 'fas fa-paper-plane',
                'Heart': 'fas fa-heart',
                'Sparkles': 'fas fa-sparkles',
            }
            
            # Replace <IconName /> with Font Awesome <i>
            for react_icon, fa_class in icon_map.items():
                # Handle <IconName /> pattern
                footer_html = re.sub(
                    rf'<{react_icon}\s*/>',
                    f'<i class="{fa_class} text-purple-400"></i>',
                    footer_html
                )
                # Handle <IconName></IconName> pattern
                footer_html = re.sub(
                    rf'<{react_icon}>\s*</{react_icon}>',
                    f'<i class="{fa_class} text-purple-400"></i>',
                    footer_html
                )
                # Handle <IconName className="..." />
                footer_html = re.sub(
                    rf'<{react_icon}\s+className="([^"]*)"\s*/>',
                    lambda m: f'<i class="{fa_class} {m.group(1)} text-purple-400"></i>',
                    footer_html
                )
            
            return footer_html









        def convert_navigation_to_html(nav_content: str, brand_name: str, nav_links: list) -> str:
            """Convert Next.js Navigation component to HTML with Lucide icons - with cart badge support"""
            
            # ========== DYNAMIC ICON EXTRACTION ==========
            icon_name = "Sparkles"  # default
            icon_size = "w-8 h-8"
            icon_color = "text-purple-500"
            
            # Method 1: Extract from JSX with any className pattern
            jsx_pattern = r'<(\w+)\s+className="([^"]*)"'
            jsx_matches = re.findall(jsx_pattern, nav_content)
            for match in jsx_matches:
                potential_icon = match[0]
                class_str = match[1]
                # Check if it's likely an icon (not a div or span)
                if potential_icon[0].isupper() and len(potential_icon) > 1:
                    icon_name = potential_icon
                    # Extract size from className
                    size_match = re.search(r'w-(\d+)\s+h-(\d+)', class_str)
                    if size_match:
                        icon_size = f"w-{size_match.group(1)} h-{size_match.group(2)}"
                    # Extract color from className
                    color_match = re.search(r'text-(\w+-\d+)', class_str)
                    if color_match:
                        icon_color = f"text-{color_match.group(1)}"
                    break
            
            # Method 2: Extract from imports if JSX extraction failed
            if icon_name == "Sparkles":
                import_match = re.search(r'import\s+\{\s*(\w+)\s*\}\s+from\s+[\'"]lucide-react[\'"]', nav_content)
                if import_match:
                    icon_name = import_match.group(1)
            
            print(f"🎨 Extracted icon: {icon_name}")
            print(f"   Size: {icon_size}")
            print(f"   Color: {icon_color}")
            
            # Map icon name to Lucide data-lucide attribute
            lucide_icon = icon_name.lower()
            special_mappings = {
                "graduationcap": "graduation-cap",
                "shoppingbag": "shopping-bag",
                "shoppingcart": "shopping-cart",
                "sparkles": "sparkles",
                "dumbbell": "dumbbell",
            }
            lucide_icon = special_mappings.get(lucide_icon, lucide_icon)
            
            # Extract brand text gradient className
            brand_text_class = "text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent"
            text_match = re.search(r'<span[^>]*className="([^"]*)"[^>]*>[^<]*</span>', nav_content)
            if text_match:
                brand_text_class = text_match.group(1)
            
            # ========== CHECK IF CART EXISTS IN NAV_LINKS ==========
            has_cart = any('cart' in label.lower() or href == '/cart' for href, label in nav_links)
            
            # ========== BUILD NAVIGATION BUTTONS ==========
            nav_buttons_html = ""
            cart_link_html = ""
            mobile_nav_html = ""
            mobile_cart_html = ""
            
            print(f"📋 Building navigation for {len(nav_links)} links: {nav_links}")
            print(f"   Has cart: {has_cart}")
            
            # E-commerce keywords that should have icons
            ECOMMERCE_KEYWORDS = ["shop", "store", "catalog", "catalogue", "cart", "basket", "products", "checkout"]
            
            for href, label in nav_links:
                label_lower = label.lower()
                
                # Check if this is the CART link (special handling for badge)
                is_cart = 'cart' in label_lower or href == '/cart'
                
                # Check if this is an e-commerce link (should have icon)
                is_ecommerce = any(keyword in label_lower for keyword in ECOMMERCE_KEYWORDS)
                
                if is_cart:
                    # Special cart link WITH badge
                    item_icon = "shopping-cart"
                    base_color = icon_color.replace('500', '400') if '500' in icon_color else icon_color
                    hover_color = icon_color.replace('500', '600') if '500' in icon_color else icon_color
                    
                    cart_link_html = f'''
                        <a href="{href}" class="nav-link relative flex items-center gap-2 group" data-page="{href.replace('/', '')}">
                            <i data-lucide="{item_icon}" class="w-4 h-4 {base_color} group-hover:{hover_color} group-hover:scale-110 transition-all duration-300"></i>
                            <span class="text-gray-300 group-hover:{icon_color} transition-colors duration-300">{label}</span>
                            <span data-cart-count class="cart-count-badge hidden absolute -top-2 -right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full items-center justify-center px-1 shadow-lg shadow-purple-500/25">0</span>
                        </a>'''
                    
                    # Mobile cart link
                    mobile_cart_html = f'''
                        <div class="flex items-center justify-between w-full px-4 py-2 rounded-lg hover:bg-white/10">
                            <a href="{href}" class="mobile-nav-link flex items-center gap-3" data-page="{href.replace('/', '')}">
                                <i data-lucide="{item_icon}" class="w-4 h-4 {icon_color}"></i>
                                <span class="text-gray-300">{label}</span>
                            </a>
                            <span data-cart-count class="cart-count-badge hidden bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full items-center justify-center px-1">0</span>
                        </div>'''
                elif is_ecommerce:
                    # Regular e-commerce link WITH icon (no badge)
                    if "shop" in label_lower or "store" in label_lower:
                        item_icon = "shopping-bag"
                    elif "catalog" in label_lower or "catalogue" in label_lower:
                        item_icon = "grid"
                    elif "products" in label_lower:
                        item_icon = "package"
                    elif "checkout" in label_lower:
                        item_icon = "credit-card"
                    else:
                        item_icon = "circle"
                    
                    base_color = icon_color.replace('500', '400') if '500' in icon_color else icon_color
                    hover_color = icon_color.replace('500', '600') if '500' in icon_color else icon_color
                    
                    nav_buttons_html += f'''
                        <a href="{href}" class="nav-link flex items-center gap-2 group" data-page="{href.replace('/', '')}">
                            <i data-lucide="{item_icon}" class="w-4 h-4 {base_color} group-hover:{hover_color} group-hover:scale-110 transition-all duration-300"></i>
                            <span class="text-gray-300 group-hover:{icon_color} transition-colors duration-300">{label}</span>
                        </a>'''
                    
                    # Mobile version
                    mobile_nav_html += f'''
                        <a href="{href}" class="mobile-nav-link flex items-center gap-3 w-full px-4 py-2 rounded-lg hover:bg-white/10" data-page="{href.replace('/', '')}">
                            <i data-lucide="{item_icon}" class="w-4 h-4 {icon_color}"></i>
                            <span class="text-gray-300">{label}</span>
                        </a>'''
                else:
                    # Build non-e-commerce link WITHOUT icon (text only)
                    nav_buttons_html += f'''
                        <a href="{href}" class="nav-link group" data-page="{href.replace('/', '')}">
                            <span class="text-gray-300 group-hover:{icon_color} transition-colors duration-300">{label}</span>
                        </a>'''
                    
                    # Mobile version
                    mobile_nav_html += f'''
                        <a href="{href}" class="mobile-nav-link block w-full px-4 py-2 rounded-lg hover:bg-white/10" data-page="{href.replace('/', '')}">
                            <span class="text-gray-300">{label}</span>
                        </a>'''
            
            # ========== GENERATE FINAL NAVIGATION HTML ==========
            # Only include cart elements if cart exists
            cart_desktop_html = cart_link_html if has_cart else ""
            cart_mobile_html = mobile_cart_html if has_cart else ""
            
            return f'''
            <nav class="flex justify-between items-center p-6 container mx-auto sticky top-0 z-50 bg-black/80 backdrop-blur-lg border-b border-white/10">
                <a href="#" class="brand flex items-center gap-2 group" onclick="handleBrandClick(event); return false;">
                    <i data-lucide="{lucide_icon}" class="w-8 h-8" style="color: #d8a219;"></i>
                    <span class="text-white text-xl font-bold">{brand_name}</span>
                </a>
                <div class="hidden md:flex space-x-2 items-center">
                    {navigation_html}
                    {cart_desktop_html}
                </div>
                <button id="mobile-menu-button" class="md:hidden p-2 rounded-lg hover:bg-white/10 transition-colors">
                    <i data-lucide="menu" class="w-6 h-6" style="color: #d8a219;"></i>
                </button>
            </nav>

            <div id="mobile-menu" class="hidden md:hidden bg-black/80 backdrop-blur-lg p-4 space-y-2 border-t border-white/10">
                {navigation_html}
                {cart_mobile_html}
            </div>

            <style>
                /* Cart Badge Animation */
                .cart-count-badge {{
                    animation: bounceIn 0.3s ease-out;
                }}
                @keyframes bounceIn {{
                    0% {{ transform: scale(0); opacity: 0; }}
                    50% {{ transform: scale(1.2); }}
                    100% {{ transform: scale(1); opacity: 1; }}
                }}
            </style>

            <script>
                document.getElementById('mobile-menu-button')?.addEventListener('click', function() {{
                    const menu = document.getElementById('mobile-menu');
                    if (menu) menu.classList.toggle('hidden');
                }});
                lucide.createIcons();
            </script>
            '''
                    
                    
                    











        def clean_onError_handlers(html: str) -> str:
            """Convert string onError handlers to actual JavaScript"""
            import re
            
            # Count how many fixes were made
            fixes_count = 0
            
            # ⭐ NEW: Fix broken onError that appears as text with double braces
            # Pattern: onError="{{ (e) => { ... } }}" 
            pattern0 = r'onError="\{\{\s*\(e\)\s*=>\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}\s*\}\}"'
            html, count = re.subn(pattern0, r'onError={(e) => { \1 }}', html)
            fixes_count += count
            
            # Fix pattern with optional chaining and double braces
            pattern0b = r'onError="\{\{\s*\(e\)\s*=>\s*\{([^}]+?\.parentElement\?\.classList[^}]+)\}\s*\}\}"'
            html, count = re.subn(pattern0b, r'onError={(e) => { \1 }}', html)
            fixes_count += count
            
            # Fix pattern: onError="{(e) => { ... }}"
            pattern = r'onError="\{\(e\)\s*=>\s*\{([^}]+)\}\}"'
            html, count = re.subn(pattern, r'onError={(e) => { \1 }}', html)
            fixes_count += count
            
            # Fix any onError with quotes
            pattern2 = r'onError="([^"]+)"'
            def fix_handler(match):
                handler = match.group(1)
                handler = handler.strip()
                if handler.startswith('{') and handler.endswith('}'):
                    handler = handler[1:-1]
                return f'onError={{{handler}}}'
            html, count = re.subn(pattern2, fix_handler, html)
            fixes_count += count
            
            # Fix escaped characters
            html = html.replace('&quot;', '"')
            html = html.replace('&#39;', "'")
            html = html.replace('&#123;', '{')
            html = html.replace('&#125;', '}')
            
            # Fix double braces
            html, count = re.subn(r'onError=\{\{(.+?)\}\}', r'onError={\1}', html)
            fixes_count += count
            
            # ⭐ NEW: Remove any remaining broken onError that might render as text
            html = re.sub(
                r'onError="[^"]*parentElement\?\.classList[^"]*"\s*/>',
                'onError={(e) => { e.currentTarget.style.display = "none"; }} />',
                html
            )
            
            if fixes_count > 0:
                print(f"🔧 Fixed {fixes_count} onError handler(s) in preview HTML")
            
            return html















        # ========== COLLECT NAVIGATION ==========
        nav_links = []
        nav_content = ""
        brand_name = project_name
        
        # Initialize dashboard detection EARLY
        detected_as_dashboard = False
        if user_prompt:
            dashboard_keywords = ['dashboard', 'analytics', 'kpi', 'metrics', 'overview', 'reports', 'monitoring']
            detected_as_dashboard = any(keyword in user_prompt.lower() for keyword in dashboard_keywords)
        
        # Check page.tsx content for dashboard indicators
        if not detected_as_dashboard:
            homepage_content = files.get("app/page.tsx", "")
            if 'kpiData' in homepage_content or 'recharts' in homepage_content:
                detected_as_dashboard = True
        
        nav_paths = [
            "components/Navigation.tsx",
            "components/Navigation.jsx", 
            "components/Navbar.tsx",
            "components/Navbar.jsx",
            "app/components/Navigation.tsx",
            "components/Header.tsx"
        ]
        
        for fp in nav_paths:
            if fp in files:
                nav_content = files[fp]
                break
        
        if not nav_content:
            for fp, content in files.items():
                if any(x in fp for x in ["Navigation", "Navbar", "Header"]) and fp.endswith((".tsx", ".jsx")):
                    nav_content = content
                    break
        
        # ========== EXTRACT BRAND AND NAVIGATION LINKS ==========
        print(f"🔍 DEBUG - nav_content length: {len(nav_content) if nav_content else 0}")
        print(f"🔍 DEBUG - nav_content preview: {nav_content[:500] if nav_content else 'EMPTY'}")
        
        if nav_content:
            # Extract brand name
            brand_patterns = [
                r'<Link\s+href="/"[^>]*>(.*?)</Link>',
                r'<div\s+className="[^"]*brand[^"]*"[^>]*>(.*?)</div>',
                r'<span\s+className="[^"]*text-xl[^"]*font-bold[^"]*"[^>]*>(.*?)</span>',
                r'<span\s+className="[^"]*font-bold[^"]*"[^>]*>([^<]+)</span>',
            ]
            for pattern in brand_patterns:
                match = re.search(pattern, nav_content, re.DOTALL)
                if match:
                    brand_name = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                    if brand_name:
                        break
            
            # ========== IMPROVED LINK EXTRACTION FOR RESTAURANT NAVIGATION ==========
            # Pattern 1: Direct Link components with href (works for <Link href="/menu">Menu</Link>)
            link_patterns = [
                r'<Link\s+href="/([^"]+)"[^>]*>([^<]+)</Link>',
                r'<Link\s+href=\'/([^\']+)\'[^>]*>([^<]+)</Link>',
                r'href="/([^"]+)".*?>([^<]+)</Link>',
            ]
            
            for pattern in link_patterns:
                matches = re.findall(pattern, nav_content, re.DOTALL)
                for href, label in matches:
                    clean_label = re.sub(r'<[^>]+>', '', label).strip()
                    if href and clean_label and href not in ['', '/']:
                        # Skip brand/home links
                        if clean_label.lower() != brand_name.lower() and clean_label.lower() != 'home':
                            nav_links.append((href, clean_label))
                if nav_links:
                    break
            
            # Pattern 2: Look for the hidden md:flex div structure (your Navigation component)
            if not nav_links:
                # Find the div with hidden md:flex class
                flex_pattern = r'<div\s+className="hidden md:flex[^"]*"[^>]*>(.*?)</div>'
                flex_match = re.search(flex_pattern, nav_content, re.DOTALL)
                if flex_match:
                    links_html = flex_match.group(1)
                    # Extract all Link components inside
                    inner_matches = re.findall(r'<Link\s+href="/([^"]+)"[^>]*>([^<]+)</Link>', links_html)
                    for href, label in inner_matches:
                        nav_links.append((href, label.strip()))
            
            # Pattern 3: Look for any Link with href that's not the brand
            if not nav_links:
                all_links = re.findall(r'<Link\s+href="/([^"]+)"[^>]*>', nav_content)
                for href in all_links:
                    if href not in ['', '/'] and href.lower() != brand_name.lower():
                        # Try to find the label
                        label_pattern = rf'<Link\s+href="/{href}"[^>]*>([^<]+)</Link>'
                        label_match = re.search(label_pattern, nav_content)
                        if label_match:
                            label = label_match.group(1).strip()
                        else:
                            label = href.capitalize()
                        nav_links.append((href, label))
        
        # ========== FALLBACK: Use restaurant defaults if no links found and it's a restaurant ==========
        if not nav_links:
            # Check if this is a restaurant website (based on file names or user prompt)
            is_restaurant = False
            for file_path in files.keys():
                if any(keyword in file_path.lower() for keyword in ['menu', 'reservation', 'restaurant', 'gallery']):
                    is_restaurant = True
                    break
            
            if 'restaurant' in user_prompt.lower() or 'cafe' in user_prompt.lower() or 'dining' in user_prompt.lower():
                is_restaurant = True
            
            if is_restaurant:
                nav_links = [("menu", "Menu"), ("reservations", "Reservations"), ("gallery", "Gallery")]
                print(f"📍 Using restaurant default nav_links: {nav_links}")
            elif detected_as_dashboard:
                nav_links = [("analytics", "Analytics"), ("settings", "Settings")]
                print(f"📍 Using dashboard default nav_links: {nav_links}")
                
                
                
                
                
                
                
                
                
                
                
            else:
                nav_links = [("shop", "Shop"), ("cart", "Cart")]
                print("🔍 Using e-commerce default nav_links")
                
                
                
                
                
                
                

        print(f"📍 Navigation: {brand_name} -> {nav_links}")
        
        
        # Generate navigation HTML using the function
        navigation_html = generate_navigation_html(brand_name, nav_links)
        print(f"✅ Generated navigation HTML with {len(nav_links)} links")
        
        # ========== CONVERT NAVIGATION TO HTML ==========
        navigation_html = convert_navigation_to_html(nav_content, brand_name, nav_links)
        navigation_html_for_prompt = navigation_html










        
        # ========== EXTRACT FOOTER CONTENT ==========
        footer_html = ""
        footer_paths = [
            "components/Footer.tsx",
            "components/Footer.jsx",
            "app/components/Footer.tsx",
        ]
        
        for fp in footer_paths:
            if fp in files:
                footer_content = files[fp]
                # Extract the JSX return content
                match = re.search(r'return\s*\(\s*([\s\S]*?)\s*\)\s*;', footer_content)
                if match:
                    footer_html = match.group(1)
                else:
                    footer_html = footer_content
                
                # Convert JSX to HTML
                footer_html = re.sub(r'className=', 'class=', footer_html)
                footer_html = re.sub(r'<Link\s+href="([^"]+)"[^>]*>', r'<a href="\1">', footer_html)
                footer_html = re.sub(r'</Link>', '</a>', footer_html)
                
                # Convert icons to Font Awesome
                footer_html = convert_footer_to_fontawesome(footer_html)
                print(f"✅ Footer extracted and converted to Font Awesome")
                break
        
        # If no footer found, use default
        if not footer_html:
            from datetime import datetime
            footer_html = f'''
            <footer class="bg-zinc-950 border-t border-zinc-800 py-12">
                <div class="container mx-auto grid md:grid-cols-4 gap-8 px-4">
                    <div>
                        <h4 class="font-bold mb-4">{brand_name}</h4>
                        <p class="text-sm text-gray-400">Premium lifestyle goods.</p>
                    </div>
                    <div>
                        <h4 class="font-bold mb-4">Links</h4>
                        <p class="text-sm text-gray-400">Shop | Catalog | Cart</p>
                    </div>
                    <div>
                        <h4 class="font-bold mb-4">Contact</h4>
                        <p class="text-sm text-gray-400">info@{brand_name.lower().replace(' ', '')}.com</p>
                    </div>
                    <div class="flex gap-4">
                        <i class="fab fa-instagram text-gray-400 hover:text-purple-400"></i>
                        <i class="fab fa-facebook text-gray-400 hover:text-purple-400"></i>
                        <i class="fab fa-twitter text-gray-400 hover:text-purple-400"></i>
                    </div>
                </div>
                <div class="text-center mt-8 text-sm text-gray-600">
                    © {datetime.now().year} {brand_name}. Crafted by Eaglecode
                </div>
            </footer>
            '''
        
        # ========== INCLUDE FONT AWESOME CDN IN PREVIEW ==========
        # Make sure to add this to your final preview HTML <head> section
        font_awesome_cdn = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">'
        
        # Continue with the rest of your preview generation...
        # Make sure to add {font_awesome_cdn} to your <head> section






















        # ========== EXTRACT FOOTER CONTENT ==========
        footer_html = ""
        footer_paths = [
            "components/Footer.tsx",
            "components/Footer.jsx",
            "app/components/Footer.tsx",
            "components/Footer/index.tsx",
            "components/Layout/Footer.tsx"
        ]
        
        for fp in footer_paths:
            if fp in files:
                content = files[fp]
                # Remove 'use client' and imports first
                clean_footer = re.sub(r'^["\']use client["\'];\s*$', '', content, flags=re.MULTILINE)
                clean_footer = re.sub(r'^import\s+.*?from\s+["\'][^"\']+["\'];\s*$', '', clean_footer, flags=re.MULTILINE)
                
                # Extract JSX return content
                match = re.search(r'return\s*\(\s*([\s\S]*?)\s*\)\s*;', clean_footer, re.DOTALL)
                if match:
                    footer_html = match.group(1)
                else:
                    match = re.search(r'<footer[\s\S]*?</footer>', content, re.DOTALL)
                    if match:
                        footer_html = match.group(0)
                
                if footer_html:
                    # Clean up footer HTML (preserve content)
                    footer_html = re.sub(r'className=', 'class=', footer_html)
                    footer_html = re.sub(r'<Link\s+href="([^"]+)"[^>]*>', r'<a href="\1">', footer_html)
                    footer_html = re.sub(r'</Link>', '</a>', footer_html)
                    footer_html = re.sub(r'\s+key=["\'][^"\']*["\']', '', footer_html)
                    # Don't remove curly braces in footer
                    # footer_html = re.sub(r'\{[^}]+\}', '', footer_html)  # COMMENTED OUT
                    print(f"✅ Footer extracted: {len(footer_html)} chars")
                    break
        
        
        
        
        
        
        
        
        
        
         # ========== DETECT PROJECT TYPE (EARLY) ==========
        is_dashboard_detected = False
        is_restaurant_detected = False
        
        if user_prompt:
            dashboard_keywords = ['dashboard', 'analytics', 'kpi', 'metrics', 'overview', 'reports', 'monitoring']
            is_dashboard_detected = any(keyword in user_prompt.lower() for keyword in dashboard_keywords)
            
            restaurant_keywords = ['restaurant', 'cafe', 'dining', 'menu', 'culinary', 'bistro', 'food', 'eatery', 'grill', 'kitchen', 'chef', 'reservation', 'booking']
            is_restaurant_detected = any(keyword in user_prompt.lower() for keyword in restaurant_keywords)
        
        # Also check file names for restaurant indicators
        if not is_restaurant_detected:
            for file_path in files.keys():
                if any(keyword in file_path.lower() for keyword in ['menu', 'reservation', 'restaurant', 'gallery']):
                    is_restaurant_detected = True
                    break
        
        print(f"\n{'='*60}")
        print(f"🏷️ PROJECT TYPE DETECTION")
        print(f"{'='*60}")
        print(f"   Dashboard: {'✅ YES' if is_dashboard_detected else '❌ NO'}")
        print(f"   Restaurant: {'✅ YES' if is_restaurant_detected else '❌ NO'}")
        print(f"{'='*60}\n")



        
        
        
        
        
        
        
        # ========== EXTRACT ALL PAGE CONTENTS ==========
        page_contents = {}
        
        
        
        








        def render_arrays_from_source(extracted: str, content: str) -> str:
            """Render JavaScript arrays from source into HTML - handles filtered arrays and nested menu items"""
            
            
            
            
            
            
            
            
            
            # ========== HANDLE PROJECTS ARRAY (for portfolio/agency sites) ==========
            projects_pattern = r'(?:const|let)\s+projects\s*=\s*\[\s*((?:[^\[\]]*?\{[^}]*\}[^\[\]]*?)*?)\s*\]'
            projects_match = re.search(projects_pattern, content, re.DOTALL)
            
            if projects_match and 'projects' in extracted.lower():
                print("   📁 Rendering projects array from source...")
                projects_content = projects_match.group(1)
                
                # Extract projects - match title/name and desc/description
                project_pattern = r'\{\s*(?:title|name):\s*["\']([^"\']+)["\']\s*,\s*(?:desc|description):\s*["\']([^"\']+)["\']'
                projects = re.findall(project_pattern, projects_content)
                
                if projects:
                    projects_html = '<div class="grid md:grid-cols-3 gap-8">\n'
                    for title, desc in projects:
                        projects_html += f'''
            <div class="bg-white/5 p-6 rounded-2xl border border-white/10 hover:border-purple-500/50 transition-all">
                <h3 class="text-xl font-bold mb-2">{title}</h3>
                <p class="text-gray-400">{desc}</p>
            </div>'''
                    projects_html += '\n        </div>'
                    print(f"   ✅ Rendered {len(projects)} projects from source array")
                    
                    # Replace the projects map block
                    projects_map_pattern = r'\{projects\.map\(\([^)]+\)\s*=>\s*\(?\s*<div[^>]*>[\s\S]*?</div>\s*\)?\s*\}'
                    extracted = re.sub(projects_map_pattern, projects_html, extracted, flags=re.DOTALL)
        
            
            
            
            
            
            
            
            
            
            
            
            
            # ========== SPECIAL HANDLING FOR MENU ITEMS (nested structure) ==========
            menu_pattern = r'(?:const|let)\s+menuItems\s*=\s*\[\s*((?:[^\[\]]*?\{[^}]*\}[^\[\]]*?)*?)\s*\]'
            menu_match = re.search(menu_pattern, content, re.DOTALL)
            
            if menu_match and 'menu' in extracted.lower():
                print("   🍽️ Rendering nested menu items from source...")
                menu_content = menu_match.group(1)
                
                # Find categories and their nested items
                category_pattern = r'\{\s*category:\s*["\']([^"\']+)["\']\s*,\s*items:\s*\[\s*((?:[^\[\]]*?\{[^}]*\}[^\[\]]*?)*?)\s*\]\s*\}'
                categories = re.findall(category_pattern, menu_content, re.DOTALL)
                
                if categories:
                    full_menu_html = ''
                    
                    for category_name, items_str in categories:
                        # Extract individual items from the category
                        item_pattern = r'\{\s*id:\s*(\d+)\s*,\s*name:\s*["\']([^"\']+)["\']\s*,\s*description:\s*["\']([^"\']+)["\']\s*,\s*price:\s*["\']([^"\']+)["\']\s*,\s*dietary:\s*\[(.*?)\]\s*\}'
                        items = re.findall(item_pattern, items_str, re.DOTALL)
                        
                        if items:
                            category_html = f'''
                            <div class="mb-16">
                                <h2 class="text-3xl font-bold mb-8 text-center gradient-text">{category_name}</h2>
                                <div class="grid md:grid-cols-2 gap-8">
                            '''
                            
                            for item_id, name, desc, price, dietary_str in items:
                                # Parse dietary restrictions
                                dietary_items = re.findall(r'["\']([^"\']+)["\']', dietary_str)
                                dietary_badges = ''
                                for diet in dietary_items:
                                    if diet == 'GF':
                                        dietary_badges += '<span class="text-xs px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 ml-2">Gluten-Free</span>'
                                    elif diet == 'V':
                                        dietary_badges += '<span class="text-xs px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400 ml-2">Vegetarian</span>'
                                    elif diet == 'VG':
                                        dietary_badges += '<span class="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 ml-2">Vegan</span>'
                                
                                category_html += f'''
                                    <div class="flex items-start gap-4 p-4 rounded-xl bg-white/5 border border-white/10 hover:border-orange-500/50 transition-all">
                                        <div class="w-20 h-20 bg-gradient-to-br from-orange-500/20 to-amber-500/20 rounded-xl flex items-center justify-center shrink-0">
                                            <i class="fas fa-utensils text-2xl text-orange-400"></i>
                                        </div>
                                        <div class="flex-1">
                                            <div class="flex justify-between items-start mb-1">
                                                <h3 class="text-xl font-bold text-white">{name}</h3>
                                                <span class="text-orange-400 font-semibold">{price}</span>
                                            </div>
                                            <p class="text-gray-400 text-sm mb-2">{desc}</p>
                                            <div class="flex gap-2">{dietary_badges}</div>
                                        </div>
                                    </div>
                                '''
                            
                            category_html += '''
                                </div>
                            </div>
                            '''
                            full_menu_html += category_html
                            print(f"      ✅ Rendered {len(items)} items for {category_name}")
                    
                    if full_menu_html:
                        # Find and replace the menu section
                        menu_section_pattern = r'(<div\s+class="[^"]*space-y-16[^"]*">)([\s\S]*?)(</div>)'
                        if re.search(menu_section_pattern, extracted, re.DOTALL):
                            extracted = re.sub(menu_section_pattern, r'\1' + full_menu_html + r'\3', extracted, flags=re.DOTALL)
                        else:
                            # Try alternative pattern for menu container
                            alt_pattern = r'(<div\s+class="[^"]*grid[^"]*">)([\s\S]*?)(</div>)'
                            extracted = re.sub(alt_pattern, r'\1' + full_menu_html + r'\3', extracted, flags=re.DOTALL)
                        print(f"   ✅ Replaced menu section with full HTML")
            
            # ========== REGULAR ARRAY HANDLING FOR OTHER ARRAYS ==========
            # Pattern for const arrayName = [...] at top level
            array_def_pattern = r'const\s+(\w+)\s*=\s*\[\s*((?:[^\[\]]*?\{[^}]*\}[^\[\]]*?)*?)\s*\]'
            
            for match in re.finditer(array_def_pattern, content, re.DOTALL):
                array_name = match.group(1)
                array_content = match.group(2)
                
                # Skip menuItems since we already handled it
                if array_name == 'menuItems':
                    continue
                
                # Extract items from the array
                items = []
                
                # More flexible pattern for class objects
                class_pattern = r'\{\s*id:\s*(\d+)\s*,\s*name:\s*["\']([^"\']+)["\']\s*,\s*description:\s*["\']([^"\']+)["\']\s*,\s*instructor:\s*["\']([^"\']+)["\']\s*,\s*time:\s*["\']([^"\']+)["\']\s*,\s*duration:\s*["\']([^"\']+)["\']\s*,\s*level:\s*["\']([^"\']+)["\']'
                
                item_matches = re.findall(class_pattern, array_content)
                
                for m in item_matches:
                    items.append({
                        'id': m[0],
                        'name': m[1],
                        'description': m[2],
                        'instructor': m[3],
                        'time': m[4],
                        'duration': m[5],
                        'level': m[6]
                    })
                
                if not items:
                    # Try simpler pattern for feature cards
                    feature_pattern = r'\{\s*title:\s*["\']([^"\']+)["\']\s*,\s*desc:\s*["\']([^"\']+)["\']\s*\}'
                    feature_matches = re.findall(feature_pattern, array_content)
                    for title, desc in feature_matches:
                        items.append({'title': title, 'desc': desc})
                
                if items:
                    # Look for BOTH direct map and filtered map
                    map_patterns = [
                        rf'{array_name}\.map\(\([^)]+\)\s*=>\s*\(\s*([\s\S]*?)\s*\)\s*\)',  # classes.map
                        rf'filtered{array_name.capitalize()}s?\.map\(\([^)]+\)\s*=>\s*\(\s*([\s\S]*?)\s*\)\s*\)',  # filteredClasses.map
                        rf'{array_name}\.filter\([^)]+\)\.map\(\([^)]+\)\s*=>\s*\(\s*([\s\S]*?)\s*\)\s*\)',  # classes.filter().map
                    ]
                    
                    template = None
                    for pattern in map_patterns:
                        map_match = re.search(pattern, extracted, re.DOTALL)
                        if map_match:
                            template = map_match.group(1)
                            break
                    
                    if template:
                        rendered_items = []
                        for item in items:
                            rendered = template
                            if 'cls.name' in rendered:
                                rendered = rendered.replace('{cls.name}', item.get('name', ''))
                                rendered = rendered.replace('{cls.description}', item.get('description', ''))
                                rendered = rendered.replace('{cls.instructor}', item.get('instructor', ''))
                                rendered = rendered.replace('{cls.time}', item.get('time', ''))
                                rendered = rendered.replace('{cls.duration}', item.get('duration', ''))
                                rendered = rendered.replace('{cls.level}', item.get('level', ''))
                            else:
                                rendered = rendered.replace('{item.title}', item.get('title', ''))
                                rendered = rendered.replace('{item.desc}', item.get('desc', ''))
                            rendered_items.append(rendered)
                        
                        # Replace the map block
                        map_block_pattern = r'\{[^{}]*\.map\([^{}]*\)[^{}]*\}'
                        extracted = re.sub(map_block_pattern, '\n'.join(rendered_items), extracted, count=1, flags=re.DOTALL)
                        print(f"   ✅ Rendered {len(items)} items from {array_name} array")
            
            
            
            
            
            
            
            return extracted
















        def extract_page_content(content: str, route_name: str, is_dashboard_detected: bool = False) -> str:
            """Extract meaningful content from page component"""
            
            
  
  
  
  
  
  
  
                        # ========== USE THE DETECTED FLAG FROM OUTSIDE ==========
            if is_dashboard_detected and route_name == 'page':
                return render_dashboard_from_source(content)
          
            
            
            
            
            
            
            
            
            
            
            
            print(f"\n{'='*60}")
            
    
            
            print(f"🔍 EXTRACTING: {route_name}")
            
            
            
            
            print(f"{'='*60}")
            print(f"📦 Original content length: {len(content)} chars")
            
            if not content:
                print(f"❌ Content is empty!")
                return ""
            
            # ⭐ STEP 0: Pre-render arrays on the ORIGINAL content
            print(f"\n📌 STEP 0: Pre-rendering arrays from source...")
            content = render_array_to_html(content)  # ← MODIFIES content
            print(f"   ✅ Arrays pre-rendered, content length: {len(content)} chars")
            
            # NOW use the modified content for the rest of extraction
            print(f"\n📌 STEP 1: Removing imports and exports...")
            clean = re.sub(r'^import\s+.*?from\s+["\'][^"\']+["\'];\s*$', '', content, flags=re.MULTILINE)  # ← Use 'content', not original
            clean = re.sub(r'^export\s+default\s+\w+;?\s*$', '', clean, flags=re.MULTILINE)
            clean = re.sub(r'^export\s+const\s+\w+\s*=\s*', '', clean, flags=re.MULTILINE)
            clean = re.sub(r'^export\s+function\s+\w+\s*\([^)]*\)\s*{?', '', clean, flags=re.MULTILINE)
            print(f"   ✅ Length after import removal: {len(clean)} chars")
       
            
            
            
            
            
            # ========== PRESERVE ORIGINAL CONTENT STRUCTURE ==========
            # Don't let AI modify the hero text and features
            # Preserve the badge text
            badge_match = re.search(r'<span\s+className="text-amber-400[^>]*>([^<]+)</span>', content)
            if badge_match:
                original_badge = badge_match.group(1)
                print(f"  ✅ Preserved badge: {original_badge}")
            
            # Preserve the tagline
            tagline_match = re.search(r'<p\s+className="text-xl md:text-2xl[^>]*>([^<]+)</p>', content)
            if tagline_match:
                original_tagline = tagline_match.group(1)
                print(f"  ✅ Preserved tagline: {original_tagline}")
            
            # Preserve the description
            desc_match = re.search(r'<p\s+className="text-base md:text-lg[^>]*>([^<]+)</p>', content)
            if desc_match:
                original_desc = desc_match.group(1)
                print(f"  ✅ Preserved description: {original_desc[:50]}...")          
            
            
            
            
            
            
            # Remove 'use client' directive
            print(f"\n📌 STEP 2: Removing 'use client' directive...")
            clean = re.sub(r'^["\']use client["\'];\s*$', '', clean, flags=re.MULTILINE)
            print(f"   ✅ Length after 'use client' removal: {len(clean)} chars")

            
            # ⭐ NEW: Check for image in cleaned content
            if 'image_1.jpg' in clean or 'image_' in clean:
                  print(f"   ✅ Image found in cleaned content")
            
            # Check for key sections in cleaned content
            print(f"\n📌 STEP 3: Checking for key sections in cleaned content...")
            if 'Our Core Pillars' in clean or 'Core Features' in clean:
                  print(f"   ✅ Features/Pillars section FOUND")
                  features_pos = clean.find('Our Core Pillars') if 'Our Core Pillars' in clean else clean.find('Core Features')
                  print(f"   📍 Section at position: {features_pos}")
                  print(f"   📄 Preview around section:")
                  print(f"      {clean[features_pos-50:features_pos+100]}...")
            else:
                  print(f"   ❌ Features/Pillars section NOT FOUND")
            
            # Check for inline array
            print(f"\n📌 STEP 4: Checking for inline array (.map())...")
            if '.map(' in clean:
                  print(f"   ✅ .map() found in cleaned content")
            else:
                  print(f"   ❌ .map() NOT found in cleaned content")
            
            # Extract return JSX using bracket counting
            print(f"\n📌 STEP 5: Extracting return JSX...")
            start_match = re.search(r'return\s*\(', clean)
            if not start_match:
                  start_match = re.search(r'return\s+', clean)
                  if not start_match:
                        print(f"   ❌ No return statement found!")
                        return f'<div class="container"><h1 class="gradient-text">{route_name.replace("_", " ").title()}</h1></div>'
            
            print(f"   ✅ Return statement found at position {start_match.start()}")
            start_pos = start_match.end()
            print(f"   📍 Start position: {start_pos}")
            
            # Count brackets to find the matching closing parenthesis
            open_count = 1
            i = start_pos
            extracted = ""
            bracket_count = 0
            
            print(f"   🔄 Counting brackets to find matching closing parenthesis...")
            while i < len(clean) and open_count > 0:
                  char = clean[i]
                  extracted += char
                  if char == '(':
                        open_count += 1
                        bracket_count += 1
                  elif char == ')':
                        open_count -= 1
                        bracket_count += 1
                  i += 1
            
            print(f"   ✅ Extraction complete. Processed {bracket_count} brackets")
            print(f"   📏 Extracted length: {len(extracted)} chars")
            
            # ⭐ CRITICAL FIX: DO NOT truncate at semicolons!
            print(f"   📏 Keeping full extracted content (no semicolon truncation): {len(extracted)} chars")
            
            extracted = extracted.strip()
            
            
            
            
            
            
            print(f"   📏 Final extracted length: {len(extracted)} chars")
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            # ⭐ Check if image was preserved in extracted content
            if 'image_1.jpg' in extracted:
                  print(f"   ✅ Image preserved in extracted content")
            else:
                  print(f"   ⚠️ Image NOT found in extracted content")
            
            # Show preview of extracted content
            print(f"\n📌 STEP 6: Preview of extracted content (first 500 chars):")
            print(f"{'-'*60}")
            print(extracted[:500])
            print(f"{'-'*60}")
            
            if extracted:
                
                
                
                  # Apply dashboard preservation
                  extracted = preserve_dashboard_content(extracted, route_name)               
                
                 
                  # ⭐ ADD THIS LINE - Render arrays from source first
                  extracted = render_arrays_from_source(extracted, content)
                  
                  
                  # Process inline arrays inside JSX
                  print(f"\n📌 STEP 7: Processing inline arrays...")
                  
                  # Find and render the pillars/features array
                  array_pattern = r'\{\s*\[([\s\S]*?)\]\s*\.map\(\(([^,]+),\s*([^)]+)\)\s*=>\s*\(\s*([\s\S]*?)\s*\)\s*\)\s*\}'
                  
                  def render_array(match):
                        array_items_str = match.group(1)
                        item_var = match.group(2).strip()
                        index_var = match.group(3).strip()
                        template = match.group(4).strip()
                        
                        print(f"      📦 Found array with {array_items_str.count('title:')} items")
                        print(f"      🏷️ Item variable: {item_var}, Index variable: {index_var}")
                        
                        items = []
                        object_pattern = r'\{\s*title:\s*["\']([^"\']+)["\']\s*,\s*desc:\s*["\']([^"\']+)["\']\s*\}'
                        object_matches = re.findall(object_pattern, array_items_str)
                        
                        for title, desc in object_matches:
                              items.append({"title": title, "desc": desc})
                              print(f"         📌 Item: '{title}' -> '{desc[:40]}...'")
                        
                        if items:
                              rendered_items = []
                              for idx, item in enumerate(items):
                                    rendered_html = template
                                    rendered_html = rendered_html.replace(f'{{{item_var}.title}}', item['title'])
                                    rendered_html = rendered_html.replace(f'{{{item_var}.desc}}', item['desc'])
                                    rendered_html = rendered_html.replace(f'{{{index_var}}}', str(idx))
                                    rendered_items.append(rendered_html)
                                    # Fix icon class for ShieldCheck
                                    rendered_html = rendered_html.replace('fa-shield-check', 'fa-shield-alt')
                              
                              print(f"      ✅ Rendered {len(rendered_items)} items")
                              return '\n'.join(rendered_items)
                        
                        return match.group(0)
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  extracted = re.sub(array_pattern, render_array, extracted, flags=re.DOTALL)
                  
                  if '.map(' in extracted:
                        print(f"   ⚠️ Some .map() patterns may not have been processed")
                        
                        
                        
                        
                        
                        
                        
                        
                          # ========== Extract products array from shop page ==========

                  products_array_pattern = r'const\s+products\s*=\s*\[\s*((?:[^\[\]]*?\{[^}]*\}[^\[\]]*?)*?)\s*\]'

                  products_match = re.search(products_array_pattern, content, re.DOTALL)

                  if products_match and route_name == 'shop':

                      # ========== STOP IF BUTTONS ALREADY EXIST ==========
                      existing_button_pattern = r'add-to-cart-btn'

                      if re.search(existing_button_pattern, content, re.DOTALL):
                          return content  # Prevent overwriting existing buttons

                      products_content = products_match.group(1)

                      # Extract each product
                      product_pattern = r'\{\s*id:\s*["\']([^"\']+)["\']\s*,\s*name:\s*["\']([^"\']+)["\']\s*,\s*price:\s*([\d.]+)'

                      product_items = re.findall(product_pattern, products_content)

                      if product_items:

                          # Build the products grid HTML
                          products_html = '<div class="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">'

                          for product_id, product_name, product_price in product_items:

                              products_html += f'''
                          <div class="group relative bg-gradient-to-br from-white/5 to-white/3 rounded-2xl overflow-hidden backdrop-blur-sm border border-white/10 hover:border-purple-500/50 transition-all duration-300 hover:-translate-y-1">

                              <div class="relative h-64 bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center">

                                  <i data-lucide="shopping-bag" class="w-16 h-16 text-purple-400/50 group-hover:scale-110 transition-transform duration-300"></i>

                                  <button class="absolute top-3 right-3 p-2 rounded-full bg-black/50 hover:bg-purple-600 transition-colors">

                                      <i data-lucide="heart" class="w-4 h-4 text-white"></i>

                                  </button>

                              </div>

                              <div class="p-5">

                                  <h3 class="text-lg font-bold mb-1">{product_name}</h3>

                                  <p class="text-sm text-gray-400 mb-3">Product</p>

                                  <div class="flex items-center justify-between">

                                      <span class="text-2xl font-bold text-purple-400">${product_price}</span>

                                      <button class="add-to-cart-btn px-4 py-2 bg-purple-600/20 rounded-full text-purple-400 hover:bg-purple-600 hover:text-white transition-all text-sm"
                                          data-id="{product_id}"
                                          data-name="{product_name}"
                                          data-price="{product_price}">
                                          Add to Cart
                                      </button>

                                  </div>

                              </div>

                          </div>'''

                          products_html += '</div>'
                          
                          
                          
                          # Replace the products grid
                          extracted = re.sub(
                              r'<div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">[\s\S]*?</div>',
                              products_html,
                              extracted
                          )
                          print(f"   ✅ Rendered {len(product_items)} products for shop page")
                          
                          
                          
                          
                          
                          
                          
                          
                          
                          
                          
                          
                          
                          
                          
                  # ========== Extract and render filter buttons ==========
                  # Pattern for filter buttons array
                  filter_pattern = r'\{\s*\[\s*([^\]]+?)\s*\]\s*\.map\(\(([^,]+),\s*([^)]+)\)\s*=>\s*\(\s*<button[^>]*>\s*\{[^}]+\}\s*<\/button>\s*\)\s*\)\s*\}'
                  
                  def render_filters(match):
                        categories_str = match.group(1)
                        # Extract quoted strings from the array
                        categories = re.findall(r'["\']([^"\']+)["\']', categories_str)
                        
                        if categories:
                            buttons_html = '<div class="flex flex-wrap justify-center gap-3">'
                            for i, cat in enumerate(categories):
                                active_class = 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/25' if i == 0 else 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10'
                                display_name = cat.capitalize()
                                buttons_html += f'''
                            <button class="filter-btn px-4 py-2 rounded-full text-sm font-medium transition-all {active_class}" data-filter="{cat}">{display_name}</button>'''
                            buttons_html += '</div>'
                            print(f"      ✅ Rendered {len(categories)} filter buttons")
                            return buttons_html
                        
                        # Fallback: generate default filter buttons
                        default_cats = ['all', 'coffee', 'blends', 'accessories']
                        buttons_html = '<div class="flex flex-wrap justify-center gap-3">'
                        for i, cat in enumerate(default_cats):
                            active_class = 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/25' if i == 0 else 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10'
                            display_name = cat.capitalize()
                            buttons_html += f'''
                        <button class="filter-btn px-4 py-2 rounded-full text-sm font-medium transition-all {active_class}" data-filter="{cat}">{display_name}</button>'''
                        buttons_html += '</div>'
                        print(f"      ✅ Generated {len(default_cats)} default filter buttons")
                        return buttons_html
                  
                  # Apply filter pattern replacement
                  extracted = re.sub(filter_pattern, render_filters, extracted, flags=re.DOTALL)                          
                          
                          
                          
                                                 
                        
                        
                        
                        
                        
                        
                  
                  # Convert JSX to HTML
                  print(f"\n📌 STEP 8: Converting JSX to HTML...")
                  extracted = re.sub(r'className=', 'class=', extracted)
                  
                  
                  extracted = extracted.replace('fa-shield-check', 'fa-shield-alt')
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  # ========== PRESERVE HERO BADGE FROM SOURCE ==========
                  # Extract the badge from original content (not extracted)
                  badge_match = re.search(
                      r'<div\s+className="inline-flex items-center gap-2[^>]*>.*?<Sparkles\s+className="([^"]*)"[^>]*/>\s*<span[^>]*>([^<]+)</span>',
                      content,
                      re.DOTALL
                  )
                  
                  if badge_match:
                      badge_text = badge_match.group(2).strip()
                      badge_html = f'''
          <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-amber-500/20 backdrop-blur-sm border border-amber-500/30 mb-6">
            <i class="fas fa-sparkles w-4 h-4 text-amber-400"></i>
            <span class="text-amber-400 text-sm font-medium uppercase tracking-wider">{badge_text}</span>
          </div>'''
                      
                      # Check if badge already exists in extracted
                      if '<div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-amber-500/20' in extracted:
                          print(f"  ✅ Hero badge already present")
                      else:
                          # Inject badge into hero section - look for the hero content div
                          if '<div class="relative z-10 text-center px-4 max-w-4xl mx-auto">' in extracted:
                              extracted = extracted.replace(
                                  '<div class="relative z-10 text-center px-4 max-w-4xl mx-auto">',
                                  '<div class="relative z-10 text-center px-4 max-w-4xl mx-auto">' + badge_html
                              )
                              print(f"  ✅ Injected hero badge: {badge_text}")
                          elif '<div class="relative z-10 text-center px-4">' in extracted:
                              extracted = extracted.replace(
                                  '<div class="relative z-10 text-center px-4">',
                                  '<div class="relative z-10 text-center px-4">' + badge_html
                              )
                              print(f"  ✅ Injected hero badge: {badge_text}")
                          else:
                              print(f"  ⚠️ Could not find hero container to inject badge")
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
          
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  
                  extracted = re.sub(r'htmlFor=', 'for=', extracted)
                  extracted = re.sub(r'<Link\s+href="([^"]+)"[^>]*>', r'<a href="\1">', extracted)
                  extracted = re.sub(r'<Link\s+href=\'([^\']+)\'[^>]*>', r'<a href="\1">', extracted)
                  extracted = re.sub(r'</Link>', '</a>', extracted)
                  extracted = re.sub(r'<Image\s+src="([^"]+)"[^>]*/?>', r'<img src="\1" alt="" />', extracted)
                  extracted = re.sub(r'<Image\s+src=\'([^\']+)\'[^>]*/?>', r'<img src="\1" alt="" />', extracted)
                  extracted = re.sub(r'<>', '<div>', extracted)
                  extracted = re.sub(r'</>', '</div>', extracted)
                  extracted = re.sub(r'\s+key=["\'][^"\']*["\']', '', extracted)
                  extracted = re.sub(r'\s+priority\s*', '', extracted)
                  extracted = re.sub(r'\s+loading="lazy"\s*', '', extracted)
                  extracted = re.sub(r'<Fragment>', '', extracted)
                  extracted = re.sub(r'</Fragment>', '', extracted)
                  extracted = re.sub(r'>\s+<', '><', extracted)
                  extracted = re.sub(r'\n{3,}', '\n\n', extracted)
                  
                  # ⭐ FINAL CHECK: If image was lost, manually inject it
                  if 'image_1.jpg' not in extracted and 'image_' in str(files.keys()):
                        print(f"\n   🔧 Image lost during conversion - manually injecting...")
                        # Find the hero section and add the image
                        if '<section class="relative h-screen' in extracted:
                              # Inject image right after section opening
                              image_tag = '<img src="/images/image_1.jpg" alt="Hero background" class="absolute inset-0 w-full h-full object-cover" />'
                              extracted = extracted.replace(
                                    '<section class="relative h-screen',
                                    f'<section class="relative h-screen">{image_tag}'
                              )
                              # Also add the dark overlay
                              overlay = '<div class="absolute inset-0 bg-black/50"></div>'
                              extracted = extracted.replace(image_tag, f'{image_tag}\n    {overlay}')
                              print(f"   ✅ Image injected into hero section")
                  
                  # Final verification
                  print(f"\n📌 STEP 9: Final verification...")
                  if 'Core Features' in extracted or 'Our Core Pillars' in extracted:
                        print(f"   ✅ Features/Pillars section present in final extracted content")
                        card_count = extracted.count('rounded-xl')
                        print(f"   📊 Cards found: {card_count}")
                        
                        if card_count >= 3:
                              print(f"   ✅ All features successfully extracted!")
                  else:
                        print(f"   ❌ Features section MISSING from final extracted content!")
                  
                  # ⭐ Final image check
                  if 'image_1.jpg' in extracted:
                        print(f"   ✅ Image present in final output!")
                  else:
                        print(f"   ⚠️ Image missing from final output!")
                  
                  
                  
                  
                  
                  print(f"\n✅ Extraction complete for {route_name}")
                  print(f"{'='*60}\n")
                  return extracted.strip()
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            print(f"❌ No JSX extracted, using fallback")
            return f'<div class="container"><h1 class="gradient-text">{route_name.replace("_", " ").title()}</h1><p>Content from {route_name}</p></div>'
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        # Scan all files for page components
        for file_path, content in files.items():
            # Match Next.js page patterns
            if file_path.endswith((".tsx", ".jsx", ".js")) and ("/app/" in file_path or file_path.startswith("app/")):
                # Skip non-page files
                if "layout" in file_path.lower() or "error" in file_path.lower() or "loading" in file_path.lower():
                    continue
                
                # Extract route name
                route = file_path.replace("app/", "").replace("/page.tsx", "").replace("/page.jsx", "").replace("/page.js", "")
                route = route.replace(".tsx", "").replace(".jsx", "").replace(".js", "")
                route_name = route if route else "home"
                route_name = route_name.replace("/", "_")
                
                print(f"\n📄 Found page: {file_path} -> {route_name}")
                

                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                extracted_content = extract_page_content(content, route_name, is_dashboard_detected)
                
                
                
                
                
                
                
                
                # ========== DEBUG: Log extracted content for home page ==========
                if route_name == 'page' or route_name == 'home':
                    print(f"\n{'='*60}")
                    print(f"🔍 DEBUGGING EXTRACTED CONTENT FOR HOME PAGE")
                    print(f"{'='*60}")
                    print(f"📏 Extracted content length: {len(extracted_content)} chars")
                    print(f"\n📄 FIRST 500 CHARACTERS:")
                    print("-" * 40)
                    print(extracted_content[:500])
                    print("-" * 40)
                    
                    print(f"\n🔎 SEARCHING FOR KEY SECTIONS:")
                    print("-" * 40)
                    
                    # Check for hero section
                    if 'relative h-screen' in extracted_content or 'hero' in extracted_content.lower():
                        print("✅ Hero section found")
                    else:
                        print("❌ Hero section MISSING")
                    
                    # Check for features section
                    if 'Our Features' in extracted_content:
                        print("✅ 'Our Features' heading found")
                    else:
                        print("❌ 'Our Features' heading MISSING")
                    
                    # Check for grid
                    if 'grid md:grid-cols-3' in extracted_content:
                        print("✅ Grid container found")
                    else:
                        print("❌ Grid container MISSING")
                    
                    # Check for individual feature cards
                    card_count = extracted_content.count('rounded-xl bg-white/5')
                    print(f"📊 Feature cards found: {card_count}")
                    
                    # Check for specific feature titles
                    if 'Cloud Analytics' in extracted_content:
                        print("✅ 'Cloud Analytics' found")
                    else:
                        print("❌ 'Cloud Analytics' MISSING")
                    
                    if 'Team Sync' in extracted_content:
                        print("✅ 'Team Sync' found")
                    else:
                        print("❌ 'Team Sync' MISSING")
                    
                    if 'Security First' in extracted_content:
                        print("✅ 'Security First' found")
                    else:
                        print("❌ 'Security First' MISSING")
                    
                    # Check if the inline array pattern exists
                    if 'map((f, i)' in extracted_content or '.map(' in extracted_content:
                        print("⚠️ Raw .map() still present (not rendered)")
                        # Find and show the map pattern
                        import re
                        map_match = re.search(r'\{[^}]*\.map\([^)]*\)[^}]*\}', extracted_content)
                        if map_match:
                            print(f"   Map pattern found: {map_match.group(0)[:150]}...")
                    else:
                        print("✅ No raw .map() found (should be rendered)")
                    
                    # Check for any JavaScript expressions left
                    if '{' in extracted_content and '}' in extracted_content:
                        # Count remaining JS expressions
                        js_exprs = re.findall(r'\{[^{}]*\}', extracted_content)
                        if js_exprs:
                            print(f"⚠️ Remaining JS expressions: {len(js_exprs)}")
                            for expr in js_exprs[:3]:
                                print(f"   - {expr[:80]}")
                    
                    print(f"\n📄 LAST 500 CHARACTERS:")
                    print("-" * 40)
                    print(extracted_content[-500:])
                    print("-" * 40)
                    print(f"{'='*60}\n")
                               
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
             # ========== ADD THIS AUTH OVERRIDE RIGHT HERE ==========
                # Override signup/login pages with backend HTML forms
                if route_name in ['signup', 'login', 'auth']:
                    if route_name == 'signup':
                        page_contents[route_name] = '''
                        <div class="min-h-screen flex items-center justify-center py-12 px-4">
                            <div class="max-w-md w-full space-y-8 bg-white/5 backdrop-blur-sm p-8 rounded-2xl border border-white/10">
                                <div>
                                    <h2 class="text-center text-3xl font-extrabold text-white">Create your account</h2>
                                    <p class="mt-2 text-center text-sm text-gray-400">
                                        Already have an account? <a href="#" onclick="showPage('login'); return false;" class="font-medium text-purple-400 hover:text-purple-300">Sign in</a>
                                    </p>
                                </div>
                                <form id="signup-form" class="mt-8 space-y-6">
                                    <div class="space-y-4">
                                        <div>
                                            <input type="text" name="name" required placeholder="Full name" class="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500" />
                                        </div>
                                        <div>
                                            <input type="email" name="email" required placeholder="Email address" class="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500" />
                                        </div>
                                        <div>
                                            <input type="password" name="password" required placeholder="Password (min. 6 characters)" class="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500" />
                                        </div>
                                        <div>
                                            <input type="password" name="confirmPassword" required placeholder="Confirm password" class="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500" />
                                        </div>
                                    </div>
                                    <button type="submit" class="w-full flex justify-center py-3 px-4 text-sm font-medium rounded-lg text-white bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700">Sign up</button>
                                </form>
                            </div>
                        </div>
                        '''
                        print(f"  ✅ Using backend HTML form for signup")
                    elif route_name == 'login':
                        page_contents[route_name] = '''
                        <div class="min-h-screen flex items-center justify-center py-12 px-4">
                            <div class="max-w-md w-full space-y-8 bg-white/5 backdrop-blur-sm p-8 rounded-2xl border border-white/10">
                                <div>
                                    <h2 class="text-center text-3xl font-extrabold text-white">Sign in to your account</h2>
                                    <p class="mt-2 text-center text-sm text-gray-400">
                                        Or <a href="#" onclick="showPage('signup'); return false;" class="font-medium text-purple-400 hover:text-purple-300">create a new account</a>
                                    </p>
                                </div>
                                <form id="login-form" class="mt-8 space-y-6">
                                    <div class="space-y-4">
                                        <div>
                                            <input type="email" name="email" required placeholder="Email address" class="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500" />
                                        </div>
                                        <div>
                                            <input type="password" name="password" required placeholder="Password" class="w-full px-4 py-3 border border-white/10 bg-white/5 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500" />
                                        </div>
                                    </div>
                                    <button type="submit" class="w-full flex justify-center py-3 px-4 text-sm font-medium rounded-lg text-white bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700">Sign in</button>
                                </form>
                            </div>
                        </div>
                        '''
                        print(f"  ✅ Using backend HTML form for login")
                # ========== END OF AUTH OVERRIDE ==========
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                # ========== CHANGE THIS PART - USE ELIF ==========
                elif extracted_content and len(extracted_content) > 50:
                    page_contents[route_name] = extracted_content[:1000000]  # Limit size
                    print(f"  ✅ Extracted {len(extracted_content)} chars")
                else:
                    # Create meaningful fallback content based on route name
                    display_name = route_name.replace("_", " ").title()
                    page_contents[route_name] = f'''
                    <div class="container">
                        <div class="hero" style="min-height: 40vh; margin: 2rem;">
                            <div class="hero-content">
                                <h1 class="gradient-text">{display_name}</h1>
                                <p>Welcome to our {display_name.lower()} page. Explore what we have to offer.</p>
                                <button class="btn" onclick="showPage('home')">Back to Home</button>
                            </div>
                        </div>
                        <div class="grid">
                            <div class="card">
                                <h3>About {display_name}</h3>
                                <p>Learn more about our {display_name.lower()} offerings and how we can help you.</p>
                                <button class="btn" style="margin-top: 1rem;">Learn More</button>
                            </div>
                            <div class="card">
                                <h3>Our {display_name} Services</h3>
                                <p>Discover the range of services we provide in {display_name.lower()}.</p>
                                <button class="btn" style="margin-top: 1rem;">View Services</button>
                            </div>
                            <div class="card">
                                <h3>Contact Us About {display_name}</h3>
                                <p>Have questions? Reach out to our team for more information.</p>
                                <button class="btn" style="margin-top: 1rem;">Get in Touch</button>
                            </div>
                        </div>
                    </div>
                    '''
                    print(f"  ⚠️ Using fallback content for {route_name}")
                    
                    
                    
                    
                    
                    
                    
                    
        # Print summary
        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"  - Brand: {brand_name}")
        print(f"  - Navigation links: {len(nav_links)}")
        print(f"  - Pages extracted: {len(page_contents)}")
        for route, content in page_contents.items():
            print(f"    • {route}: {len(content)} chars")
        print(f"  - Footer: {'✅ Extracted' if footer_html else '❌ Not found (will generate default)'}")
        
        
        
        
        
        # ========== CALL THE DASHBOARD DETECTION HERE ==========
        is_dashboard = detect_dashboard_from_content(page_contents, user_prompt)
        # ======================================================
        
        
        
        
        
        
        # ========== BUILD DYNAMIC PAGES SECTION FOR PROMPT ==========
        pages_section = ""
        for route, content in page_contents.items():
            pages_section += f"""
--- PAGE: {route} ---
{content[:50000]}
--- END OF PAGE: {route} ---

"""
        
        print(f"📄 Built pages section for routes: {list(page_contents.keys())}")       
        
        
        
        
        
        
        
        
        
        
        
        
        
        

        # ========== DEBUG: CHECK WHAT WAS EXTRACTED ==========
        print(f"\n🔍 DEBUG - page_contents keys: {list(page_contents.keys())}")
        for key in page_contents.keys():
            preview = page_contents[key][:100] if page_contents[key] else "(empty)"
            print(f"  Key: '{key}' - Content preview: {preview}...")
        # ====================================================

        # ========== COLLECT AVAILABLE IMAGES ==========
        first_image = None        
                           
                    
                    
                    
                    
                    
                    
                    

        # Ensure all navigation pages have content
        for href, label in nav_links:
            route_key = href.replace("/", "_")
            if route_key not in page_contents:
                page_contents[route_key] = f'''
                <div class="container">
                    <div class="hero" style="min-height: 40vh; margin: 2rem;">
                        <div class="hero-content">
                            <h1 class="gradient-text">{label}</h1>
                            <p>Welcome to our {label.lower()} page. Explore our offerings and find what suits you best.</p>
                            <button class="btn" onclick="showPage('home')">Back to Home</button>
                        </div>
                    </div>
                    <div class="grid">
                        <div class="card">
                            <h3>Featured {label}</h3>
                            <p>Discover amazing opportunities in our {label.lower()} section.</p>
                            <button class="btn" style="margin-top: 1rem;">Learn More</button>
                        </div>
                        <div class="card">
                            <h3>Upcoming {label}</h3>
                            <p>Stay updated with the latest news and events in {label.lower()}.</p>
                            <button class="btn" style="margin-top: 1rem;">View Details</button>
                        </div>
                        <div class="card">
                            <h3>Contact Us About {label}</h3>
                            <p>Have questions? Reach out to our team for more information.</p>
                            <button class="btn" style="margin-top: 1rem;">Get in Touch</button>
                        </div>
                    </div>
                </div>
                '''

        # Print summary
        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"  - Brand: {brand_name}")
        print(f"  - Navigation links: {len(nav_links)}")
        print(f"  - Pages extracted: {len(page_contents)}")
        for route, content in page_contents.items():
            print(f"    • {route}: {len(content)} chars")
        print(f"  - Footer: {'✅ Extracted' if footer_html else '❌ Not found (will generate default)'}")

        # ========== COLLECT AVAILABLE IMAGES ==========
        first_image = None
        for file_path in files.keys():
            if file_path.startswith("public/images/") and file_path.endswith((".jpg", ".png", ".jpeg")):
                first_image = "/" + file_path.replace("public/", "")
                break

        print(f"\n🖼️ First image: {first_image}")
        
        
        
        
        
        
    
    
    
    
    
     
        
          # ========== DETECT PROJECT TYPE ==========
        # Check user prompt for dashboard keywords
        prompt_lower = user_prompt.lower()
        dashboard_keywords = [
            'dashboard', 'analytics', 'admin', 'metrics', 'statistics',
            'insights', 'overview', 'reports', 'monitoring', 'kpi',
            'kpi cards', 'analytics dashboard', 'business intelligence'
        ]
        
        is_dashboard = any(keyword in prompt_lower for keyword in dashboard_keywords)
        
        # ALSO check the actual page.tsx content
        if not is_dashboard:
            homepage_content = files.get("app/page.tsx", "")
            if 'kpiData' in homepage_content or 'ResponsiveContainer' in homepage_content or 'recharts' in homepage_content:
                is_dashboard = True
                print(f"📊 Dashboard detected from page.tsx content")
        
        # If dashboard detected, force skip e-commerce
        if is_dashboard:
            has_shop_page = False
            has_cart_page = False
            is_ecommerce = False
            is_gym = False
            print(f"📊 DASHBOARD MODE ENABLED - e-commerce features disabled")
        else:
            has_shop_page = any('shop' in f.lower() or 'products' in f.lower() or 'store' in f.lower() for f in files.keys())
            has_cart_page = any('cart' in f.lower() for f in files.keys())
            is_ecommerce = has_shop_page and has_cart_page
        
        # Detect gym/fitness website (only if not dashboard)
        is_gym = False
        if not is_dashboard:
            is_gym = any('gym' in f.lower() or 'fitness' in f.lower() or 'workout' in f.lower() or 'trainer' in f.lower() or 'classes' in f.lower() or 'membership' in f.lower() for f in files.keys())
        
        print(f"📊 Project detection: dashboard={is_dashboard}, ecommerce={is_ecommerce}, gym={is_gym}, shop={has_shop_page}, cart={has_cart_page}")
        
        
        

        # ========== PREPARE DATA FOR PROMPT ==========
        nav_links_json = json.dumps(nav_links)
        page_contents_json = json.dumps(page_contents, indent=2)[:15000]
        
        # Get home page content
        home_content = page_contents.get('page', f'<div class="hero-content"><h1 class="gradient-text">{brand_name}</h1><p>Welcome to our website</p><button class="btn">Get Started</button></div>')
        
        
        
        
        
        
        
        
        
        
        
        # ========== ADD THIS CODE HERE - EXTRACT PRODUCTS DATA ==========
        products_data = ""
        shop_content = files.get("app/shop/page.tsx", "")
        if shop_content:
            products_match = re.search(r'const\s+products\s*=\s*\[\s*([\s\S]*?)\s*\]', shop_content)
            if products_match:
                products_data = products_match.group(1)
                print(f"📦 Extracted products data: {products_data[:200]}...")
            else:
                # Try alternative pattern for products array
                products_match = re.search(r'const\s+products\s*=\s*\[\s*((?:[^\[\]]*?\{[^}]*\}[^\[\]]*?)*?)\s*\]', shop_content, re.DOTALL)
                if products_match:
                    products_data = products_match.group(1)
                    print(f"📦 Extracted products data (alt pattern): {products_data[:200]}...")
        
        # Also extract cart items if needed
        cart_content = files.get("app/cart/page.tsx", "")       
        
        
        
        
        
        
        
        
        
        
        
        
        # Fix ShieldCheck icon to use correct Font Awesome class
        home_content = home_content.replace('fa-shield-check', 'fa-shield-alt')       
        
        
        
        
        
        
        # Get backend URL
        BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
         # ========== FORCE EXTRACT FAQ AND STATS FROM SOURCE FILES ==========
        homepage_source = files.get("app/page.tsx", "")
        faq_component_source = files.get("components/FAQ.tsx", "")
        
        
        
        
        
        
        
        
        
        
        
        
        
        
         # ========== STRONG FAQ EXTRACTION - HANDLES ALL FORMATS ==========
        faq_html = ""
        stats_html = ""
        
        # Combine all source files to search
        all_source = homepage_source + "\n" + faq_component_source
        
        # METHOD 1: Extract from inline map array (most common in your code)
        # Pattern: {[ { q: "text", a: "text" }, { q: "text", a: "text" } ].map(...)}
        inline_map_pattern = r'\{\s*\[\s*\{\s*(?:q|question):\s*["\']([^"\']+)["\']\s*,\s*(?:a|answer):\s*["\']([^"\']+)["\']\s*\}'
        inline_items = re.findall(inline_map_pattern, homepage_source)
        
        if inline_items:
            print(f"✅ Found {len(inline_items)} FAQ items from inline map")
            for question, answer in inline_items:
                faq_html += f'''
            <div class="bg-gradient-to-br from-white/5 to-white/3 rounded-2xl border border-white/10 overflow-hidden">
                <button class="faq-btn w-full px-6 py-4 flex justify-between items-center text-left hover:bg-white/5 transition-colors">
                    <span class="font-semibold text-white">{question}</span>
                    <i class="fas fa-plus text-purple-400"></i>
                </button>
                <div class="faq-answer hidden px-6 pb-4 text-gray-400">
                    {answer}
                </div>
            </div>'''
        
        # METHOD 2: Extract from React component state array
        # Pattern: const [openFaq, setOpenFaq] = useState... and array defined above
        if not faq_html:
            # Look for faqs array with q/a properties
            const_faq_pattern = r'(?:const|let)\s+faqs\s*=\s*\[\s*((?:[^\[\]]*?\{[^}]*\}[^\[\]]*?)*?)\s*\]'
            const_match = re.search(const_faq_pattern, all_source, re.DOTALL)
            
            if const_match:
                faq_content = const_match.group(1)
                # Match both { q: "...", a: "..." } and { question: "...", answer: "..." }
                item_pattern = r'\{\s*(?:q|question):\s*["\']([^"\']+)["\']\s*,\s*(?:a|answer):\s*["\']([^"\']+)["\']\s*\}'
                faq_items = re.findall(item_pattern, faq_content)
                
                if faq_items:
                    for question, answer in faq_items:
                        faq_html += f'''
            <div class="bg-gradient-to-br from-white/5 to-white/3 rounded-2xl border border-white/10 overflow-hidden">
                <button class="faq-btn w-full px-6 py-4 flex justify-between items-center text-left hover:bg-white/5 transition-colors">
                    <span class="font-semibold text-white">{question}</span>
                    <i class="fas fa-plus text-purple-400"></i>
                </button>
                <div class="faq-answer hidden px-6 pb-4 text-gray-400">
                    {answer}
                </div>
            </div>'''
                    print(f"✅ Extracted {len(faq_items)} FAQ items from const faqs array")
        
        # METHOD 3: Extract from JSX directly (for inline FAQ without array variable)
        if not faq_html:
            # Look for FAQ items in the JSX structure
            jsx_faq_pattern = r'<div[^>]*className="[^"]*faq[^"]*"[^>]*>.*?<span[^>]*>([^<]+)</span>.*?<p[^>]*>([^<]+)</p>'
            jsx_matches = re.findall(jsx_faq_pattern, homepage_source, re.DOTALL)
            
            if jsx_matches:
                for question, answer in jsx_matches:
                    faq_html += f'''
            <div class="bg-gradient-to-br from-white/5 to-white/3 rounded-2xl border border-white/10 overflow-hidden">
                <button class="faq-btn w-full px-6 py-4 flex justify-between items-center text-left hover:bg-white/5 transition-colors">
                    <span class="font-semibold text-white">{question.strip()}</span>
                    <i class="fas fa-plus text-purple-400"></i>
                </button>
                <div class="faq-answer hidden px-6 pb-4 text-gray-400">
                    {answer.strip()}
                </div>
            </div>'''
                    print(f"✅ Extracted {len(jsx_matches)} FAQ items from JSX structure")
        
        # METHOD 4: Extract as last resort using simple search
        if not faq_html:
            # Search for patterns like "question:" and "answer:" in the source
            simple_pattern = r'(?:q|question)[:\s]+["\']([^"\']+)["\']\s*,\s*(?:a|answer)[:\s]+["\']([^"\']+)["\']'
            simple_matches = re.findall(simple_pattern, all_source, re.IGNORECASE)
            
            if simple_matches:
                print(f"✅ Found {len(simple_matches)} FAQ items using simple pattern")
                for question, answer in simple_matches:
                    faq_html += f'''
            <div class="bg-gradient-to-br from-white/5 to-white/3 rounded-2xl border border-white/10 overflow-hidden">
                <button class="faq-btn w-full px-6 py-4 flex justify-between items-center text-left hover:bg-white/5 transition-colors">
                    <span class="font-semibold text-white">{question}</span>
                    <i class="fas fa-plus text-purple-400"></i>
                </button>
                <div class="faq-answer hidden px-6 pb-4 text-gray-400">
                    {answer}
                </div>
            </div>'''
        
        if not faq_html:
            faq_html = '<p class="text-gray-400 text-center">No FAQ items found</p>'
            print("⚠️ No FAQ section found in source")
        else:
            print(f"📊 Total FAQ items extracted: {faq_html.count('faq-btn')}")
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        # ========== EXTRACT FOOTER FROM SOURCE ==========
        footer_html = ""
        
        # Check for Footer.tsx component file
        footer_component = files.get("components/Footer.tsx", "")
        
        if footer_component:
            print("🔍 Extracting footer from components/Footer.tsx")
            
            # Extract the JSX content from return statement
            return_match = re.search(r'return\s*\(\s*([\s\S]*?)\s*\)\s*;', footer_component, re.DOTALL)
            
            if return_match:
                footer_html = return_match.group(1)
                
                # Convert React/JSX to HTML
                footer_html = re.sub(r'className=', 'class=', footer_html)
                footer_html = re.sub(r'<Link\s+href="([^"]+)"[^>]*>', r'<a href="\1">', footer_html)
                footer_html = re.sub(r'</Link>', '</a>', footer_html)
                
                # Convert Lucide icons to Font Awesome
                footer_html = re.sub(r'<Sparkles\s*/>', '<i class="fas fa-sparkles text-purple-500"></i>', footer_html)
                footer_html = re.sub(r'<Mail\s*/>', '<i class="fas fa-envelope"></i>', footer_html)
                footer_html = re.sub(r'<Phone\s*/>', '<i class="fas fa-phone"></i>', footer_html)
                footer_html = re.sub(r'<Send\s*/>', '<i class="fas fa-paper-plane"></i>', footer_html)
                footer_html = re.sub(r'<ArrowUp\s*/>', '<i class="fas fa-arrow-up"></i>', footer_html)
                
                # Remove useState and useEffect hooks
                footer_html = re.sub(r'\{showScroll \&\& \(', '', footer_html)
                footer_html = re.sub(r'\)\}', '', footer_html)
                
                print(f"✅ Footer extracted from component: {len(footer_html)} chars")
        
        # Fallback to default footer if component not found
        if not footer_html:
            from datetime import datetime
            footer_html = f'''
            <footer class="bg-zinc-950 border-t border-white/10 py-12">
                <div class="container mx-auto px-4 grid md:grid-cols-4 gap-8">
                    <div class="space-y-4">
                        <div class="flex items-center gap-2"><i class="fas fa-sparkles text-purple-500"></i><span class="font-bold">{brand_name}</span></div>
                        <p class="text-sm text-gray-400">Premium digital solutions.</p>
                    </div>
                    <div><h4 class="font-bold mb-4">Quick Links</h4><ul class="space-y-2 text-sm text-gray-400"><li>Courses</li><li>Admissions</li></ul></div>
                    <div><h4 class="font-bold mb-4">Contact</h4><ul class="space-y-2 text-sm text-gray-400"><li>support@example.com</li><li>+1 (555) 123-4567</li></ul></div>
                    <div><h4 class="font-bold mb-4">Newsletter</h4><div class="flex gap-2"><input class="bg-white/5 p-2 rounded w-full" placeholder="Email" /><button class="bg-purple-600 p-2 rounded"><i class="fas fa-paper-plane"></i></button></div></div>
                </div>
                <div class="text-center mt-8 text-sm text-gray-600">© {datetime.now().year} {brand_name}. All rights reserved.</div>
            </footer>
            '''
        
        # Also extract scroll to top button JavaScript
        scroll_script = """
        <script>
        // Scroll to Top Functionality
        let scrollBtn = document.getElementById('scrollToTop');
        if(scrollBtn) {
            window.addEventListener('scroll', () => {
                if(window.scrollY > 500) {
                    scrollBtn.classList.remove('hidden');
                } else {
                    scrollBtn.classList.add('hidden');
                }
            });
            scrollBtn.addEventListener('click', () => {
                window.scrollTo({top: 0, behavior: 'smooth'});
            });
        }
        </script>
        """       
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
         # ========== EXTRACT TESTIMONIALS FROM SOURCE ==========
        testimonials_html = ""
        
        # Check for testimonials array in homepage
        testimonials_pattern = r'const\s+testimonials\s*=\s*\[\s*((?:[^\[\]]*?\{[^}]*\}[^\[\]]*?)*?)\s*\]'
        testimonials_match = re.search(testimonials_pattern, homepage_source, re.DOTALL)
        
        if not testimonials_match:
            # Also check if testimonials are defined as a variable
            alt_pattern = r'const\s+testimonials\s*=\s*\[\s*((?:[^\[\]]*?\{[^}]*\}[^\[\]]*?)*?)\s*\]'
            testimonials_match = re.search(alt_pattern, homepage_source, re.DOTALL)
        
        if testimonials_match:
            testimonials_content = testimonials_match.group(1)
            
            # Try format 1: { name: "...", role: "...", quote: "..." }
            pattern1 = r'\{\s*name:\s*["\']([^"\']+)["\']\s*,\s*role:\s*["\']([^"\']+)["\']\s*,\s*quote:\s*["\']([^"\']+)["\']\s*\}'
            testimonial_items = re.findall(pattern1, testimonials_content)
            
            # If not found, try format 2: { name: "...", text: "..." } (no role)
            if not testimonial_items:
                pattern2 = r'\{\s*name:\s*["\']([^"\']+)["\']\s*,\s*text:\s*["\']([^"\']+)["\']\s*\}'
                items = re.findall(pattern2, testimonials_content)
                for name, text in items:
                    testimonial_items.append((name, "", text))
                print(f"📝 Found testimonials without roles")
            
            if testimonial_items:
                for name, role, quote in testimonial_items:
                    if role:
                        testimonials_html += f'''
            <div class="bg-gray-900 p-8 rounded-2xl border border-white/10">
                <p class="text-gray-300 mb-6 italic">"{quote}"</p>
                <div class="font-bold text-white">{name}</div>
                <div class="text-sm text-purple-400">{role}</div>
            </div>'''
                    else:
                        testimonials_html += f'''
            <div class="bg-gray-900 p-8 rounded-2xl border border-white/10">
                <p class="text-gray-300 mb-6 italic">"{quote}"</p>
                <div class="font-bold text-purple-400">- {name}</div>
            </div>'''
                print(f"✅ Extracted {len(testimonial_items)} testimonials from source")
            else:
                testimonials_html = '<p class="text-gray-400 text-center">No testimonials found</p>'
        else:
            # Also check for inline testimonials in JSX
            inline_testimonial_pattern = r'<div[^>]*className="[^"]*testimonial[^"]*"[^>]*>.*?<p[^>]*>([^<]+)</p>.*?<h[34][^>]*>([^<]+)</h[34]>'
            inline_matches = re.findall(inline_testimonial_pattern, homepage_source, re.DOTALL)
            if inline_matches:
                for quote, name in inline_matches:
                    testimonials_html += f'''
            <div class="bg-gray-900 p-8 rounded-2xl border border-white/10">
                <p class="text-gray-300 mb-6 italic">"{quote.strip()}"</p>
                <div class="font-bold text-purple-400">- {name.strip()}</div>
            </div>'''
                print(f"✅ Extracted {len(inline_matches)} testimonials from inline JSX")
            else:
                testimonials_html = '<p class="text-gray-400 text-center">No testimonials section found</p>'
                print("⚠️ No testimonials section found in source")
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
         # ⭐⭐⭐ CRITICAL: Use Cloudinary URL for images (NO base64) ⭐⭐⭐
        # Get the Cloudinary URL for the image
        image_url = existing_image_url  # Use existing URL if provided during edit
        
        # Also check if there's a Cloudinary URL in the files
        if not image_url and "__cloudinary_image_url__" in files:
            image_url = files["__cloudinary_image_url__"]
            print(f"📸 Found Cloudinary URL in files: {image_url[:80]}...")
        
        if not image_url:
            # No existing URL, upload new image
            for file_key, content in files.items():
                if file_key.startswith("public/images/") and isinstance(content, str) and content.startswith("__binary_base64__"):
                    # Upload to Cloudinary and get cached URL
                    image_url = await get_cloudinary_url_for_preview(file_key, content, files)
                    if image_url:
                        print(f"📸 Using Cloudinary URL: {image_url[:80]}...")
                    else:
                        # Fallback to placeholder if Cloudinary fails
                        image_url = "https://placehold.co/1920x1080/1a1a2e/white?text=Image"
                        print(f"⚠️ Cloudinary failed, using placeholder")
                    break
        else:
            print(f"📸 Using existing Cloudinary URL (preserved from original): {image_url[:80]}...")
            # Store the existing URL in files for database
            files["__cloudinary_image_url__"] = image_url
        
        # ⭐⭐⭐ CRITICAL FIX: ALWAYS use image_url for first_image_display ⭐⭐⭐
        # During EDIT: Use Cloudinary URL from database
        # During INITIAL BUILD: Use uploaded Cloudinary URL
        if image_url and image_url.startswith('https://res.cloudinary.com'):
            first_image_display = image_url
            print(f"🖼️ ✅ Using Cloudinary URL for hero: {first_image_display[:80]}...")
        elif first_image:
            first_image_display = first_image
            print(f"🖼️ Using local image path: {first_image_display}")
        else:
            first_image_display = 'None - use gradient background'
            print(f"🖼️ No image available, using gradient")
        
        # If we have an image URL, force it into the home content
        if image_url:
            # Replace any image path with the Cloudinary URL
            home_content = home_content.replace('/images/image_1.jpg', image_url)
            home_content = home_content.replace('/images/image_2.jpg', image_url)
            home_content = re.sub(r'src=["\']/images/[^"\']+\.jpg["\']', f'src="{image_url}"', home_content)
            home_content = re.sub(r"src=['\']/images/[^'\']+\.jpg['\']", f'src="{image_url}"', home_content)
            
            # Also ensure the hero section has the image tag
            if '<img' not in home_content:
                # Inject the image into the hero section
                home_content = f'''
        <section class="relative h-screen w-full overflow-hidden">
            <img src="{image_url}" class="absolute inset-0 w-full h-full object-cover" />
            <div class="absolute inset-0 bg-black/50"></div>
            <div class="relative z-10 flex flex-col items-center justify-center h-full text-center px-4">
                <h1 class="text-5xl md:text-7xl font-bold text-white mb-6">{brand_name}</h1>
                <p class="text-xl text-gray-200 mb-8 max-w-2xl mx-auto">Welcome to {brand_name}</p>
                <button class="btn">Get Started</button>
            </div>
        </section>
        '''
                print(f"  ✅ Injected Cloudinary image into home content")
        
        # Update the first_image display for the prompt
        first_image_display = image_url if image_url else (first_image if first_image else 'None - use gradient background')
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        prompt = f"""CRITICAL: You MUST include Tailwind CSS CDN in the <head> tag:
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://unpkg.com/lucide@latest"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

Create a BEAUTIFUL, COMPLETE HTML preview for "{brand_name}".









================================================================================
✅ REQUIRED STRUCTURE - YOU MUST OUTPUT:
================================================================================

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[PROJECT_NAME]</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        /* COMPLETE CSS HERE*/
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: linear-gradient(135deg, #0f0f12 0%, #1a1a2e 100%);
            font-family: 'Inter', sans-serif;
            color: #e2e8f0;
            min-height: 100vh;
        }}
        /* ALL navigation and page styles */
    </style>
</head>
<body>




<header>
    <nav class="nav-container">
        <a href="#" class="brand flex items-center gap-2 group" onclick="handleBrandClick(event); return false;">
            <i data-lucide="sparkles" class="w-8 h-8" style="color: #d8a219;"></i>
            <span class="text-white text-xl font-bold">{brand_name}</span>
        </a>
        <div class="hidden md:flex space-x-2 items-center" id="nav-links-container">
            <!-- Navigation links will be dynamically inserted here -->
            {navigation_html}
        </div>
        <button id="mobile-menu-button" class="md:hidden p-2 rounded-lg hover:bg-white/10 transition-colors">
            <i data-lucide="menu" class="w-6 h-6" style="color: #d8a219;"></i>
        </button>
    </nav>
    
    <div id="mobile-menu" class="hidden md:hidden bg-black/80 backdrop-blur-lg p-4 space-y-2 border-t border-white/10">
        {navigation_html}
    </div>
</header>




<div id="page_home" class="page active">
    <!-- COMPLETE HOME PAGE CONTENT -->
    <section class="relative h-screen">
        <!-- Hero section with image,badge,trust indicators, title, description -->
    </section>
    <section class="py-20">
        <!-- Features section -->
    </section>
</div>

<div id="page_shop" class="page">
    <!-- COMPLETE SHOP PAGE WITH PRODUCTS -->
</div>

<div id="page_cart" class="page">
    <!-- COMPLETE CART PAGE WITH CONTAINERS -->
</div>

<footer>
    <!-- COMPLETE FOOTER -->
</footer>

<script>
    // COMPLETE NAVIGATION JAVASCRIPT
    function showPage(pageId) {{ ... }}
    function handleBrandClick(e) {{ ... }}
    // ALL REQUIRED FUNCTIONS
</script>

</body>
</html>

================================================================================
📋 PAGE REQUIREMENTS:
================================================================================

HOME PAGE (page_home) may contain:
- Hero section with h1 and button
- Features section with AT LEAST 3 cards
- FAQ section with working accordions
- Trust badges 

SHOP PAGE (page_shop) MUST contain:
- Product grid with AT LEAST 3 products
- Each product has add-to-cart-btn with data-id, data-name, data-price

CART PAGE (page_cart) MUST contain:
- cart-items-list div (empty container)
- empty-cart-message-cart div
- cart-summary div with checkout button

================================================================================
🔧 SELF-VALIDATION CHECKLIST (CHECK BEFORE OUTPUT):
================================================================================

[ ] Does <!DOCTYPE html> exist at top?
[ ] Is there a closing </html> at bottom?
[ ] Does every <div> have a closing </div>?
[ ] Are all IDs unique and non-empty?
[ ] Is page_home NOT empty (has content)?
[ ] Is navigation header present?
[ ] Is footer present?
[ ] No stray characters or incomplete tags?
[ ] CSS selectors are valid (no #. or empty selectors)?

================================================================================
⚠️ REMEMBER: If any page is empty or missing, REGENERATE!
================================================================================











================================================================================
🚨🚨🚨 CRITICAL: PRESERVE ALL EXTRACTED CONTENT - NO GENERATION 🚨🚨🚨
================================================================================

The HTML content below has been EXTRACTED DIRECTLY from your source files.
You MUST use this EXACT content. DO NOT generate your own content.

================================================================================
✅ CONTENT YOU MUST PRESERVE (COPY EXACTLY AS SHOWN):
================================================================================

1. **HERO BADGE** - The badge with EST. 2024 and Sparkles icon
2. **HERO TITLE** - The main h1 heading
3. **HERO TAGLINE** - The amber-colored description
4. **HERO DESCRIPTION** - The longer paragraph text
5. **CTA BUTTONS** - "Book a Table" and "View Menu" with their icons
6. **TRUST BADGES** - The 4 badges at the bottom (4.9/5, 10k+ Diners, Fresh Ingredients, Award Winning)
7. **FEATURES SECTION** - ALL 4 feature cards with their titles and descriptions
8. **FAQ SECTION** - ALL 4 FAQ items with questions and answers

================================================================================
❌ FORBIDDEN - DO NOT:
================================================================================

1. ❌ DO NOT generate your own feature cards - use the EXACT ones from extraction
2. ❌ DO NOT change the badge text "EST. 2024" to something else
3. ❌ DO NOT remove the trust badges
4. ❌ DO NOT change the CTA button text or styling
5. ❌ DO NOT add extra sections that don't exist in the extraction
6. ❌ DO NOT simplify or truncate any content

================================================================================
✅ VERIFICATION CHECKLIST BEFORE OUTPUT:
=========================================================-=======================

[ ] Hero badge (EST. 2024 with Sparkles) is present
[ ] H1 title matches: "{brand_name}"
[ ] Both CTA buttons are present
[ ] Trust badges (4 items) are present
[ ] Features section has EXACTLY 4 cards
[ ] FAQ section has EXACTLY 4 items
[ ] No content has been replaced with placeholders

================================================================================
EXTRACTED CONTENT TO USE (COPY THIS EXACTLY):
================================================================================

{page_contents.get('page', '')}

================================================================================
IF ANY OF THE ABOVE IS MISSING, REGENERATE USING THE EXTRACTED CONTENT ABOVE.
================================================================================












================================================================================
🚨🚨🚨 CRITICAL: FAQ & FOOTER - MUST PRESERVE ALL CONTENT 🚨🚨🚨
================================================================================

**FAQ SECTION REQUIREMENTS:**

1. You MUST include ALL {faq_html.count('faq-btn') if faq_html else '4'} FAQ items from the source below
2. DO NOT add, remove, or modify any FAQ questions or answers
3. Each FAQ item MUST have:
   - class="faq-btn" on the button
   - class="faq-answer hidden" on the answer div
   - A plus/minus icon (fa-plus/fa-minus) for toggle functionality
4. FAQ accordion JavaScript MUST be included in the <script> tag

**EXACT FAQ HTML TO USE (COPY THIS ENTIRELY):**

{faq_html if faq_html else '''
<div class="space-y-4">
    <div class="bg-white/5 rounded-2xl border border-white/10 overflow-hidden">
        <button class="faq-btn w-full px-6 py-4 flex justify-between items-center text-left hover:bg-white/5 transition-colors">
            <span class="font-semibold text-white">How does it work?</span>
            <i class="fas fa-plus text-purple-400"></i>
        </button>
        <div class="faq-answer hidden px-6 pb-4 text-gray-400">Answer here.</div>
    </div>
</div>
'''}

**FOOTER REQUIREMENTS:**

1. You MUST include the EXACT footer HTML extracted from the source below
2. DO NOT modify, simplify, or replace the footer content
3. Footer MUST be placed AFTER all page divs, before closing </body>
4. Footer icons MUST use Font Awesome classes (fab fa-*, fas fa-*)

**EXACT FOOTER HTML TO USE (COPY THIS ENTIRELY):**

{footer_html if footer_html else '''
<footer class="bg-zinc-950 border-t border-white/10 py-12">
    <div class="container mx-auto px-4 text-center">
        <p class="text-gray-400 text-sm">© 2024 Company Name. All rights reserved.</p>
    </div>
</footer>
'''}

================================================================================
⚠️ VERIFICATION CHECKLIST BEFORE OUTPUT:
================================================================================

[ ] FAQ section has ALL {faq_html.count('faq-btn') if faq_html else '4'} items
[ ] Each FAQ item has class="faq-btn" and class="faq-answer hidden"
[ ] FAQ JavaScript (accordion toggle) is present in <script>
[ ] Footer HTML is EXACTLY as provided above
[ ] Footer uses Font Awesome icons (not Lucide)
[ ] No FAQ items are missing, truncated, or replaced with placeholders

================================================================================

















🚨🚨🚨 CRITICAL: YOU ARE GENERATING HTML - FOLLOW THESE RULES EXACTLY 🚨🚨🚨

================================================================================
❌ FORBIDDEN - NEVER GENERATE THESE:
================================================================================

1. ❌ NEVER output incomplete tags:
   - </header> without <header>
   - </div> without matching <div>
   - Empty or missing id attributes: id=""

2. ❌ NEVER leave sections empty:
   - page_home MUST have hero section AND features
   - page_shop MUST have product grid
   - page_cart MUST have cart containers

3. ❌ NEVER generate duplicate content:
   - Trust badges appear ONLY ONCE
   - No duplicate feature cards

4. ❌ NEVER output CSS with invalid selectors:
   - WRONG: #.active {{ }}
   - WRONG: .page.active# {{ }}
   - WRONG: #{{{{ }}}}

5. ❌ NEVER omit required elements:
   - MUST have <!DOCTYPE html>
   - MUST have <html> and <body> tags
   - MUST have navigation header
   - MUST have footer







================================================================================
🚨 CRITICAL: FIRST DETECT WHAT TYPE OF WEBSITE TO BUILD 🚨
================================================================================

Read the user's request and determine what type of website they want:

1. DASHBOARD/ADMIN - ONLY if they explicitly say:
   - "dashboard", "admin panel", "analytics dashboard", "KPI dashboard", 
   - "metrics dashboard", "admin interface", "data dashboard"
   
   → Generate: KPI cards, charts, data tables, NO marketing sections

2. SAAS/MARKETING WEBSITE - for everything else like:
   - "SaaS website", "landing page", "pricing page", "startup website",
   - "company website", "business website", "corporate site", "product website"
   
   → Generate: Hero section, features, pricing, testimonials, footer
   → NO KPI cards, NO analytics charts

3. RESTAURANT - "restaurant website", "cafe", "menu", "reservation"

4. E-COMMERCE - "shop", "store", "products", "cart"

================================================================================
RULE: DEFAULT TO MARKETING WEBSITE UNLESS USER EXPLICITLY SAYS "DASHBOARD"
================================================================================

If user says "SaaS website" → Marketing site with hero, features, pricing
If user says "Startup website" → Marketing site with hero, features, CTA
If user says "Business website" → Marketing site with about, services, contact

DO NOT generate dashboard pages (KPI cards, charts) for marketing websites.









## 🚨 CRITICAL: NO REACT SYNTAX IN HTML

You are generating VANILLA HTML, NOT React JSX.

### FORBIDDEN - NEVER use these patterns:

❌ **onError with arrow functions:**
```html
<img onError={{(e) => {{ e.currentTarget.style.display = 'none'; }}}} />















================================================================================
🚨🚨🚨 CRITICAL: USE THIS EXTRACTED HTML CONTENT - DO NOT GENERATE NEW CONTENT 🚨🚨🚨
================================================================================

The extracted content below is the COMPLETE dashboard HTML already rendered for you.
You MUST use this EXACT HTML content for the home page (page_home).

DO NOT generate new KPI cards.
DO NOT generate new charts.
DO NOT create placeholder content.

COPY THIS EXACT HTML INTO THE page_home DIV:

{page_contents.get('page', '')}

================================================================================
FOR page_analytics and page_settings, use the extracted content below.
DO NOT modify or replace with placeholders.
================================================================================











================================================================================
🚨 CRITICAL: FOR DASHBOARD/ANALYTICS PROJECTS - USE CHART.JS, NOT RECHARTS 🚨
================================================================================

When generating dashboard HTML:

1. ❌ DO NOT use React or Recharts
2. ✅ MUST include Chart.js CDN: https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js
3. ✅ MUST initialize charts using new Chart(ctx, {...})
4. ✅ DO NOT use React.createElement or Recharts components

Example of CORRECT chart initialization:
```javascript
const ctx = document.getElementById('revenueChart');
new Chart(ctx, {{
    data: {{ labels: ['Jan', 'Feb', 'Mar'] }}
}})



================================================================================
📊 DASHBOARD WEBSITE - SPECIAL RULES (NO HERO IMAGE, NO FOOTER)
================================================================================

When building a DASHBOARD/ANALYTICS website, you MUST follow these rules:

1. ❌ NO hero section with background image
2. ❌ NO full-screen image backgrounds
3. ❌ NO footer component (dashboard pages don't need footers)
4. ✅ ONLY show KPI cards, charts, and data tables

The home page (Overview) MUST contain:
- Header with title "Overview" and date/time
- KPI cards (Revenue, Users, Orders, Bounce Rate)
- Charts for data visualization
- NO hero image, NO "Get Started" button

Example of CORRECT dashboard home page:
```html
<div class="p-8">
    <div class="flex justify-between items-center mb-8">
        <h1 class="text-3xl font-bold">Overview</h1>
        <p class="text-gray-400">March 15, 2024 2:30 PM</p>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <!-- KPI Cards -->
    </div>
    <!-- Charts -->
</div>

❌ FORBIDDEN - DO NOT generate:

<section class="relative h-screen flex items-center justify-center overflow-hidden">
    <img src="..." class="absolute inset-0 w-full h-full object-cover" />
    <div class="absolute inset-0 bg-black/50"></div>
    <div class="relative z-10 text-center">
        <h1>Hero Title</h1>
        <button>Get Started</button>
    </div>
</section>
<footer>...</footer>
================================================================================








IMPORTANT - THIS IS A ANALYTIC DASHBOARD, NOT A MARKETING SITE. FOLLOW THESE STRICT RULES:
1. ❌ NO hero section with background image
2. ❌ NO full-screen image backgrounds
3. ❌ NO "Get Started" buttons
4. ❌ NO trust badges or testimonials
5. ❌ NO footer (dashboard pages don't need footers)
6. ❌ NO shop, cart, catalog, products, or e-commerce pages
7. ❌ NO restaurant features, reservation modal, menu pages
8. ✅ ONLY create these pages:
    - page_home (Dashboard Overview with KPI cards and charts)
    - page_analytics (Analytics page with metrics)
    - page_settings (Settings page with preferences)
9. ✅ Navigation MUST ONLY contain:
    - Overview (links to page_home)
    - Analytics (links to page_analytics)
    - Settings (links to page_settings)
10. ✅ The Overview page MUST contain:
    - Header with title "Overview" and date/time
    - KPI cards (Revenue, Users, Orders, Bounce Rate)
    - Charts for data visualization
    - Recent activity feed
11. ✅ For charts, use Chart.js CDN:
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>






























Convert this Next.js page to HTML. RENDER ALL .map() arrays into ACTUAL HTML elements.

CRITICAL - DO NOT output .map() in the HTML:

❌ WRONG: {{[1,2,3,4].map(i => <div>Feature {{i}}</div>)}}
✅ CORRECT: <div>Feature 1</div><div>Feature 2</div><div>Feature 3</div><div>Feature 4</div>

❌ WRONG: {{faqs.map(f => <div>{{f.q}}</div>)}}
✅ CORRECT: Render all 4 FAQ items as individual divs with their actual text


REQUIRED OUTPUT:
1. ALL 4 feature cards as individual HTML divs
2. ALL 4 FAQ items with working accordion (click to show/hide answer)
3. Convert icons to Font Awesome or Lucide HTML
4. Add FAQ JavaScript for toggle functionality
5. Complete HTML with Tailwind CDN








PRESERVE ALL content from the source:
   - Hero section (image, heading, text, buttons)
   - ALL trust badges at bottom of hero
   - ALL feature cards (every single one)
   - ALL FAQ items (every question and answer)
   - ALL sections in the exact order
5. DO NOT add extra pages or sections
6. ONLY render page_home from the code below







🚨🚨🚨 CRITICAL: NO REACT SYNTAX IN HTML OUTPUT 🚨🚨🚨

You are generating VANILLA HTML, NOT React JSX.

FORBIDDEN patterns (NEVER output these):

| React/JSX (WRONG) | Vanilla HTML (CORRECT) |
|-------------------|------------------------|
| style={{ background: 'red' }} | style="background: red" |
| onClick={{() => handleClick()}} | onclick="handleClick()" |
| onSubmit={{handleSubmit}} | onsubmit="handleSubmit(event)" |
| value={{formData.name}} | id="fieldName" (get value with JS) |
| {{condition && <div>...</div>}} | Show/hide with CSS/JS |
| disabled={{isSubmitting}} | disabled (with JS toggle) |
| onChange={{handleChange}} | onchange="updateValue(this)" |
| className="btn" | class="btn" |
| <img onError={{(e) => ...}} /> | <img onerror="this.style.display='none'" /> |
| <div style={{ WebkitBackgroundClip: 'text' }}> | <div class="gradient-text"> |
| {{items.map(item => <div>{{item}}</div>)}} | Write actual HTML for each item |

ALWAYS use:
- Regular HTML attributes (style="...", class="...", id="...")
- String event handlers (onclick="myFunction()", onsubmit="return validate()")
- JavaScript functions defined in <script> tags
- CSS classes for reusable styles (like .gradient-text)
- Static HTML - no curly braces {{}} in the output

REMEMBER: The output must work in a browser WITHOUT React loaded.


REQUIRED patterns (ALWAYS use these):
- style="color: red; background: blue"
- onclick="myFunction()"
- onsubmit="return validateForm(event)"
- id="fieldName" (then get value with document.getElementById)
- Show/hide with classList.toggle() or style.display





================================================================================
🚨🚨🚨 CRITICAL: RESERVATIONS PAGE - MANDATORY REQUIREMENTS 🚨🚨🚨
================================================================================

When building a RESTAURANT website, the reservations page (app/reservations/page.tsx) is MANDATORY and MUST contain ALL of the following:

================================================================================
✅ MANDATORY ELEMENTS - NO EXCEPTIONS:
================================================================================

1. ▶️ Hero Section with:
   - Calendar icon badge saying "Reserve Your Table"
   - "Book a Table" heading with amber/orange gradient
   - Description text

2. ▶️ LEFT COLUMN - 4 INFO CARDS (ALL REQUIRED):
   - Card 1: Opening Hours (Clock icon, Mon-Thu 5-10PM, Fri-Sat 5-11PM, Sun 4-9PM)
   - Card 2: Location (MapPin icon, address, valet parking note)
   - Card 3: Contact (Phone and Mail icons, phone number, email)
   - Card 4: Private Dining (Users icon, description, email link)

3. ▶️ RIGHT COLUMN - COMPLETE FORM with ALL 8 FIELDS:
   - Full Name (text input, id="reservationName", required)
   - Email Address (email input, id="reservationEmail", required)
   - Date (date picker, id="reservationDateSelect", required, min=today)
   - Time (select dropdown, id="reservationTimeSelect", required, with 10 options: 5:00 PM to 9:30 PM)
   - Number of Guests (select dropdown, id="reservationGuestsSelect", required, 1-12 options)
   - Occasion (select dropdown, id="reservationOccasion", 7 options: Dinner, Birthday, Anniversary, Date Night, Business, Family, Other)
   - Phone Number (tel input, id="reservationPhone")
   - Special Requests (textarea, id="reservationRequests")

4. ▶️ CANCELLATION POLICY CARD:
   - Info icon
   - Text: "Free cancellation up to 2 hours before your reservation. Late cancellations incur a $25/person fee. No-shows are charged the full meal price."

5. ▶️ SUBMIT BUTTON:
   - Amber/orange gradient background
   - Loading spinner when submitting
   - "Confirm Reservation" text

6. ▶️ SUCCESS MODAL:
   - Green checkmark icon
   - "Table Reserved! 🎉" heading
   - Details card showing: Guest, Date, Time, Guests, Occasion
   - Confirmation email line
   - "Wonderful!" button to close











================================================================================
🚨🚨🚨 CRITICAL: THIS IS A DASHBOARD/ANALYTICS PROJECT 🚨🚨🚨
================================================================================

Based on the source code, this is an ANALYTICS DASHBOARD website.

ABSOLUTE RULES - YOU MUST FOLLOW:
1. ❌ NO shop page, NO cart page, NO catalog page
2. ❌ NO hero section with background image
3. ❌ NO restaurant features, NO reservation modal
4. ❌ NO "Get Started" buttons
5. ✅ ONLY KPI cards (Revenue, Users, Orders, Bounce Rate)
6. ✅ ONLY charts using recharts
7. ✅ ONLY pages: Overview (home), Analytics, Settings

The user's source code contains:
- kpiData array
- Recharts imports (LineChart, BarChart, PieChart)
- Dashboard layout with grid of KPI cards

YOUR OUTPUT MUST MATCH THE SOURCE CODE STRUCTURE.
DO NOT add e-commerce or restaurant features.
DO NOT add hero sections or call-to-action buttons.

================================================================================













# ========== DASHBOARD-SPECIFIC PROMPT INSTRUCTION ==========

================================================================================
📊 DASHBOARD WEBSITE - HTML GENERATION INSTRUCTIONS
================================================================================

When the user requests a DASHBOARD, ANALYTICS, or ADMIN website, you MUST generate:

1. PAGE STRUCTURE (3 pages only):
   - page_home (Dashboard Overview with KPI cards and charts)
   - page_analytics (Analytics with date picker and advanced metrics)
   - page_settings (Settings with user preferences)

2. NAVIGATION (3 links only):
   - Overview (links to page_home)
   - Analytics (links to page_analytics)
   - Settings (links to page_settings)

3. DO NOT generate: shop, cart, catalog, products, menu, reservations, gallery

4. The Overview page MUST include:
   - KPI cards (Revenue, Users, Orders, Page Views)
   - Line chart for revenue trends using recharts
   - Bar chart for user growth
   - Recent activity feed

5. Use recharts library for charts: import {{ LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer }} from 'recharts'

================================================================================



























================================================================================
MENU PAGE (app/menu/page.tsx) - PRESERVATION RULES
================================================================================

When generating the menu page HTML from the extracted source, you MUST preserve ALL of these elements:

1. ✅ Hero section with badge, title, description, and decorative elements
2. ✅ Category filter buttons (Appetizers, Mains, Desserts, Drinks) - ALL categories must be present
3. ✅ ALL menu items from the source - do NOT skip any items
4. ✅ For EACH menu item preserve:
   - Item name
   - Description
   - Price
   - Dietary icons (GF, V, etc.) with proper colors
   - Icon/image placeholder
5. ✅ The layout MUST be grid md:grid-cols-2 gap-8
6. ✅ Image modal functionality with smooth animation

❌ FORBIDDEN - DO NOT:
   - Skip any menu items
   - Combine multiple categories into one
   - Remove dietary icons
   - Simplify the grid layout
   - Remove the image modal

The menu page from the source has approximately 14-20 menu items across 4 categories. ALL of them MUST appear in the final HTML.
================================================================================








================================================================================
🚨🚨🚨 RESERVATIONS PAGE - COMPLETE CONTENT REQUIREMENT 🚨🚨🚨
================================================================================

When generating the HTML preview, the reservations page MUST contain ALL of these elements EXACTLY as shown in the source:

1. ✅ Hero section with badge, title, description
2. ✅ Left column with 4 COMPLETE info cards:
   - Opening Hours (with Clock icon, Mon-Thu 5-10PM, Fri-Sat 5-11PM, Sun 4-9PM)
   - Location (with MapPin icon, address, valet parking note)
   - Contact (with Phone and Mail icons, phone number, email)
   - Private Dining (with Users icon, description, email link)
3. ✅ Right column with COMPLETE form containing ALL 8 fields:
   - Full Name (text input, required)
   - Email Address (email input, required)
   - Date (date picker, min=today)
   - Time (select dropdown with 10 options: 5:00 PM to 9:30 PM)
   - Number of Guests (select dropdown with 1-12 options, with warning for 8+)
   - Occasion (select dropdown with 7 options: Dinner, Birthday, Anniversary, Date Night, Business, Family, Other)
   - Phone Number (tel input)
   - Special Requests (textarea)
4. ✅ Cancellation policy card (with Info icon, policy text)
5. ✅ Submit button with loading spinner and amber gradient
6. ✅ Success modal with all booking details

❌ FORBIDDEN - DO NOT simplify or truncate:
   - Do not replace select dropdowns with text inputs
   - Do not remove any of the 4 left column cards
   - Do not remove the cancellation policy
   - Do not reduce the number of form fields

The reservations page from the source has ALL these elements. COPY THEM COMPLETELY.












================================================================================
🚨 CRITICAL: RESERVATIONS PAGE - MUST RENDER COMPLETE FORM 🚨
================================================================================

When generating the HTML preview, the reservations page MUST contain the COMPLETE form with ALL fields from the Next.js source.

DO NOT replace the form with placeholder text like:
- "Booking system integration placeholder"
- "Reservation form integration would appear here"
- "Please contact us to book your table"

The reservations page HTML MUST include:
- A form with id="restaurantBookingForm"
- Input fields with ids: reservationName, reservationEmail, reservationDateSelect, reservationTimeSelect, reservationGuestsSelect, reservationOccasion, reservationPhone, reservationRequests
- A working submit button
- The cancellation policy card
- The left column with info cards (Opening Hours, Location, Contact, Private Dining)

THE RESERVATIONS PAGE IS A CRITICAL PART OF THE RESTAURANT WEBSITE. DO NOT SIMPLIFY IT.
================================================================================











# Always include this in styles to prevent header overlap:

/* CRITICAL: Fix for iframe preview - push hero content below fixed header */
#page_home .relative.z-10 {{
    padding-top: 78px !important;
}}

/* For mobile devices */
@media (max-width: 768px) {{
    #page_home .relative.z-10 {{
        padding-top: 72px !important;
    }}
}}












## 🚨 CRITICAL: PREVENT HEADER OVERLAP - ALWAYS ADD PADDING TOP

The fixed header is 72px tall. To prevent content from being hidden under the header:

### REQUIRED CSS:
Add this to your <style> tag:
```css
#page_home section .hero-content {{
    padding-top: 78px !important;
}}

/* OR add to the hero content div */
.hero-content-padding {{
    padding-top: 78px;
}}



















## THEME REQUIREMENTS (MUST MATCH EXACTLY)

### Colors & Gradients:
- Body background: `linear-gradient(135deg, #0f0f12 0%, #1a1a2e 100%)`
- Primary gradient: `linear-gradient(135deg, #c084fc, #f472b6)` (purple-pink)
- Secondary gradient: `linear-gradient(135deg, #c084fc, #f472b6)` for buttons
- Text gradient: `linear-gradient(135deg, #c084fc, #f472b6)` with `-webkit-background-clip: text`
- Card background: `rgba(255,255,255,0.05)` with `backdrop-filter: blur(10px)`
- Border color: `rgba(255,255,255,0.1)`

### Typography:
- Font family: 'Inter', system-ui, sans-serif
- Body text color: #e2e8f0
- Heading gradient: purple to pink

### Components:

**Navbar:**
- Fixed position, backdrop blur
- Brand: icon + text with gradient
- Nav links: hover purple, active purple background

**Cards:**
- Glass morphism effect
- Border: 1px solid rgba(255,255,255,0.1)
- Border radius: 1rem
- Hover: translateY(-4px) + border purple

**Buttons:**
- Gradient background (purple to pink)
- Border radius: 2rem
- Hover: translateY(-2px) + shadow glow

**Hero Section:**
- Full screen height
- Background image with opacity 0.35 overlay
- Dark overlay: rgba(0,0,0,0.5)
- Content centered

**Scrollbar:**
- Width: 6px
- Track: #1a1a1e
- Thumb: gradient purple to pink














================================================================================
REQUIRED OUTPUT FORMAT:
================================================================================
✅ Pure HTML with <!DOCTYPE html>
✅ CSS styling in <style> tags (Tailwind CDN for utilities)
✅ Pure JavaScript in <script> tags
✅ Regular HTML elements only (div, section, button, etc.)
✅ onclick handlers for interactivity
✅ All content rendered as static HTML (no .map() in output)

================================================================================
CRITICAL: RENDER ARRAYS AS STATIC HTML
================================================================================
If you see React code like:
features.map(feature => <div>{{feature.title}}</div>)

You MUST output:
<div>Feature Title 1</div>
<div>Feature Title 2</div>
<div>Feature Title 3</div>

NO .map() in the final HTML - render EVERY item as actual HTML.

================================================================================
CRITICAL: NO PLACEHOLDER TEXT
================================================================================
Use the EXACT content from the source files below. 
DO NOT write "Coming soon", "Lorem ipsum", or any placeholder text.

================================================================================
PAGES TO RENDER (from Next.js files):
================================================================================
{page_contents_json}

================================================================================
NAVIGATION TO USE:
================================================================================
{nav_links_json}

================================================================================
BRAND NAME:
================================================================================
{brand_name}

================================================================================
HERO IMAGE URL (use this EXACT URL):
================================================================================
{first_image_display}

================================================================================
FOOTER HTML (use this EXACT HTML):
================================================================================
{footer_html if footer_html else '<!-- No footer found -->'}

================================================================================
FAQ CONTENT (use these EXACT questions):
================================================================================
{faq_html if faq_html else '<!-- No FAQ found -->'}

================================================================================
TESTIMONIALS (use these EXACT quotes):
================================================================================
{testimonials_html if testimonials_html else '<!-- No testimonials found -->'}

================================================================================

















================================================================================
✅ REQUIRED: BODY BACKGROUND - MUST USE THIS GRADIENT
================================================================================

ALWAYS use this EXACT gradient for the body background:

background: linear-gradient(135deg, #0f0f12 0%, #1a1a2e 100%);

This creates a rich, dark theme with subtle purple/blue tones.

================================================================================
✅ CORRECT BODY STYLING - COPY THIS EXACTLY:
================================================================================

<style>
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    background: linear-gradient(135deg, #0f0f12 0%, #1a1a2e 100%);
    color: #e2e8f0;
    min-height: 100vh;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}}

header {{
    background: rgba(10, 10, 12, 0.75);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    height: 72px;
}}

.nav-container {{
    max-width: 1280px;
    margin: 0 auto;
    height: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 1.5rem;
}}

.brand {{
    font-size: 1.5rem;
    font-weight: 800;
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
}}

.nav-links {{
    display: flex;
    gap: 1rem;
    align-items: center;
}}

.nav-link {{
    color: #94a3b8;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 0.75rem;
    font-size: 0.875rem;
    font-weight: 500;
    transition: all 0.2s;
}}

.nav-link:hover {{
    color: #ffffff;
    background: rgba(255, 255, 255, 0.05);
}}

.nav-link.active {{
    color: #ffffff;
    background: rgba(139, 92, 246, 0.15);
}}

/* ========== PAGE TRANSITIONS ========== */
.page {{
    display: none;
    min-height: calc(100vh - 72px);
    padding-top: 78px;
}}

.page.active {{
    display: block;
}}

#page_home {{
    padding-top: 78 !important;
}}

/* ========== BUTTONS ========== */
.btn {{
    display: inline-block;
    padding: 0.75rem 1.5rem;
    background: linear-gradient(135deg, #8b5cf6, #ec4899);
    border-radius: 9999px;
    font-weight: 600;
    color: white;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
}}

.btn:hover {{
    opacity: 0.9;
    transform: translateY(-2px);
}}

.add-to-cart-btn {{
    background: linear-gradient(135deg, #8b5cf6, #ec4899);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    font-weight: 600;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
    width: 100%;
}}

.add-to-cart-btn:hover {{
    opacity: 0.9;
    transform: scale(0.98);
}}

/* ========== CARDS ========== */
.card, .product-card {{
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 1rem;
    padding: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s;
}}

.card:hover, .product-card:hover {{
    transform: translateY(-4px);
    border-color: #c084fc;
}}

/* ========== GRADIENT TEXT ========== */
.gradient-text {{
    background: linear-gradient(135deg, #c084fc, #f472b6);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}}

/* ========== CART SIDEBAR ========== */
#cart-sidebar {{
    position: fixed;
    right: -100%;
    top: 0;
    height: 100%;
    width: 100%;
    max-width: 420px;
    background: linear-gradient(135deg, #1e293b, #0f172a);
    box-shadow: -5px 0 30px rgba(0, 0, 0, 0.5);
    z-index: 1000;
    transition: right 0.3s ease;
    display: flex;
    flex-direction: column;
}}

#cart-sidebar.active {{
    right: 0;
}}

/* ========== CART BADGE ========== */
.cart-count-badge {{
    animation: bounceIn 0.3s ease-out;
}}

@keyframes bounceIn {{
    0% {{ transform: scale(0); opacity: 0; }}
    50% {{ transform: scale(1.2); }}
    100% {{ transform: scale(1); opacity: 1; }}
}}

/* ========== TOAST ========== */
#cart-toast {{
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 2rem;
    font-size: 0.875rem;
    z-index: 1001;
    opacity: 0;
    transition: opacity 0.3s;
    pointer-events: none;
}}

#cart-toast.show {{
    opacity: 1;
}}

/* ========== MODALS ========== */
#checkout-modal, #success-modal {{
    animation: fadeIn 0.2s ease-out;
}}

@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
}}

/* ========== RESPONSIVE ========== */
@media (max-width: 768px) {{
    .nav-links {{
        display: none;
    }}
    
    .hamburger {{
        display: flex;
    }}
    
    #cart-sidebar {{
        max-width: 100%;
    }}
}}

/* ========== UTILITIES ========== */
.container {{
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 1.5rem;
}}

.hidden {{
    display: none !important;
}}

.flex {{
    display: flex;
}}

.items-center {{
    align-items: center;
}}

.justify-between {{
    justify-content: space-between;
}}

.gap-2 {{
    gap: 0.5rem;
}}

.gap-4 {{
    gap: 1rem;
}}

.text-center {{
    text-align: center;
}}

.w-full {{
    width: 100%;
}}

.mt-4 {{
    margin-top: 1rem;
}}

.mb-4 {{
    margin-bottom: 1rem;
}}

.p-4 {{
    padding: 1rem;
}}

/* In your <style> tag */
.relative.z-10 {{
    padding-top: max(125px, 12vh) !important;
}}

/* For iframe (small screens) */
@media (max-height: 600px) {{
    .relative.z-10 {{
        padding-top: 15vh !important;
    }}
}}



/* Additional badge margin */
.relative.z-10 .inline-flex.rounded-full {{
    margin-top: 8px;
}}




/* Additional badge margin */
.relative.z-10 .inline-flex.rounded-full {{
    margin-top: 8px;
}}




/* Additional badge margin */
.relative.z-10 .inline-flex.rounded-full {{
    margin-top: 8px;
}}



</style>

================================================================================
✅ HOW TO APPLY:
================================================================================

1. Add the gradient to the <body> tag via CSS
2. Ensure NO solid colors are used for background
3. The gradient MUST be the FIRST style rule for body

================================================================================
✅ EXAMPLE - COMPLETE BODY STYLING:
================================================================================

<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            background: linear-gradient(135deg, #0f0f12 0%, #1a1a2e 100%);
            color: #e2e8f0;
            min-height: 100vh;
            font-family: 'Inter', system-ui, sans-serif;
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    <!-- Your content here -->
</body>
</html>

================================================================================
✅ VERIFICATION:
================================================================================

Before outputting HTML, CONFIRM:
- [ ] body has background: linear-gradient(135deg, #0f0f12 0%, #1a1a2e 100%)
- [ ] No solid black backgrounds exist
- [ ] Gradient creates rich dark theme with purple/blue tones



















## 🚨 CRITICAL: SHOP PAGE PRODUCT ATTRIBUTES - MUST PRESERVE

When generating the shop page HTML, you MUST ensure EVERY "Add to Cart" button has these EXACT attributes:

### REQUIRED ATTRIBUTES FOR EACH PRODUCT BUTTON:

| Attribute | Value | Example |
|-----------|-------|---------|
| `class` | `"add-to-cart-btn"` | `class="add-to-cart-btn"` |
| `data-id` | Unique product ID | `data-id="prod_1"` |
| `data-name` | Product name | `data-name="Premium Hoodie"` |
| `data-price` | Product price as number | `data-price="79.99"` |

### CORRECT BUTTON EXAMPLE:

```html
<button class="add-to-cart-btn" 
        data-id="1" 
        data-name="Premium Hoodie" 
        data-price="79.99">
    Add to Cart
</button>






















================================================================================
🚨🚨🚨 CRITICAL: MODERN PREMIUM NAVIGATION - NO FLOATING 🚨🚨🚨
================================================================================

The navigation MUST use a glass pill container for links - NEVER floating individual links.

================================================================================
✅ CORRECT NAVIGATION STRUCTURE (GROUNDED):
================================================================================
<header>
    <nav class="nav-container">
        <a href="#" class="brand" onclick="handleBrandClick(event)">
            <i data-lucide="cpu" class="w-6 h-6" style="color: #d8a219;"></i>
            <span>{brand_name}</span>
        </a>
        <div class="nav-links">  <!-- ← GLASS PILL CONTAINER -->
            <a href="#" class="nav-link" data-page="features">
                <i data-lucide="sparkles" class="w-4 h-4"></i>
                <span>Features</span>
            </a>
            <a href="#" class="nav-link" data-page="pricing">
                <i data-lucide="credit-card" class="w-4 h-4"></i>
                <span>Pricing</span>
            </a>
        </div>
        <button class="hamburger" id="hamburgerBtn">
            <span></span><span></span><span></span>
        </button>
    </nav>
</header>

================================================================================
❌ WRONG NAVIGATION STRUCTURE (FLOATING):
================================================================================

<header>
    <nav class="flex justify-between">
        <a href="#">Brand</a>
        <div class="flex space-x-2">  <!-- ← NO GLASS CONTAINER -->
            <a href="#">Features</a>   <!-- ← FLOATING INDIVIDUAL LINKS -->
            <a href="#">Pricing</a>
        </div>
    </nav>
</header>






================================================================================
🚨🚨🚨 CRITICAL: NO GAPS BETWEEN NAVIGATION AND HERO 🚨🚨🚨
================================================================================

The hero section MUST touch the navigation bar with ZERO gap.

================================================================================
❌ FORBIDDEN PATTERNS (CAUSE GAPS):
================================================================================

1. NO pt-* classes wrapping hero:
   <div class="pt-20">  ← FORBIDDEN
   <div class="pt-32">  ← FORBIDDEN

2. NO padding-top on .page for home:
   .page {{ padding-top: 78px; }}  ← FORBIDDEN for home

3. NO margin-top on hero section:
   <section class="mt-20">  ← FORBIDDEN

4. NO extra divs with padding:
   <div class="pt-16">  ← FORBIDDEN

================================================================================
✅ REQUIRED CSS (MUST USE EXACTLY):
================================================================================

<style>
/* Pages have NO default padding */
.page {{ 
    display: none; 
    min-height: calc(100vh - 72px); 
    padding-top: 0;  /* ← CRITICAL: MUST BE 0 */
}}

.page.active {{ display: block; }}

/* Home page - ABSOLUTELY NO padding */
#page_home {{ 
    padding-top: 0 !important; 
}}

/* Other pages need padding to clear fixed header */
#page_features, #page_pricing, #page_contact, #page_about {{ 
    padding-top: 78px; 
}}
</style>

================================================================================
✅ REQUIRED HERO STRUCTURE (NO GAPS):
================================================================================

<div id="page_home" class="page active">
    <!-- NO div with pt-* classes here! -->
    <section class="relative h-screen w-full overflow-hidden">
        <img src="[IMAGE_URL]" class="absolute inset-0 w-full h-full object-cover" />
        <div class="absolute inset-0 bg-black/50"></div>
        <div class="relative z-10 flex flex-col items-center justify-center w-full h-full text-center px-4">
            <h1 class="text-5xl md:text-7xl font-bold mb-6" 
                style="color: transparent; -webkit-text-stroke: 2px #d8a219;">
                {brand_name}
            </h1>
            <p class="text-xl text-gray-200 mb-8 max-w-2xl mx-auto">Your tagline</p>
            <button onclick="showPage('features')" class="btn">Get Started</button>
        </div>
    </section>
    <!-- Rest of content sections -->
</div>

================================================================================
✅ COMPLETE CSS THAT PREVENTS GAPS:
================================================================================

<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    
    header {{
        background: rgba(10, 10, 12, 0.75);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 100;
        height: 72px;
    }}
    
    /* CRITICAL: No padding on pages */
    .page {{
        display: none;
        min-height: calc(100vh - 72px);
        padding-top: 0;
    }}
    
    .page.active {{ display: block; }}
    
    /* Home page: NO padding */
    #page_home {{ padding-top: 78 !important; }}
    
    /* Other pages: Add padding to clear header */
    #page_features, #page_pricing, #page_contact, #page_about {{
        padding-top: 78px;
    }}
    
    /* Footer: NO margin */
    footer {{
        margin-top: 0;
    }}
    
    /* In your <style> tag */
.relative.z-10 {{
    padding-top: max(125px, 12vh) !important;
}}

/* For iframe (small screens) */
@media (max-height: 600px) {{
    .relative.z-10 {{
        padding-top: 15vh !important;
    }}
}}
</style>

================================================================================
🚨 VERIFICATION CHECKLIST FOR AI:
================================================================================

Before outputting HTML, VERIFY:
- [ ] .page has padding-top: 78
- [ ] #page_home has padding-top: 78 !important
- [ ] NO <div class="pt-20"> wrapping the hero section
- [ ] NO <div class="pt-32"> anywhere in page_home
- [ ] Hero section uses class="relative h-screen w-full overflow-hidden"
- [ ] Hero has dark overlay: <div class="absolute inset-0 bg-black/50"></div>
- [ ] Footer has NO mt-* class
- [ ] Non-home pages have padding-top: 78px

================================================================================
🔧 AUTO-FIX IF GAPS ARE DETECTED:
================================================================================

If you see any of these patterns, REMOVE THEM:
- pt-20, pt-32, pt-16, pt-24, mt-20, mt-32
- padding-top: 78px in .page (change to 0)
- Missing #page_home rule

================================================================================









================================================================================
✅ CORRECT FOOTER HTML (NO GAP):
================================================================================

<!-- GOOD - NO mt-20, NO margin-top -->
<footer class="py-12 border-t border-white/10 bg-zinc-950 text-center">
    <p>© 2026 Company Name</p>
</footer>

❌ WRONG - CREATES GAP:
<footer class="py-12 border-t border-white/10 bg-zinc-950 text-center mt-20">







================================================================================
🚨 HERO H1 HEADING - MUST USE EXACT STYLING 🚨
================================================================================

The main hero heading H1 MUST use this EXACT styling:

<h1 class="text-5xl md:text-7xl font-bold mb-6" 
    style="color: transparent; -webkit-text-stroke: 2px #d8a219; text-stroke: 2px #d8a219;">
    {project_name}
</h1>

RULES:
1. Text color: transparent (creates outline effect)
2. Outline stroke: 2px solid #d8a219 (golden color)
3. Font size: text-5xl on mobile, text-7xl on desktop
4. Font weight: bold
5. Margin bottom: mb-6

OPTIONAL: Add animation for subtle glow effect
<h1 class="text-5xl md:text-7xl font-bold mb-6 animate-glow" 
    style="color: transparent; -webkit-text-stroke: 2px #d8a219; text-stroke: 2px #d8a219;">
    {project_name}
</h1>

================================================================================
🚨 CSS FOR GLOW ANIMATION (OPTIONAL) 🚨
================================================================================

<style>
@keyframes glowPulse {{
    0% {{ text-shadow: 0 0 0px rgba(216, 162, 25, 0); }}
    50% {{ text-shadow: 0 0 20px rgba(216, 162, 25, 0.5); }}
    100% {{ text-shadow: 0 0 0px rgba(216, 162, 25, 0); }}
}}

.animate-glow {{
    animation: glowPulse 3s ease-in-out infinite;
}}
</style>

================================================================================
🚨 EXAMPLE - COMPLETE HERO SECTION 🚨
================================================================================

<section class="relative h-screen flex items-center justify-center overflow-hidden">
    <img src="[IMAGE_URL]" class="absolute inset-0 w-full h-full object-cover" />
    <div class="absolute inset-0 bg-black/50"></div>
    <div class="relative z-10 flex flex-col items-center justify-center w-full h-full text-center px-4">
        <h1 class="text-5xl md:text-7xl font-bold mb-6" 
            style="color: transparent; -webkit-text-stroke: 2px #d8a219; text-stroke: 2px #d8a219;">
            {project_name}
        </h1>
        <p class="text-xl text-gray-200 mb-8 max-w-2xl mx-auto">Your tagline here</p>
        <button onclick="showPage('features')" class="px-8 py-3 bg-gradient-to-r from-amber-500 to-yellow-600 rounded-full font-bold text-white hover:opacity-90 transition">
            Get Started
        </button>
    </div>
</section>

================================================================================













================================================================================
🚨 BRAND STYLING - MUST USE EXACTLY THIS 🚨
================================================================================

The brand/logo MUST use this EXACT structure:

<a href="#" class="brand flex items-center gap-2 group" onclick="handleBrandClick(event); return false;">
    <i data-lucide="[ICON_NAME]" class="w-8 h-8" style="color: #d8a219;"></i>
    <span class="text-white text-xl font-bold">{brand_name}</span>
</a>

RULES:
- Icon color: #d8a219 (golden) using inline style
- Brand name: white text with text-xl font-bold
- Icon size: w-8 h-8
- No gradient on brand name (keep it white)

================================================================================






================================================================================
🚨 PREMIUM NAVIGATION STYLES - MUST USE EXACTLY 🚨
================================================================================

Use these EXACT CSS classes for navigation styling:

<style>
/* Premium Sidebar Navigation Styles */
.nav-links {{
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    align-items: stretch;
    padding: 0 0.75rem;
}}

.nav-link {{
    position: relative;
    color: #94a3b8;
    text-decoration: none;
    padding: 0.7rem 1rem;
    border-radius: 0.75rem;
    font-size: 0.875rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 12px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid transparent;
}}

/* Hover State - subtle lift and glow */
.nav-link:hover {{
    color: #ffffff;
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.08);
    transform: translateX(4px);
}}

/* Active State - Premium look */
.nav-link.active {{
    color: #ffffff;
    background: linear-gradient(90deg, rgba(139, 92, 246, 0.15) 0%, rgba(139, 92, 246, 0.05) 100%);
    border-color: rgba(139, 92, 246, 0.3);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}}

/* Vertical indicator pill for active link */
.nav-link.active::before {{
    content: "";
    position: absolute;
    left: -4px;
    height: 60%;
    width: 3px;
    background: #8b5cf6;
    border-radius: 99px;
    box-shadow: 0 0 10px #8b5cf6;
}}

/* Desktop navigation - horizontal layout */
@media (min-width: 769px) {{
    .nav-links {{
        flex-direction: row;
        gap: 0.5rem;
        padding: 0;
    }}
    
    .nav-link:hover {{
        transform: translateY(-2px);
    }}
    
    .nav-link.active::before {{
        bottom: -4px;
        left: 50%;
        transform: translateX(-50%);
        top: auto;
        height: 3px;
        width: 60%;
    }}
}}

/* In your <style> tag */
.relative.z-10 {{
    padding-top: max(125px, 12vh) !important;
}}

/* For iframe (small screens) */
@media (max-height: 600px) {{
    .relative.z-10 {{
        padding-top: 15vh !important;
    }}
}}
</style>
















⚠️⚠️⚠️ CRITICAL HTML RULES - MUST FOLLOW ⚠️⚠️⚠️
================================================================================

1. CSS RULES: Always use {{ }} braces
   ✅ .page {{ display: none; }}
   ❌ .page 

2. HERO SECTION: Must be centered with overlay
   ✅ <section class="relative h-screen w-full overflow-hidden">
        <img class="absolute inset-0 w-full h-full object-cover" />
        <div class="absolute inset-0 bg-black/50"></div>
        <div class="relative z-10 flex flex-col items-center justify-center w-full h-full text-center px-4">
          <h1>Title</h1>
        </div>
      </section>
   ❌ Missing overlay or flex centering

3. HOME PAGE: No padding-top
   ✅ #page_home {{ padding-top: 78 !important; }}
   ❌ .page {{ padding-top: 78px; }} (affects home)

4. NO JSX: Convert all .map() to actual HTML
   ❌ {{features.map(f => <div>{{f.title}}</div>)}}
   ✅ <div><h3>Feature 1</h3></div><div><h3>Feature 2</h3></div>

5. NO onError JSX:
   ❌ onError={{ (e) => ... }}
   ✅ onerror="this.style.display='none'"

================================================================================






## 🚨 CRITICAL: DO NOT GENERATE DUPLICATE CART SYSTEMS

You MUST NOT generate any cart-related JavaScript that includes:
- `let items = []`
- `let totalItems = 0`
- `function addToCart(product) 
- Custom cart functions that duplicate the master system

The MASTER CART SYSTEM will be injected automatically by the backend.
Your job is ONLY to generate:
1. app/shop/page.tsx - with add-to-cart buttons (class="add-to-cart-btn", data-id, data-name, data-price)
2. app/cart/page.tsx - with empty containers (#cart-items-list, #cart-summary, etc.)

DO NOT generate cart JavaScript. DO NOT generate duplicate cart functions.









================================================================================
🚨 CRITICAL: USE EXACT EXTRACTED CONTENT - NO GENERIC PLACEHOLDERS 🚨
================================================================================

The extracted content below is FROM YOUR ACTUAL NEXT.JS FILES.
You MUST use THIS EXACT content. DO NOT generate new content.

EXTRACTED HOME PAGE CONTENT (USE THIS EXACTLY):
{home_content}

EXTRACTED FAQ CONTENT (USE THESE EXACT QUESTIONS AND ANSWERS):
{faq_html}

EXTRACTED FOOTER HTML (USE THIS EXACTLY):
{footer_html}

EXTRACTED TESTIMONIALS (USE THESE EXACTLY):
{testimonials_html}

================================================================================
🚨 NAVIGATION RULES - NO "HOME" BUTTON 🚨
================================================================================

The brand/logo IS the home button. DO NOT add a separate "Home" link.

✅ CORRECT navigation:
<nav>
    <a href="#" class="brand" onclick="handleBrandClick(event)">Brand Name</a>
    <a href="#" data-page="features">Features</a>
    <a href="#" data-page="pricing">Pricing</a>
</nav>

❌ WRONG - DO NOT add:
<a href="#" data-page="home">Home</a>  <!-- NO! Brand is home -->

================================================================================
🚨 FOOTER - MUST INCLUDE EXTRACTED HTML 🚨
================================================================================

You MUST include the EXACT footer HTML from the extraction above.
DO NOT generate a generic footer.

================================================================================
🚨 FAQ - MUST USE EXTRACTED QUESTIONS & ANSWERS 🚨
================================================================================

The FAQ section MUST use the EXACT questions and answers from:
{faq_html}

================================================================================
🚨 HERO SECTION - NO GAP AT TOP 🚨
================================================================================

CSS MUST have:
.page {{ display: none; min-height: calc(100vh - 78px); }}
#page_home {{ padding-top: 0 !important; }}

================================================================================
RETURN ONLY COMPLETE HTML with <!DOCTYPE html>
================================================================================

















================================================================================
📋 GENERAL INSTRUCTION - WHAT TO GENERATE
================================================================================

Based on the source files provided below, generate a COMPLETE HTML preview that:

1. **Preserves ALL content** from the extracted pages exactly as provided
2. **Converts React JSX to HTML** (change className to class, Link to a, etc.)
3. **Includes working navigation** with showPage() function for page switching
4. **Has mobile responsive design** with hamburger menu on smaller screens
5. **Uses dark theme** with purple/pink gradients for modern look

================================================================================
🎨 REQUIRED CSS (ALWAYS INCLUDE)
================================================================================

- Tailwind CSS for utility classes
- Custom styles for navigation, pages, cards, buttons
- Mobile menu styles (hamburger animation, slide-in menu)
- Smooth transitions and hover effects
- Glass morphism effects (backdrop-blur, semi-transparent backgrounds)

================================================================================
🔧 REQUIRED JAVASCRIPT (ALWAYS INCLUDE)
================================================================================

- showPage(pageId) - switches between pages
- handleBrandClick(event) - navigates to home when logo clicked
- Mobile menu toggle functionality
- Lucide icons initialization
- FAQ accordion functionality (if FAQ section exists)
- Scroll to top button (if present)

================================================================================
🛒 CART FUNCTIONALITY (ONLY IF E-COMMERCE DETECTED)
================================================================================

If the source files contain shop and cart pages, INCLUDE:
- Add to Cart buttons with data-id, data-name, data-price attributes
- Cart sidebar (#cart-sidebar)
- Cart toast notifications (#cart-toast)
- Checkout modal (#checkout-modal)
- Success modal (#success-modal)
- Complete cart JavaScript (addToCart, removeFromCart, updateQuantity, etc.)

================================================================================
📄 PAGE STRUCTURE
================================================================================

Create a div for EACH page extracted:
<div id="page_[route_name]" class="page">
    [EXACT CONTENT FROM EXTRACTION - DO NOT MODIFY]
</div>

The home page must be active by default (class="page active")

================================================================================
⚠️ CRITICAL RULES
================================================================================

1. DO NOT add placeholder text - USE THE EXACT extracted content
2. DO NOT add extra pages that don't exist in the source
3. DO NOT modify wording, headings, or button text
4. DO preserve ALL sections (hero, features, testimonials, FAQ, footer)
5. DO make sure navigation links match the actual pages that exist

================================================================================
✅ FINAL VERIFICATION
================================================================================

Before outputting, ensure:
- [ ] Complete HTML document with <!DOCTYPE html>
- [ ] All CSS and JS in one file
- [ ] Navigation matches extracted links
- [ ] All pages have their exact content
- [ ] Mobile menu works
- [ ] Lucide icons are initialized
- [ ] Footer is included

================================================================================
RETURN ONLY COMPLETE HTML starting with <!DOCTYPE html>. NO explanations.
================================================================================
















## CRITICAL: NAVIGATION STRUCTURE - NO "HOME" BUTTON

**The brand/logo IS the home button. There is NO separate "Home" link in the navigation.**

### Dynamic Navigation Template:

```html
<header>
    <nav class="nav-container">
        <!-- Brand/Logo - THIS IS THE HOME LINK -->
        <a href="#" class="brand flex items-center gap-2 group" onclick="handleBrandClick(event); return false;">
            <i data-lucide="[DYNAMIC_ICON]" class="w-8 h-8" style="color: #d8a219;"></i>
            <span class="text-white text-xl font-bold">[BRAND_NAME]</span>
        </a>
        
        <!-- Navigation Links - Dynamically generated from nav_links -->
        <div class="hidden md:flex space-x-2 items-center">
            <!-- For each link in nav_links, generate appropriate HTML -->
            {navigation_html}
        </div>
        
        <!-- Mobile Menu Button -->
        <button id="mobile-menu-button" class="md:hidden p-2 rounded-lg hover:bg-white/10 transition-colors">
            <i data-lucide="menu" class="w-6 h-6" style="color: #d8a219;"></i>
        </button>
    </nav>
    
    <!-- Mobile Menu - Dynamically generated -->
    <div id="mobile-menu" class="hidden md:hidden bg-black/80 backdrop-blur-lg p-4 space-y-2 border-t border-white/10">
        {navigation_html}
    </div>
</header>




## CRITICAL: NAVIGATION CART LINK - MUST HAVE ICON AND CORRECT HREF

The cart link in the navigation MUST use this EXACT structure:

```html
<a href="cart" class="nav-link relative flex items-center gap-2 group" data-page="cart">
    <i data-lucide="shopping-cart" class="w-4 h-4 text-purple-400"></i>
    <span class="text-gray-300 group-hover:text-purple-400">Cart</span>
    <span data-cart-count class="cart-count-badge hidden absolute -top-2 -right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full items-center justify-center px-1 shadow-lg shadow-purple-500/25">0</span>
</a>




## CRITICAL REQUIREMENTS - ADD TO CART BUTTONS

**EVERY Add to Cart button MUST have these 4 things:**

1. **Class name:** `class="add-to-cart-btn"` (NOT "btn", NOT "button", EXACTLY this)
2. **data-id:** `data-id="unique_product_id"` (string, e.g., "prod_001")
3. **data-name:** `data-name="Product Name"` (the product name)
4. **data-price:** `data-price="49.99"` (the price as a number)

**Example of CORRECT Add to Cart button:**
```html
<button class="add-to-cart-btn" data-id="hoodie_001" data-name="Premium Hoodie" data-price="79.99">
    Add to Cart
</button>

Navigation Cart Link - MUST have this exact structure:
<a href="#" class="nav-link relative" data-page="cart">
    Cart
    <span data-cart-count class="cart-count-badge hidden absolute -top-2 -right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full flex items-center justify-center px-1">0</span>
</a>





================================================================================
🚨 CRITICAL: DO NOT GENERATE CART JAVASCRIPT 🚨
================================================================================

The cart JavaScript will be injected automatically by the backend.
DO NOT generate any script that starts with "// ========== CART SYSTEM =========="

If you see this pattern in your output, REMOVE IT:
<script>
// ========== CART SYSTEM ==========
let cart = [];
...
</script>

The backend provides a working cart system. Your job is only to generate:
- app/shop/page.tsx (with add-to-cart buttons)
- app/cart/page.tsx (with empty containers)
- components/Navigation.tsx (with cart link and badge)

DO NOT generate cart JavaScript or cart CSS.








================================================================================
🚨 HTML PREVIEW - ONLY USE PAGES FROM THE NEXT.JS PROJECT 🚨
================================================================================

When generating the HTML preview, you MUST ONLY create page divs for routes that ACTUALLY EXIST in the Next.js project files.

DO NOT create extra pages like:
- catalog (unless app/catalog/page.tsx exists)
- about (unless app/about/page.tsx exists)
- contact (unless app/contact/page.tsx exists)

The navigation should ONLY contain links to pages that exist.

For an e-commerce website, if the Next.js project only has:
- app/page.tsx (home)
- app/shop/page.tsx (shop)
- app/cart/page.tsx (cart)

Then the HTML preview MUST ONLY have:
- page_home
- page_shop
- page_cart

And navigation MUST ONLY have:
- Shop link
- Cart link

DO NOT add a Catalog link or page if it doesn't exist in the source files.






================================================================================
🚨 CART PAGE - CRITICAL ID MATCHING 🚨
================================================================================

The JavaScript `updateCartPage()` function MUST use the EXACT same IDs as the HTML:

✅ HTML:
```html
<div id="cart-items-list"></div>
<div id="empty-cart-message-cart"></div>
<div id="cart-summary"></div>
<span id="cart-total-count"></span>
<span id="cart-page-subtotal"></span>
<span id="cart-page-total"></span>










================================================================================
🚨 NAVIGATION COMPONENT - CRITICAL FIXES 🚨
================================================================================

The Navigation component MUST have:

1. **VISIBLE BRAND NAME** - NEVER hide the brand name with absolute positioning
2. **CART LINK WITH PROPER TEXT** - Show "Cart" text, NOT the item count
3. **SEPARATE CART BADGE** - Item count goes in a badge span, NOT replacing the cart text

================================================================================
FORBIDDEN PATTERNS - NEVER GENERATE:
================================================================================

❌ WRONG - Brand name hidden with absolute positioning:
```tsx
<a href="/" class="brand">
    <i data-lucide="sparkles" class="w-8 h-8"></i>
    <span class="absolute -top-2 -right-2">Brand Name</span> {{/* ← HIDDEN OFF-SCREEN */}}
</a>




================================================================================
CORRECT PATTERNS - ALWAYS GENERATE:
================================================================================

✅ CORRECT - Brand name visible with gradient text:
<a href="/" class="brand flex items-center gap-2 group" onclick="handleBrandClick(event)">
    <i data-lucide="sparkles" class="w-8 h-8 text-purple-500 drop-shadow-lg group-hover:scale-110 transition-all duration-300"></i>
    <span class="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
        Brand Name
    </span>
</a>


✅ CORRECT - Cart link with "Cart" text AND separate badge:

<a href="/cart" class="nav-link relative flex items-center gap-2 group" data-page="cart">
    <i data-lucide="shopping-cart" class="w-4 h-4 text-purple-400 group-hover:text-purple-600 group-hover:scale-110 transition-all duration-300"></i>
    <span class="text-gray-300 group-hover:text-purple-500 transition-colors duration-300">Cart</span>
    <span data-cart-count class="cart-count-badge hidden absolute -top-2 -right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full items-center justify-center px-1 shadow-lg shadow-purple-500/25">
        0
    </span>
</a>


================================================================================
CART BADGE RULES:
================================================================================

The cart badge MUST:

    Have data-cart-count attribute

    Start with hidden class

    Be positioned absolutely (absolute -top-2 -right-2)

    Have badge styling (rounded-full, gradient background)

    Show item count, NOT replace the cart text







================================================================================
🚨🚨🚨 CRITICAL: CART PAGE RENDERING - NO .map() IN FINAL HTML 🚨🚨🚨
================================================================================

When generating the HTML preview for the Cart page, you MUST render ACTUAL HTML elements, NOT the React .map() function.

THE PROBLEM:
❌ WRONG (AI outputs this):
```html
<div id="cart-items-list">
  {{items.map((item) => (
    <div key={{item.id}}>...</div>
  ))}}
</div>

✅ CORRECT (AI must output this):
<div id="cart-items-list">
  <!-- This will be populated dynamically by JavaScript -->
</div>

















================================================================================
HOW THE CART PAGE SHOULD BE STRUCTURED:
================================================================================
The Cart page MUST have:

1. Cart title with item count:
<h1 class="text-3xl font-bold mb-8 gradient-text">Shopping Cart (<span id="cart-total-count">0</span> items)</h1>

2. Empty state container (visible when cart is empty):
<div id="empty-cart-message-cart" class="text-center py-12">
    <i data-lucide="shopping-bag" class="w-20 h-20 text-gray-600 mx-auto mb-6"></i>
    <h2 class="text-2xl font-bold mb-4">Your Cart is Empty</h2>
    <button onclick="showPage('shop')" class="btn">Continue Shopping</button>
</div>

3. Items container (hidden when empty, shown when items exist):
<div id="cart-items-list" class="space-y-4"></div>

4. Order summary with PROCEED TO CHECKOUT BUTTON (hidden when empty):
<div id="cart-summary" class="bg-white/5 rounded-xl p-6 border border-white/10 h-fit hidden">
    <h3 class="text-xl font-bold mb-4 gradient-text">Order Summary</h3>
    
    <div class="space-y-2">
        <div class="flex justify-between">
            <span class="text-gray-400">Subtotal</span>
            <span id="cart-page-subtotal" class="font-semibold">$0.00</span>
        </div>
        <div class="flex justify-between">
            <span class="text-gray-400">Shipping</span>
            <span class="text-green-400">Free</span>
        </div>
    </div>
    
    <div class="border-t border-white/10 my-4"></div>
    
    <div class="flex justify-between font-bold text-lg mb-6">
        <span>Total</span>
        <span id="cart-page-total" class="text-purple-400">$0.00</span>
    </div>
    
    <!-- PROCEED TO CHECKOUT BUTTON - MUST BE INCLUDED -->
    <button onclick="openCheckoutModal()" class="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-semibold text-white hover:opacity-90 transition duration-300">
        Proceed to Checkout →
    </button>
    
    <!-- OPTIONAL: Clear Cart Button -->
    <button onclick="clearCart()" class="w-full mt-3 py-2 text-gray-400 hover:text-white transition text-sm">
        Clear Cart
    </button>
</div>

================================================================================
CRITICAL REQUIREMENTS FOR CART PAGE:
================================================================================

✅ MUST have the "Proceed to Checkout" button inside #cart-summary
✅ MUST have onclick="openCheckoutModal()" on the checkout button
✅ MUST have #cart-total-count for displaying item count
✅ MUST have #cart-page-subtotal and #cart-page-total for totals
✅ MUST have #cart-items-list for dynamic items
✅ MUST have #empty-cart-message-cart for empty state

================================================================================
WHAT THE FINAL CART PAGE HTML SHOULD LOOK LIKE:
================================================================================

<div id="page_cart" class="page">
    <div class="min-h-screen pt-24 container mx-auto px-4">
        <h1 class="text-3xl font-bold mb-8 gradient-text">Shopping Cart (<span id="cart-total-count">0</span> items)</h1>
        
        <div class="lg:grid lg:grid-cols-3 lg:gap-8">
            
            <!-- Left: Cart Items -->
            <div class="lg:col-span-2">
                <div id="cart-items-list" class="space-y-4">
                    <!-- Cart items injected here by JavaScript -->
                </div>
                
                <div id="empty-cart-message-cart" class="text-center py-12">
                    <i data-lucide="shopping-bag" class="w-20 h-20 text-gray-600 mx-auto mb-6"></i>
                    <h2 class="text-2xl font-bold mb-4">Your Cart is Empty</h2>
                    <button onclick="showPage('shop')" class="btn">Continue Shopping</button>
                </div>
            </div>
            
            <!-- Right: Order Summary -->
            <div class="lg:col-span-1 mt-8 lg:mt-0">
                <div id="cart-summary" class="bg-white/5 rounded-xl p-6 border border-white/10 h-fit hidden">
                    <h3 class="text-xl font-bold mb-4 gradient-text">Order Summary</h3>
                    
                    <div class="space-y-2">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Subtotal</span>
                            <span id="cart-page-subtotal" class="font-semibold">$0.00</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Shipping</span>
                            <span class="text-green-400">Free</span>
                        </div>
                    </div>
                    
                    <div class="border-t border-white/10 my-4"></div>
                    
                    <div class="flex justify-between font-bold text-lg mb-6">
                        <span>Total</span>
                        <span id="cart-page-total" class="text-purple-400">$0.00</span>
                    </div>
                    
                    <button onclick="openCheckoutModal()" class="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-semibold text-white hover:opacity-90 transition duration-300">
                        Proceed to Checkout →
                    </button>
                    
                    <button onclick="clearCart()" class="w-full mt-3 py-2 text-gray-400 hover:text-white transition text-sm">
                        Clear Cart
                    </button>
                </div>
            </div>
            
        </div>
    </div>
</div>

================================================================================
VERIFICATION CHECKLIST:
================================================================================

✅ Cart page has NO .map() in the HTML
✅ Cart page has <div id="cart-items-list"> (empty container, JS injects items)
✅ Cart page has <div id="empty-cart-message-cart"> (empty state message)
✅ Cart page has <div id="cart-summary"> (order summary, hidden by default)
✅ Cart page has <button onclick="openCheckoutModal()"> (Proceed to Checkout)
✅ Cart page has <span id="cart-total-count"> (item count in title)
✅ Cart page has <span id="cart-page-subtotal"> (subtotal value)
✅ Cart page has <span id="cart-page-total"> (total value)
✅ Cart page uses lg:grid lg:grid-cols-3 layout (items left, summary right)
✅ Cart page has NO hardcoded cart items — JavaScript renders all items
✅ Cart page has NO checkout form — checkout is always a modal
✅ JavaScript has updateCartPage() function
✅ JavaScript has openCheckoutModal() function
✅ JavaScript has processPayment() function
✅ JavaScript has clearCart() function
✅ updateCartPage() is called inside saveCart() and on page load
✅ updateCartPage() updates #cart-total-count, #cart-page-subtotal, #cart-page-total
✅ updateCartPage() toggles hidden class on #cart-summary and #empty-cart-message-cart




























================================================================================
SUMMARY - WHAT THE AI MUST DO:
================================================================================

# ❌ DO NOT output {{items.map(...)}} in the HTML

✅ Output empty containers with IDs: #empty-cart-message-cart, #cart-items-list, #cart-summary

✅ Output #cart-total-count for displaying item count

✅ Output #cart-page-subtotal and #cart-page-total for totals

✅ Ensure the JavaScript updateCartPage() function exists in the page

✅ Call updateCartPage() on page load and whenever cart changes

================================================================================
VERIFICATION CHECKLIST:
================================================================================

Cart page has NO .map() in the HTML

Cart page has <div id="cart-items-list"> (empty container)

Cart page has <div id="empty-cart-message-cart"> (empty state)

Cart page has <div id="cart-summary"> (order summary)

Cart page has <span id="cart-total-count"> (item count)

JavaScript has updateCartPage() function

updateCartPage() is called in saveCart() and on page load
























================================================================================
🚨 SHOP PAGE RENDERING - CRITICAL 🚨
================================================================================

When you see a shop page with `products.map(p => (...))`, you MUST:

1. Extract the products array from the code
2. Render EACH product as an individual HTML div
3. DO NOT output `.map()` in the final HTML



Example products array in code:
```javascript
const products = [
  {{ id: "1", name: "Premium Hoodie", price: 49.99 }},
  {{ id: "2", name: "Scholar Tee", price: 29.99 }},
  {{ id: "3", name: "Leather Notebook", price: 19.99 }},
  {{ id: "4", name: "Canvas Tote", price: 24.99 }},
  {{ id: "5", name: "Ceramic Mug", price: 15.99 }},
  {{ id: "6", name: "Varsity Jacket", price: 89.99 }}
];


MUST OUTPUT (all 6 products as separate HTML):

<div class="grid md:grid-cols-3 gap-8">
    <!-- Product 1 -->
    <div class="p-6 bg-white/5 rounded-xl">
        <h3 class="text-xl font-bold">Premium Hoodie</h3>
        <p class="text-purple-400">$49.99</p>
        <button class="add-to-cart-btn mt-4 px-4 py-2 bg-purple-600 rounded" data-id="1" data-name="Premium Hoodie" data-price="49.99">Add to Cart</button>
    </div>
    <!-- Product 2 -->
    <div class="p-6 bg-white/5 rounded-xl">
        <h3 class="text-xl font-bold">Scholar Tee</h3>
        <p class="text-purple-400">$29.99</p>
        <button class="add-to-cart-btn mt-4 px-4 py-2 bg-purple-600 rounded" data-id="2" data-name="Scholar Tee" data-price="29.99">Add to Cart</button>
    </div>
    <!-- Continue for products 3-6 -->
</div>


CRITICAL:

ALL 6 products MUST be rendered

Each product button MUST have correct data-id, data-name, data-price

NO .map() in the final HTML













================================================================================
PRODUCTS DATA FOR SHOP PAGE (USE THESE EXACT VALUES):
================================================================================
{products_data}

Render ALL products from this array as individual HTML elements.
DO NOT use .map() in the output - write each product div manually.
================================================================================


















================================================================================
PRODUCT CARD FORMAT FOR SHOP PAGE:
================================================================================

When generating shop page products, use this EXACT format for Add to Cart buttons:

<div class="product-card">
    <div class="product-image">
        <i data-lucide="shopping-bag" class="w-16 h-16 text-purple-400"></i>
    </div>
    <div class="product-info">
        <h3 class="product-title">Product Name</h3>
        <p class="product-price">$49.99</p>
        <button class="add-to-cart-btn" 
                data-id="prod_unique_id" 
                data-name="Product Name" 
                data-price="49.99">
            Add to Cart
        </button>
    </div>
</div>

CRITICAL: Every product button MUST have:
- class="add-to-cart-btn"
- data-id (unique for each product)
- data-name (product name)
- data-price (product price as number)

================================================================================
CART BADGE IN NAVIGATION:
================================================================================

Add this to your cart navigation link:

<a href="#" class="nav-link relative" data-page="cart">
    <i data-lucide="shopping-cart" class="w-4 h-4"></i>
    Cart
    <span data-cart-count class="cart-count-badge hidden absolute -top-2 -right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full items-center justify-center px-1">0</span>
</a>








================================================================================
🚨 AI INSTRUCTION: HANDLING NAVIGATION LINKS WITH ICONS 🚨
================================================================================

When you see navigation links with icons inside the Link component, you MUST:

1. Extract BOTH the href and the text label
2. Preserve the icon by converting it to HTML
3. ONLY add icons to E-COMMERCE links (Shop, Catalog, Cart, Products, Store, Basket, Checkout)
4. Keep OTHER links (About, Contact, Projects, Services, Blog, etc.) as TEXT-ONLY

================================================================================
PATTERNS TO RECOGNIZE:
================================================================================

React pattern for E-COMMERCE links (WITH icon):
```jsx
<Link href="/cart" className="flex items-center gap-2">
    <ShoppingBag className="w-5 h-5" /> Cart
</Link>

HTML output MUST be:
<a href="/cart" class="nav-link flex items-center gap-2 group" data-page="cart">
    <i data-lucide="shopping-bag" class="w-4 h-4 text-purple-400 group-hover:text-pink-500 group-hover:scale-110 transition-all duration-300"></i>
    <span class="text-gray-300 group-hover:text-purple-400 transition-colors duration-300">Cart</span>
</a>



================================================================================
ICON MAPPING FOR NAVIGATION LINKS:
================================================================================

- ShoppingBag → shopping-bag

















================================================================================
🚨 FAQ SECTION - USE THIS EXACT HTML (DO NOT MODIFY) 🚨
================================================================================

The following FAQ HTML has been pre-built from your source file.
You MUST include this EXACT HTML in the FAQ section.

{faq_html}

DO NOT generate new FAQ items. DO NOT add or remove any questions.
Simply place this HTML inside the FAQ section div.
================================================================================














================================================================================
CRITICAL: YOU MUST USE THE EXACT CONTENT BELOW FOR EACH PAGE
================================================================================

{pages_section}

================================================================================
NOW GENERATE THE HTML PREVIEW USING THE EXACT CONTENT ABOVE
================================================================================

For EACH page in the extraction above, create:
<div id="page_{route}" class="page">
    <div class="container mx-auto px-4 py-20">
        [PASTE THE EXACT CONTENT FROM THE PAGE EXTRACTION ABOVE - DO NOT MODIFY]
    </div>
</div>

DO NOT write "Welcome to our about page" or any other placeholder text.
USE THE EXACT CONTENT PROVIDED ABOVE.
================================================================================



















================================================================================
🚨 NAVIGATION STYLING REQUIREMENTS - MUST INCLUDE EXACT CLASSES 🚨
================================================================================

When generating navigation HTML, you MUST include these exact classes for the brand icon:

BRAND ICON REQUIREMENTS:
- MUST have: class="w-6 h-6 text-yellow-400 drop-shadow-lg group-hover:scale-110 transition-all duration-300"
- MUST have: data-lucide="[THE_ICON_NAME_EXTRACTED_FROM_SOURCE]" 
- MUST be wrapped in: <a class="brand flex items-center gap-2 group">

EXAMPLE - CORRECT BRAND HTML:
```html
<a href="/" class="brand flex items-center gap-2 group" onclick="handleBrandClick(event)">
    <i data-lucide="sparkles" class="w-6 h-6 text-yellow-400 drop-shadow-lg group-hover:scale-110 transition-all duration-300"></i>
    <span class="text-xl font-bold bg-gradient-to-r from-yellow-400 to-purple-500 bg-clip-text text-transparent">Brand Name</span>
</a>






================================================================================
🚨🚨🚨 ABSOLUTE REQUIREMENT - YOU MUST INCLUDE THIS EXACT CSS 🚨🚨🚨
================================================================================

FAILURE TO INCLUDE THE CSS BELOW WILL CAUSE THE PREVIEW TO BREAK.

YOU HAVE NO CHOICE. YOU MUST COPY AND PASTE THIS EXACT CSS INTO YOUR <style> TAG.

DO NOT MODIFY IT.
DO NOT SIMPLIFY IT.
DO NOT WRITE YOUR OWN CSS.
DO NOT OMIT ANY PART OF IT.

================================================================================
MANDATORY CSS - COPY THIS EXACTLY:
================================================================================
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Inter', system-ui, sans-serif; 
    background: linear-gradient(135deg, #0a0a0c 0%, #2d1b4e 100%); 
    color: #f8fafc; 
    min-height: 100vh;}}



header {{
    /* 1. Use a slightly more transparent background to let the blur shine */
    background: rgba(10, 10, 12, 0.75); 
    
    /* 2. Standard and Safari-specific blur */
    backdrop-filter: blur(12px) saturate(180%);
    -webkit-backdrop-filter: blur(12px) saturate(180%);
    
    /* 3. High-definition border */
    border-bottom: 1px solid rgba(255, 255, 255, 0.08); 
    
    /* 4. Layout & Positioning */
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    height: 72px;
    
    /* 5. Smooth transition for scroll effects */
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}





header::after {{
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, transparent, #c084fc, #f472b6, transparent);
    opacity: 0.3;
}}





.nav-container {{ max-width: 1280px; margin: 0 auto; height: 100%; display: flex; justify-content: space-between; align-items: center; padding: 0 1.5rem; }}
.brand {{ font-size: 1.5rem; font-weight: 800; text-decoration: none; background: linear-gradient(135deg, #c084fc, #f472b6); -webkit-background-clip: text; background-clip: text; color: transparent; display: flex; align-items: center; gap: 0.5rem; cursor: pointer; }}







.nav-links {{
    display: flex;
    flex-direction: column; /* Stacked for sidebar layout */
    gap: 0.4rem;
    align-items: stretch; /* Fills the width of the sidebar */
    padding: 0 0.75rem;
}}

.nav-link {{
    position: relative;
    color: #94a3b8; /* Slightly softer blue-gray */
    text-decoration: none;
    padding: 0.7rem 1rem;
    border-radius: 0.75rem;
    font-size: 0.875rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 12px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid transparent;
}}

/* Hover State: Suble lift and glow */
.nav-link:hover {{
    color: #ffffff;
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.08);
    transform: translateX(4px); /* Slight slide-in effect */
}}

/* Active State: The "Premium" look */
.nav-link.active {{
    color: #ffffff;
    background: linear-gradient(
        90deg, 
        rgba(139, 92, 246, 0.15) 0%, 
        rgba(139, 92, 246, 0.05) 100%
    );
    border-color: rgba(139, 92, 246, 0.3);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}}

/* The vertical indicator pill for the active link */
.nav-link.active::before {{
    content: "";
    position: absolute;
    left: -4px;
    height: 60%;
    width: 3px;
    background: #8b5cf6;
    border-radius: 99px;
    box-shadow: 0 0 10px #8b5cf6;
}}







.hamburger {{ display: none; flex-direction: column; gap: 4px; background: transparent; border: none; cursor: pointer; padding: 0.5rem; }}
.hamburger span {{ width: 25px; height: 3px; background: #9ca3af; border-radius: 2px; transition: all 0.3s ease; }}
.hamburger.active span:nth-child(1) {{ transform: rotate(45deg) translate(5px, 5px); }}
.hamburger.active span:nth-child(2) {{ opacity: 0; }}
.hamburger.active span:nth-child(3) {{ transform: rotate(-45deg) translate(5px, -5px); }}

.mobile-menu {{ position: fixed; top: 72px; right: -100%; width: 280px; height: calc(100vh - 72px); background: #1a1a1e; z-index: 200; transition: right 0.3s ease; padding: 24px; border-left: 1px solid rgba(255,255,255,0.1); }}
.mobile-menu.active {{ right: 0; }}
.mobile-overlay {{ position: fixed; top: 72px; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 199; display: none; }}
.mobile-overlay.active {{ display: block; }}
.mobile-nav-link {{ display: block; padding: 12px 16px; color: #9ca3af; text-decoration: none; border-radius: 0.5rem; margin-bottom: 8px; transition: all 0.2s; cursor: pointer; }}
.mobile-nav-link:hover, .mobile-nav-link.active {{ color: #c084fc; background: rgba(192,132,252,0.1); }}

.page {{ display: none; min-height: calc(100vh - 72px); padding-top: 0; }}
.page.active {{ display: block; }}
.container {{ max-width: 1280px; margin: 0 auto; padding: 0 1.5rem; }}

@media (max-width: 768px) {{ .nav-links {{ display: none; }} .hamburger {{ display: flex; }} }}







/* Yellow Icon Styles for Navigation */
.nav-link i, 
.mobile-nav-link i {{
    filter: drop-shadow(0 0 3px rgba(234, 179, 8, 0.5));
    transition: all 0.3s ease;
}}

.nav-link:hover i, 
.mobile-nav-link:hover i {{
    filter: drop-shadow(0 0 8px rgba(234, 179, 8, 0.8));
    transform: scale(1.1);
}}

.nav-link:hover span, 
.mobile-nav-link:hover span {{
    color: #eab308;
}}

.nav-link.active i, 
.mobile-nav-link.active i {{
    color: #fbbf24;
    filter: drop-shadow(0 0 5px rgba(251, 191, 36, 0.8));
}}

.nav-link.active span, 
.mobile-nav-link.active span {{
    color: #fbbf24;
}}

.brand i {{
    filter: drop-shadow(0 0 5px rgba(234, 179, 8, 0.5));
}}

.brand:hover i {{
    transform: scale(1.05);
    filter: drop-shadow(0 0 10px rgba(234, 179, 8, 0.8));
}}





/* ========== PRODUCT CARD STYLES ========== */
.product-card {{
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 1rem;
    padding: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
}}

.product-card:hover {{
    {{transform}}: translateY(-4px);
    border-color: #c084fc;
    box-shadow: 0 10px 25px -5px rgba(192, 132, 252, 0.3);
}}

.product-image {{
    background: linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(236, 72, 153, 0.2));
    border-radius: 0.75rem;
    transition: all 0.3s ease;
}}

.product-card:hover .product-image i {{
    {{transform}}: scale(1.1);
}}

.product-title {{
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: white;
}}

.product-price {{
    font-size: 1.5rem;
    font-weight: 700;
    color: #c084fc;
    margin-bottom: 1rem;
}}

.add-to-cart-btn {{
    width: 100%;
    padding: 0.5rem 1rem;
    background: linear-gradient(135deg, #8b5cf6, #ec4899);
    color: white;
    border-radius: 0.5rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    border: none;
}}

.add-to-cart-btn:hover {{
    opacity: 0.9;
    {{transform}}: scale(0.98);
}}

/* ========== CART SIDEBAR STYLES ========== */
#cart-sidebar {{
    position: fixed;
    right: 0;
    top: 0;
    height: 100%;
    width: 100%;
    max-width: 420px;
    background: linear-gradient(135deg, #1a1a2e, #0f0f12);
    box-shadow: -5px 0 30px rgba(0, 0, 0, 0.5);
    z-index: 1000;
    {{transform}}: translateX(100%);
    transition: {{transform}} 0.3s ease;
    display: flex;
    flex-direction: column;
}}

#cart-sidebar.active {{
    {{transform}}: translateX(0);
}}

/* ========== CART PAGE STYLES ========== */
#cart-page-items {{
    max-height: 60vh;
    overflow-y: auto;
}}

#cart-page-items .flex {{
    background: rgba(255, 255, 255, 0.05);
    border-radius: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 1rem;
    transition: all 0.3s ease;
}}

#cart-page-items .flex:hover {{
    border-color: #c084fc;
    background: rgba(255, 255, 255, 0.08);
}}

#cart-summary {{
    animation: fadeInUp 0.4s ease-out;
}}

/* ========== CART BADGE STYLES ========== */
.cart-count-badge {{
    animation: bounceIn 0.3s ease-out;
    box-shadow: 0 0 10px rgba(168, 85, 247, 0.5);
}}

/* ========== TOAST NOTIFICATION ========== */
#cart-toast {{
    position: fixed;
    bottom: 2rem;
    left: 50%;
    {{transform}}: translateX(-50%);
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 2rem;
    font-size: 0.875rem;
    font-weight: 500;
    z-index: 1001;
    opacity: 0;
    transition: opacity 0.3s ease;
    pointer-events: none;
    white-space: nowrap;
}}

#cart-toast.show {{
    opacity: 1;
}}

/* ========== MODAL STYLES ========== */
#checkout-modal, #success-modal {{
    animation: fadeIn 0.2s ease-out;
}}

#checkout-modal input, #success-modal input {{
    transition: all 0.2s ease;
}}

#checkout-modal input:focus, #success-modal input:focus {{
    border-color: #c084fc;
    box-shadow: 0 0 0 2px rgba(192, 132, 252, 0.2);
}}

/* ========== ANIMATIONS ========== */
@keyframes bounceIn {{
    0% {{ {{transform}}: scale(0); opacity: 0; }}
    50% {{ {{transform}}: scale(1.2); }}
    100% {{ {{transform}}: scale(1); opacity: 1; }}
}}

@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
}}

@keyframes fadeInUp {{
    from {{
        opacity: 0;
        {{transform}}: translateY(20px);
    }}
    to {{
        opacity: 1;
        {{transform}}: translateY(0);
    }}
}}

@keyframes spin {{
    to {{ {{transform}}: rotate(360deg); }}
}}

.fa-spinner {{
    animation: spin 1s linear infinite;
}}

/* ========== SCROLLBAR STYLES ========== */
#cart-items::-webkit-scrollbar,
#cart-page-items::-webkit-scrollbar {{
    width: 6px;
}}

#cart-items::-webkit-scrollbar-track,
#cart-page-items::-webkit-scrollbar-track {{
    background: rgba(255, 255, 255, 0.05);
    border-radius: 3px;
}}

#cart-items::-webkit-scrollbar-thumb,
#cart-page-items::-webkit-scrollbar-thumb {{
    background: linear-gradient(135deg, #8b5cf6, #ec4899);
    border-radius: 3px;
}}

#cart-items::-webkit-scrollbar-thumb:hover,
#cart-page-items::-webkit-scrollbar-thumb:hover {{
    background: linear-gradient(135deg, #a855f7, #f472b6);
}}

/* ========== BUTTON HOVER EFFECTS ========== */
button {{
    transition: all 0.2s ease;
}}

button:active {{
    {{transform}}: scale(0.98);
}}

/* ========== EMPTY CART MESSAGE ========== */
#empty-cart-message i {{
    opacity: 0.5;
}}

/* ========== GRID LAYOUT FOR PRODUCTS ========== */
.grid {{
    display: grid;
    gap: 1.5rem;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}}

@media (min-width: 768px) {{
    .grid {{
        grid-template-columns: repeat(3, 1fr);
    }}
}}

/* ========== RESPONSIVE ADJUSTMENTS ========== */
@media (max-width: 768px) {{
    #cart-sidebar {{
        max-width: 100%;
    }}
    
    .product-card {{
        padding: 1rem;
    }}
    
    .product-title {{
        font-size: 1rem;
    }}
    
    .product-price {{
        font-size: 1.25rem;
    }}
    
    #cart-toast {{
        font-size: 0.75rem;
        padding: 0.5rem 1rem;
        white-space: nowrap;
    }}
}}

/* ========== CHECKOUT FORM STYLES ========== */
#checkout-form input {{
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
}}

#checkout-form input:focus {{
    outline: none;
    border-color: #c084fc;
    ring: 2px solid rgba(192, 132, 252, 0.3);
}}

/* ========== SUCCESS MODAL ICON ========== */
#success-modal .fa-check {{
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}}

#page_home section {{
    scroll-margin-top: 72px;
}}

.relative.z-10 {{
    margin-top: 72px;
}}


/* In your <style> tag */
.relative.z-10 {{
    padding-top: max(125px, 12vh) !important;
}}

/* For iframe (small screens) */
@media (max-height: 600px) {{
    .relative.z-10 {{
        padding-top: 15vh !important;
    }}
}}
</style>


















================================================================================
🚨 CRITICAL: PROPER CONTAINER STRUCTURE - MUST FOLLOW EXACTLY 🚨
================================================================================

You MUST wrap ALL section content in a proper container with mx-auto for centering.

================================================================================
HERO SECTION - CORRECT STRUCTURE (MUST USE THIS EXACTLY):
================================================================================

```html
<section class="relative h-screen flex items-center justify-center overflow-hidden">
    <!-- Background Image -->
    <img src="[IMAGE_URL]" alt="Hero" class="absolute inset-0 w-full h-full object-cover" />
    
    <!-- Overlay -->
    <div class="absolute inset-0 bg-black/50"></div>
    
    <!-- Content Container - THIS IS THE KEY -->
    <div class="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <!-- ALL hero content goes INSIDE this div -->
        <span class="inline-block px-4 py-1 rounded-full bg-purple-500/20 text-purple-300 text-sm mb-4">BADGE TEXT</span>
        <h1 class="text-5xl md:text-7xl font-bold text-white mb-6">[BRAND_NAME]</h1>
        <p class="text-lg md:text-xl text-gray-200 mb-8 max-w-2xl mx-auto">[DESCRIPTION]</p>
        <div class="flex gap-4 justify-center">
            <a href="/shop" class="btn">Shop Now →</a>
            <a href="/catalog" class="btn">View Collection</a>
        </div>
    </div>
</section>























================================================================================
🚨 NAVIGATION & MOBILE MENU CSS REQUIREMENTS - MUST INCLUDE EXACTLY 🚨
================================================================================

You MUST include these COMPLETE navigation styles in your <style> tag:

```css
/* ========== HEADER & NAVIGATION ========== */
header {{
    background: rgba(26, 26, 30, 0.95);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    height: 72px;
}}



/* In your <style> tag */
.relative.z-10 {{
    padding-top: max(125px, 12vh) !important;
}}

/* For iframe (small screens) */
@media (max-height: 600px) {{
    .relative.z-10 {{
        padding-top: 15vh !important;
    }}
}}



.nav-container {{
    max-width: 1280px;
    margin: 0 auto;
    height: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 1.5rem;
}}

.brand {{
    font-size: 1.5rem;
    font-weight: 800;
    text-decoration: none;
    background: linear-gradient(135deg, #c084fc, #f472b6);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
}}

.nav-links {{
    display: flex;
    gap: 1rem;
    align-items: center;
}}

.nav-link {{
    color: #9ca3af;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    transition: all 0.2s;
    cursor: pointer;
}}

.nav-link:hover,
.nav-link.active {{
    color: #c084fc;
    background: rgba(192, 132, 252, 0.1);
}}

/* ========== MOBILE MENU ========== */
.hamburger {{
    display: none;
    flex-direction: column;
    gap: 4px;
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 0.5rem;
}}

.hamburger span {{
    width: 25px;
    height: 3px;
    background: #9ca3af;
    border-radius: 2px;
    transition: all 0.3s ease;
}}

/* Hamburger animation to X when open */
.hamburger.active span:nth-child(1) {{
    transform: rotate(45deg) translate(5px, 5px);
}}

.hamburger.active span:nth-child(2) {{
    opacity: 0;
}}

.hamburger.active span:nth-child(3) {{
    transform: rotate(-45deg) translate(5px, -5px);
}}

.mobile-menu {{
    position: fixed;
    top: 72px;
    right: -100%;
    width: 280px;
    height: calc(100vh - 72px);
    background: #1a1a1e;
    z-index: 200;
    transition: right 0.3s ease;
    padding: 24px;
    border-left: 1px solid rgba(255, 255, 255, 0.1);
}}

.mobile-menu.active {{
    right: 0;
}}

.mobile-overlay {{
    position: fixed;
    top: 72px;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 199;
    display: none;
}}

.mobile-overlay.active {{
    display: block;
}}

.mobile-nav-link {{
    display: block;
    padding: 12px 16px;
    color: #9ca3af;
    text-decoration: none;
    border-radius: 0.5rem;
    margin-bottom: 8px;
    transition: all 0.2s;
    cursor: pointer;
}}

.mobile-nav-link:hover,
.mobile-nav-link.active {{
    color: #c084fc;
    background: rgba(192, 132, 252, 0.1);
}}

/* Responsive */
@media (max-width: 768px) {{
    .nav-links {{
        display: none;
    }}
    .hamburger {{
        display: flex;
    }}
}}






================================================================================
🚨 AI INSTRUCTIONS FOR HTML PREVIEW GENERATION 🚨
================================================================================

You are generating a COMPLETE HTML preview from Next.js React components.

================================================================================
CRITICAL RULES FOR NAVIGATION:
================================================================================

1. Navigation links MUST NOT have inline onclick attributes:
   ✅ CORRECT: <a href="#" class="nav-link" data-page="courses">Courses</a>
   ❌ WRONG: <a href="#" onclick="handleNavClick()" data-page="courses">Courses</a>

2. The JavaScript handles all clicks via event listeners - do NOT add onclick to nav links

3. Each page div MUST have id="page_pagename" where pagename matches data-page attribute

4. Active page MUST have class="active", others should not



================================================================================
EXACT HOME PAGE CONTENT - CONVERT THIS JSX TO HTML (PRESERVE EVERYTHING):
================================================================================
{home_content}

================================================================================
EXACT FAQ CONTENT - USE THIS EXACT HTML (DO NOT MODIFY):
================================================================================
{faq_html}

================================================================================
EXACT STATS CONTENT - USE THIS EXACT HTML (DO NOT MODIFY):
================================================================================
{faq_html}














================================================================================
🚨 CRITICAL: FAQ SECTION - PRESERVE ALL EXTRACTED ITEMS 🚨
================================================================================

You have been provided with FAQ content extracted from the source file below.
The number of FAQ items will vary based on what exists in the source.

EXTRACTED FAQ CONTENT (use ALL items below - do not add or remove):
================================================================================
{faq_html if faq_html else 'No FAQ items found in source'}
================================================================================

CRITICAL RULES FOR FAQ:
1. Use EVERY FAQ item in the HTML above - preserve ALL questions and answers
2. DO NOT add new FAQ items that don't exist
3. DO NOT remove any FAQ items
4. Each FAQ item MUST have working accordion toggle functionality
5. The answer must be hidden initially and shown when clicking the question

If there are 4 items in the extracted content → generate 4 items in HTML
If there are 3 items → generate 3 items
If there are 2 items → generate 2 items
If there is 1 item → generate 1 item
If there are 0 items → skip the FAQ section entirely

================================================================================
EXTRACTED FAQ HTML (USE THESE EXACT QUESTIONS AND ANSWERS):
================================================================================
{faq_html}









================================================================================
EXACT TESTIMONIALS CONTENT - USE THIS EXACT HTML:
================================================================================
{testimonials_html}










================================================================================
🚨 PREVIEW GENERATION INSTRUCTION - INCLUDE ALL SECTIONS FROM SOURCE FILES 🚨
================================================================================


Generate a complete HTML preview that includes EVERY section found in the source files.

CRITICAL RULES:
1. **ALWAYS include** the Navigation component (from components/Navigation.tsx)
2. **ALWAYS include** the Hero section (from app/page.tsx)
3. **ALWAYS include** the Features section (from app/page.tsx) - if present
4. **ALWAYS include** the Testimonials section (from app/page.tsx) - if present
5. **ALWAYS include** the Stats section (from app/page.tsx) - if present
6. **ALWAYS include** the FAQ section (from app/page.tsx) - if present
7. **ALWAYS include** the Footer (from components/Footer.tsx)

For EACH section found in the source files:
- Copy the EXACT content (same text, same images, same layout)
- Convert React components to HTML
- Preserve all styling classes
- Keep the same order as the original page

If a section does NOT exist in the source files → DO NOT generate it

The final HTML preview should be a TRUE representation of the Next.js project, containing ALL sections that exist in the original code.

================================================================================








================================================================================
🚨 CRITICAL: USE EXACT NAVIGATION HTML - DO NOT MODIFY 🚨
================================================================================

You MUST use the navigation HTML provided below EXACTLY as is.
DO NOT add, remove, or modify any links.

The brand/logo is the ONLY home link. There is NO separate "Home" button.

================================================================================
EXACT NAVIGATION HTML - USE THIS EXACTLY (DO NOT MODIFY):
================================================================================
{navigation_html}

================================================================================
RULES FOR THIS NAVIGATION:
================================================================================
1. ✅ The brand/logo clicks to home page (already has onclick="handleBrandClick(event)")
2. ✅ Only these links exist: Projects, About, Contact (or whatever is in the HTML above)
3. ❌ DO NOT add a "Home" link - it does not exist in the source
4. ❌ DO NOT add any extra links that aren't in the HTML above
5. ✅ Keep ALL classes, icons, and styling exactly as shown

================================================================================
IF THE NAVIGATION ABOVE IS EMPTY OR MISSING, USE THIS FALLBACK (WITHOUT HOME):
================================================================================
<nav class="flex justify-between items-center p-6 container mx-auto sticky top-0 z-50 bg-black/80 backdrop-blur-lg border-b border-white/10">
    <a href="/" class="brand flex items-center gap-2 group" onclick="handleBrandClick(event)">
        <i data-lucide="sparkles" class="w-6 h-6 text-yellow-400 drop-shadow-lg group-hover:scale-110 transition-all duration-300"></i>
        <span class="text-xl font-bold bg-gradient-to-r from-yellow-400 to-purple-500 bg-clip-text text-transparent">{brand_name}</span>
    </a>
    <div class="hidden md:flex space-x-2">
        <a href="/projects" class="nav-link flex items-center gap-2 group" data-page="projects">
            <i data-lucide="folder" class="w-4 h-4 text-yellow-400 group-hover:text-amber-500 group-hover:scale-110 transition-all duration-300"></i>
            <span class="text-gray-300 group-hover:text-yellow-400 transition-colors duration-300">Projects</span>
        </a>
        <a href="/about" class="nav-link flex items-center gap-2 group" data-page="about">
            <i data-lucide="info" class="w-4 h-4 text-yellow-400 group-hover:text-amber-500 group-hover:scale-110 transition-all duration-300"></i>
            <span class="text-gray-300 group-hover:text-yellow-400 transition-colors duration-300">About</span>
        </a>
        <a href="/contact" class="nav-link flex items-center gap-2 group" data-page="contact">
            <i data-lucide="mail" class="w-4 h-4 text-yellow-400 group-hover:text-amber-500 group-hover:scale-110 transition-all duration-300"></i>
            <span class="text-gray-300 group-hover:text-yellow-400 transition-colors duration-300">Contact</span>
        </a>
    </div>
    <button id="mobile-menu-button" class="md:hidden p-2 rounded-lg hover:bg-white/10 transition-colors">
        <i data-lucide="menu" class="w-6 h-6 text-yellow-400"></i>
    </button>
</nav>




================================================================================
VERIFICATION: The final HTML MUST NOT contain any "Home" link in the navigation.
================================================================================



This ensures the AI:
1. Uses your exact navigation HTML (with the correct links and icons)
2. Never adds a "Home" link
3. Preserves all icons and styling
4. Only shows Projects, About, Contact (or whatever is in your source)








================================================================================
MOBILE MENU REQUIREMENTS
================================================================================
- Hamburger button must exist and be clickable
- Mobile menu must slide in from right
- Clicking overlay or link must close menu
- Hamburger must animate to X when open









================================================================================
🚨🚨🚨 CRITICAL: HERO BACKGROUND IMAGE URL - MUST USE CLOUDINARY URL 🚨🚨🚨
================================================================================

The hero background image MUST use EXACTLY this Cloudinary URL:

{image_url if image_url else first_image_display}

ABSOLUTE RULES - YOU MUST FOLLOW:
1. DO NOT replace this URL with "/images/image_1.jpg"
2. DO NOT use any local path like "/images/image_1.jpg"  
3. DO NOT use placeholder images or gradients
4. MUST use the EXACT Cloudinary URL provided above

CORRECT hero section (MUST USE THIS EXACT STRUCTURE):
<section class="relative h-screen flex items-center justify-center overflow-hidden">
    <img src="{image_url if image_url else first_image_display}" alt="Hero background" class="absolute inset-0 w-full h-full object-cover" />
    <div class="absolute inset-0 bg-black/50"></div>
    <div class="relative z-10 text-center px-4">
        <h1 class="text-6xl md:text-7xl font-bold text-white mb-6">{brand_name}</h1>
        <p class="text-xl text-gray-200 mb-8 max-w-2xl mx-auto">Your tagline here</p>
        <a href="#" class="btn">Get Started</a>
    </div>
</section>

WRONG - NEVER DO THIS:
❌ <img src="/images/image_1.jpg" ...>
❌ <img src="./image.jpg" ...>
❌ <div class="bg-gradient"></div> (without the image)
❌ Using any local path that starts with "/images/"

================================================================================













================================================================================
🚨 CRITICAL: BRAND ICON REQUIREMENT - MUST INCLUDE LUCIDE ICON
================================================================================

STATEMENT: The brand/logo link in the navigation MUST include a Lucide icon next to the brand name.

REQUIREMENT: Every brand link MUST have this structure:
- Use <a> tag (NOT <div>)
- Include flex classes: class="flex items-center gap-2"
- Add Lucide icon: <i data-lucide="icon-name" class="w-6 h-6 text-purple-400"></i>
- Add brand name text

✅ CORRECT HTML:
<a href="/" class="flex items-center gap-2 text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent" onclick="handleBrandClick(event)">
    <i data-lucide="hotel" class="w-6 h-6 text-purple-400"></i>
    Lodge Hub
</a>

❌ WRONG HTML (missing icon):
<div class="brand" onclick="handleBrandClick(event)">Lodge Hub</div>

❌ WRONG HTML (missing flex classes):
<a href="/" class="brand" onclick="handleBrandClick(event)">
    <i data-lucide="hotel"></i> Lodge Hub
</a>

CONSEQUENCE: Without the proper icon structure, the brand will have no visual icon and will not align correctly.

================================================================================











================================================================================
🚨 CRITICAL: BRAND/LOGO CLICK HANDLER - MUST INCLUDE
================================================================================

STATEMENT: The brand/logo link MUST have an onclick handler that navigates to the home page.






================================================================================
🚨 MANDATORY CSS INSTRUCTION - DO NOT IGNORE 🚨
================================================================================

You MUST include the COMPLETE CSS code below in EVERY HTML preview you generate.
This CSS is REQUIRED for proper navigation, mobile menu, and page transitions.
NEVER skip CSS. 







================================================================================
🚨🚨🚨 CRITICAL: YOU ARE AN HTML CONVERTER, NOT A CONTENT GENERATOR 🚨🚨🚨
================================================================================

Your ONLY job is to convert the EXACT React JSX content below into HTML.
DO NOT write new content. DO NOT change wording. DO NOT add or remove sections.

================================================================================
ICON REQUIREMENTS:
================================================================================
- Navigation brand: Use Lucide icons with <i data-lucide="icon-name">
- Footer social icons: Use Font Awesome with <i class="fab fa-icon-name">
- Feature cards: Use regular HTML/SVG, NOT Lucide icons
- Initialize Lucide with: lucide.createIcons()

================================================================================
EXACT NAVIGATION HTML - USE THIS EXACTLY (DO NOT MODIFY):
================================================================================
{navigation_html_for_prompt}

================================================================================
EXACT HOME PAGE CONTENT - CONVERT THIS JSX TO HTML (PRESERVE EVERYTHING):
================================================================================
{home_content}

================================================================================
EXACT OTHER PAGES CONTENT - CONVERT THESE TO HTML (PRESERVE EVERYTHING):
================================================================================
{page_contents_json}

================================================================================
EXACT BRAND NAME (use this exactly):
================================================================================
{brand_name}

================================================================================
EXACT NAVIGATION LINKS (use these exactly):
================================================================================
{nav_links_json}





================================================================================
EXACT FOOTER HTML - USE THE EXTRACTED CONTENT BELOW (DO NOT GENERATE NEW FOOTER)
================================================================================

The footer HTML below has been EXTRACTED from your components/Footer.tsx file.
You MUST use this EXACT HTML. DO NOT modify, simplify, or replace it.

EXTRACTED FOOTER HTML (USE THIS EXACTLY):
================================================================================
{footer_html}

================================================================================
🚨 CRITICAL: IF EXTRACTED FOOTER IS MISSING OR EMPTY, USE THIS FALLBACK 🚨
================================================================================
{f'''
<footer class="relative mt-20 bg-gradient-to-b from-zinc-950 to-black border-t border-white/10 py-12">
    <div class="container mx-auto px-4 grid md:grid-cols-4 gap-8">
        <div class="space-y-4">
            <div class="flex items-center gap-2">
                <i class="fas fa-sparkles text-purple-500"></i>
                <h3 class="font-bold text-lg">{brand_name}</h3>
            </div>
            <p class="text-sm text-gray-400">Premium digital solutions for modern businesses.</p>
            <div class="flex gap-4">
                <i class="fab fa-facebook-f text-gray-400 hover:text-purple-400 transition-colors cursor-pointer"></i>
                <i class="fab fa-twitter text-gray-400 hover:text-purple-400 transition-colors cursor-pointer"></i>
                <i class="fab fa-instagram text-gray-400 hover:text-purple-400 transition-colors cursor-pointer"></i>
            </div>
        </div>
        <div>
            <h4 class="font-bold mb-4">Quick Links</h4>
            <ul class="space-y-2 text-sm text-gray-400">
                <li><a href="/shop" class="hover:text-purple-400 transition-colors">Shop</a></li>
                <li><a href="/catalog" class="hover:text-purple-400 transition-colors">Catalog</a></li>
                <li><a href="/about" class="hover:text-purple-400 transition-colors">About Us</a></li>
            </ul>
        </div>
        <div>
            <h4 class="font-bold mb-4">Contact</h4>
            <ul class="space-y-2 text-sm text-gray-400">
                <li class="flex items-center gap-2"><i class="fas fa-envelope"></i> support@{brand_name.lower().replace(' ', '')}.com</li>
                <li class="flex items-center gap-2"><i class="fas fa-phone"></i> +1 (555) 123-4567</li>
                <li class="flex items-center gap-2"><i class="fas fa-map-marker-alt"></i> 123 Innovation Drive, NY 10001</li>
            </ul>
        </div>
        <div>
            <h4 class="font-bold mb-4">Newsletter</h4>
            <p class="text-sm text-gray-400 mb-3">Get 10% off your first order</p>
            <form class="flex gap-2" onsubmit="handleNewsletter(event)">
                <input type="email" placeholder="Your email address" class="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-purple-500 transition-colors" />
                <button type="submit" class="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all"><i class="fas fa-paper-plane"></i></button>
            </form>
        </div>
    </div>
    <div class="text-center mt-8 pt-8 border-t border-white/10 text-sm text-gray-500">
        © 2026 {brand_name}. Crafted by Eaglecode
    </div>
</footer>
''' if not footer_html else ''}

================================================================================
🚨 FOOTER ICON CONVERSION RULES - APPLY TO EXTRACTED CONTENT 🚨
================================================================================

The extracted footer may contain Lucide icons. Convert them to Font Awesome:

| Pattern | Replace With |
|---------|--------------|
| `<Sparkles className="..." />` | `<i class="fas fa-sparkles text-purple-500"></i>` |
| `<Mail className="..." />` | `<i class="fas fa-envelope"></i>` |
| `<Phone className="..." />` | `<i class="fas fa-phone"></i>` |
| `<MapPin className="..." />` | `<i class="fas fa-map-marker-alt"></i>` |
| `<Send className="..." />` | `<i class="fas fa-paper-plane"></i>` |
| `<Heart className="..." />` | `<i class="fas fa-heart text-red-500"></i>` |
| `<Facebook className="..." />` | `<i class="fab fa-facebook-f"></i>` |
| `<Twitter className="..." />` | `<i class="fab fa-twitter"></i>` |
| `<Instagram className="..." />` | `<i class="fab fa-instagram"></i>` |
| `<ArrowUp />` | `<i class="fas fa-arrow-up"></i>` |

================================================================================
🚨 SCROLL TO TOP BUTTON & NEWSLETTER HANDLER - MUST INCLUDE 🚨
================================================================================

Add this button before closing </body>:
```html
<button id="scrollToTop" class="fixed bottom-8 right-8 z-50 w-12 h-12 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/30 hover:scale-110 transition-all duration-300 flex items-center justify-center opacity-0 invisible">
    <i class="fas fa-arrow-up"></i>
</button>

Add this script before closing </body>:

<script>
(function() {{
    const scrollBtn = document.getElementById('scrollToTop');
    if (scrollBtn) {{
        window.addEventListener('scroll', function() {{
            if (window.scrollY > 500) {{
                scrollBtn.classList.remove('opacity-0', 'invisible');
                scrollBtn.classList.add('opacity-100', 'visible');
            }} else {{
                scrollBtn.classList.add('opacity-0', 'invisible');
                scrollBtn.classList.remove('opacity-100', 'visible');
            }}
        }});
        scrollBtn.addEventListener('click', function() {{
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }});
    }}
    
    window.handleNewsletter = function(event) {{
        event.preventDefault();
        const email = event.target.querySelector('input[type="email"]')?.value;
        if (email) {{
            alert('Thank you for subscribing with: ' + email);
            event.target.reset();
        }}
    }};
}})();
</script>

================================================================================
KEEP ALL TEXT CONTENT EXACTLY AS EXTRACTED - DO NOT MODIFY:
================================================================================


1. Preserve ALL link text

2. Preserve ALL descriptions

3. Preserve ALL contact information

4. Preserve copyright text



















================================================================================
EXACT HERO BACKGROUND IMAGE URL (use this exactly):
================================================================================
{first_image_display}

================================================================================
RULES FOR CONVERTING HOME PAGE CONTENT:
================================================================================

1. Extract the hero section with EXACT text from {home_content}
2. Extract ALL feature cards with EXACT titles and descriptions
3. Extract ALL stats with EXACT numbers and labels
4. Extract ALL testimonials with EXACT quotes and names
5. Extract ALL CTA sections with EXACT button text
6. Preserve the EXACT number of items (don't add or remove cards)
7. Keep ALL text EXACTLY as written in the original JSX

================================================================================
RULES FOR CONVERTING OTHER PAGES:
================================================================================

For each page in {page_contents_json}:
1. Use the EXACT content provided
2. Preserve ALL headings, paragraphs, and button text
3. Keep the SAME number of cards, items, or sections
4. DO NOT add placeholder text like "Coming soon" or "Lorem ipsum"

================================================================================
DESIGN REQUIREMENTS:
================================================================================

1. Modern dark theme with purple/pink gradients (#c084fc, #f472b6)
2. Glass morphism effects (backdrop-blur, semi-transparent backgrounds)
3. Smooth animations and hover effects
4. Fully responsive (mobile hamburger menu at 768px)
5. ONLY ONE <style> tag and ONE <script> tag
6. Navigation brand uses Lucide icon - Footer uses Font Awesome - Features use HTML/SVG

















================================================================================
COMPLETE JAVASCRIPT:
================================================================================
<script>
    function handleBrandClick(event) {{
        event.preventDefault();
        event.stopPropagation();
        showPage('home');
        return false;
    }}
    
    function showPage(pageId) {{
        document.querySelectorAll('.page').forEach(page => {{
            page.classList.remove('active');
            page.style.display = 'none';
        }});
        const targetPage = document.getElementById('page_' + pageId);
        if (targetPage) {{
            targetPage.classList.add('active');
            targetPage.style.display = 'block';
        }}
        window.scrollTo(0, 0);
    }}
    
    function toggleMobileMenu() {{
        const mobileMenu = document.getElementById('mobileMenu');
        const mobileOverlay = document.getElementById('mobileOverlay');
        const hamburger = document.querySelector('.hamburger');
        
        if (mobileMenu) {{
            mobileMenu.classList.toggle('active');
        }}
        if (mobileOverlay) {{
            mobileOverlay.classList.toggle('active');
        }}
        if (hamburger) {{
            hamburger.classList.toggle('active');
        }}
    }}
    
    
    
    
    
    
    

    // ========== FAQ ACCORDION FUNCTIONS ==========
    function initFaqAccordion() {{
        const faqButtons = document.querySelectorAll('.faq-btn, .faq-question');
        faqButtons.forEach(button => {{
            button.removeEventListener('click', handleFaqClick);
            button.addEventListener('click', handleFaqClick);
        }});
    }}
    
    function handleFaqClick(event) {{
        const button = event.currentTarget;
        const answer = button.nextElementSibling;
        const icon = button.querySelector('i');
        if (answer && answer.classList.contains('hidden')) {{
            answer.classList.remove('hidden');
            if (icon) {{
                icon.classList.remove('fa-plus');
                icon.classList.add('fa-minus');
            }}
        }} else if (answer) {{
            answer.classList.add('hidden');
            if (icon) {{
                icon.classList.remove('fa-minus');
                icon.classList.add('fa-plus');
            }}
        }}
    }}
    

    function initScrollToTop() {{
        const scrollBtn = document.getElementById('scrollToTop');
        if (!scrollBtn) return;
        window.addEventListener('scroll', () => {{
            if (window.scrollY > 500) {{
                scrollBtn.classList.remove('opacity-0', 'invisible');
                scrollBtn.classList.add('opacity-100', 'visible');
            }} else {{
                scrollBtn.classList.add('opacity-0', 'invisible');
                scrollBtn.classList.remove('opacity-100', 'visible');
            }}
        }});
        scrollBtn.addEventListener('click', () => {{
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }});
    }}
    
    // ========== NEWSLETTER FORM HANDLER ==========
    function initNewsletterForm() {{
        const newsletterForm = document.getElementById('newsletterForm');
        if (newsletterForm) {{
            newsletterForm.addEventListener('submit', (e) => {{
                e.preventDefault();
                const emailInput = newsletterForm.querySelector('input[type="email"]');
                if (emailInput && emailInput.value) {{
                    alert(`Thank you for subscribing with: ${{emailInput.value}}`);
                    emailInput.value = '';
                }}
            }});
        }}
    }}

    
    
    
    function toggleMobileMenu() {{
        const mobileMenu = document.getElementById('mobileMenu');
        const mobileOverlay = document.getElementById('mobileOverlay');
        const hamburger = document.querySelector('.hamburger');
        
        if (mobileMenu) mobileMenu.classList.toggle('active');
        if (mobileOverlay) mobileOverlay.classList.toggle('active');
        if (hamburger) hamburger.classList.toggle('active');
    }}
    
    
    
    
    
    
    
    function closeMobileMenu() {{
        const mobileMenu = document.getElementById('mobileMenu');
        const mobileOverlay = document.getElementById('mobileOverlay');
        const hamburger = document.querySelector('.hamburger');
        
        if (mobileMenu) {{
            mobileMenu.classList.remove('active');
        }}
        if (mobileOverlay) {{
            mobileOverlay.classList.remove('active');
        }}
        if (hamburger) {{
            hamburger.classList.remove('active');
        }}
    }}
    
    document.addEventListener('DOMContentLoaded', function() {{
        if (typeof lucide !== 'undefined') {{
            lucide.createIcons();
        }}
        
        const hamburger = document.querySelector('.hamburger');
        if (hamburger) {{
            hamburger.addEventListener('click', toggleMobileMenu);
        }}
        
        const overlay = document.getElementById('mobileOverlay');
        if (overlay) {{
            overlay.addEventListener('click', closeMobileMenu);
        }}
        
        document.querySelectorAll('.nav-link, .mobile-nav-link').forEach(link => {{
            link.addEventListener('click', (e) => {{
                e.preventDefault();
                const pageId = link.getAttribute('data-page');
                if (pageId) showPage(pageId);
            }});
        }});
        
        const brandLink = document.querySelector('.brand');
        if (brandLink) {{
            brandLink.addEventListener('click', handleBrandClick);
        }}
    }});
    
    
    
    
    
    
</script>













================================================================================
FINAL VERIFICATION:
================================================================================

Before outputting, verify:
- [ ] Home page has EXACT same sections as extracted content
- [ ] All text matches the original JSX word-for-word
- [ ] Number of feature cards matches (should be 4 for gym website)
- [ ] Number of stats matches (should be 4 for gym website)
- [ ] Number of testimonials matches (should be 3 for gym website)
- [ ] No placeholder or generic text was added
- [ ] Navigation HTML was copied exactly
- [ ] Footer HTML was copied exactly (if provided)
- [ ] Footer icons use Font Awesome classes (fab fa-* or fas fa-*)
- [ ] Font Awesome CDN is in the <head> tag














================================================================================
SPECIFIC INSTRUCTION FOR HOME PAGE (page_home)
================================================================================

The home page content above (from app/page.tsx) contains:

- A hero section with an image
- An h1 heading with your actual brand name (like "Amber College Prep")
- A paragraph with your actual description
- A button with your actual button text (like "Explore Programs")

YOU MUST use these EXACT values. For example:

✅ CORRECT: <h1>Amber College Prep</h1>
❌ WRONG: <h1>Welcome to our website</h1>

✅ CORRECT: <p>Empowering the next generation of scholars...</p>
❌ WRONG: <p>Welcome to our website</p>

✅ CORRECT: <button>Explore Programs</button>
❌ WRONG: <button>Get Started</button>

================================================================================




================================================================================
🚨🚨🚨 CRITICAL: SIGNUP & LOGIN PAGE REQUIREMENTS 🚨🚨🚨
================================================================================

When generating the HTML preview, you MUST follow these rules for authentication pages:

**SIGNUP PAGE (page_signup) - MUST have:**
1. Form with id="signup-form"
2. Form with onsubmit="handleSignup(event); return false;"
3. Input with name="name" for full name
4. Input with name="email" for email address
5. Input with name="password" for password
6. Input with name="confirmPassword" for password confirmation
7. Submit button that says "Sign up"

**LOGIN PAGE (page_login) - MUST have:**
1. Form with id="login-form"
2. Form with onsubmit="handleLogin(event); return false;"
3. Input with name="email" for email address
4. Input with name="password" for password
5. Submit button that says "Sign in"









================================================================================
🚨🚨🚨 CRITICAL JAVASCRIPT RULES - NO FLICKER, NO DISAPPEARING BACKGROUND 🚨🚨🚨
================================================================================

The JavaScript code MUST follow these rules:

1. NEVER call showPage() inside init() - causes unnecessary hiding/showing
2. ALWAYS check if a page is already active before hiding all pages
3. ALWAYS return early in showPage() if already on the target page
4. NEVER use inline styles that override CSS classes
5. ALWAYS use CSS for display control, not JavaScript inline styles
6. ALWAYS add a flag to prevent double initialization



================================================================================
🚨🚨🚨 CRITICAL: USE THE EXTRACTED CONTENT BELOW - NO PLACEHOLDERS! 🚨🚨🚨
================================================================================

The content below is EXTRACTED DIRECTLY from your Next.js pages. 
YOU MUST use this EXACT content for each page's HTML.

DO NOT generate placeholder text like "Welcome to our page" or "Explore our offerings".
USE THE EXACT CONTENT PROVIDED BELOW.

================================================================================
EXTRACTED PAGE CONTENTS - USE THESE EXACTLY:
================================================================================


For EACH page, copy the EXACT content from the extracted JSON above into the page div.
If the content contains arrays/maps, render them as HTML cards/items.

For example, if Programs page has program data, render the actual programs with their titles, descriptions, icons, etc.











================================================================================
🚨🚨🚨 MANDATORY BODY BACKGROUND - MUST USE THIS EXACT GRADIENT 🚨🚨🚨
================================================================================

The <body> tag MUST use this EXACT background gradient:

<body class="bg-gradient-to-br from-purple-950 via-zinc-950 to-pink-950">

OR this alternative gradient:

<style>
body {{
    background: linear-gradient(135deg, #0f0f12 0%, #1a1a2e 100%);
}}
</style>

================================================================================
FORBIDDEN - NEVER USE THESE BACKGROUNDS:
================================================================================

❌ bg-black
❌ bg-white
❌ bg-zinc-900
❌ bg-gray-800
❌ bg-slate-900
❌ solid backgrounds of any single color

================================================================================
REQUIRED - ALWAYS USE GRADIENT BACKGROUNDS:
================================================================================

✅ linear-gradient(135deg, #0f0f12 0%, #1a1a2e 100%)
✅ bg-gradient-to-br from-purple-950 via-zinc-950 to-pink-950
✅ bg-gradient-to-tr from-indigo-950 via-purple-950 to-zinc-950

================================================================================
EXAMPLE - CORRECT BODY STYLING:
================================================================================

<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            background: linear-gradient(135deg, #0f0f12 0%, #1a1a2e 100%);
            color: #e2e8f0;
            min-height: 100vh;
        }}
    </style>
</head>
<body>
    <!-- content -->
</body>
</html>

================================================================================
















================================================================================
COMPLETE CSS - USE THIS EXACTLY
================================================================================


<script src="https://cdn.tailwindcss.com"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: 'Inter', system-ui, sans-serif;
    background: linear-gradient(135deg, #0f0f12 0%, #1a1a2e 100%);
    color: #e2e8f0;
    min-height: 100vh;
}}

header {{
    background: rgba(26, 26, 30, 0.95);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(255,255,255,0.1);
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 100;
    height: 72px;
}}

.nav-container {{
    max-width: 1280px;
    margin: 0 auto;
    height: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 1.5rem;
}}

.brand {{
    font-size: 1.5rem;
    font-weight: 800;
    text-decoration: none;
    background: linear-gradient(135deg, #c084fc, #f472b6);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}}

.nav-links {{
    display: flex;
    gap: 1rem;
    align-items: center;
}}

.nav-link {{
    color: #9ca3af;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    transition: all 0.2s;
}}

.nav-link:hover, .nav-link.active {{
    color: #c084fc;
    background: rgba(192,132,252,0.1);
}}

.page {{
    display: none;
    min-height: calc(100vh - 72px);
    padding-top: 88px;
}}

.page.active {{ display: block; }}

.container {{
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 1.5rem;
}}

.card {{
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(10px);
    border-radius: 1rem;
    padding: 1.5rem;
    border: 1px solid rgba(255,255,255,0.1);
    transition: all 0.3s;
}}

.card:hover {{
    transform: translateY(-4px);
    border-color: #c084fc;
}}

.gradient-text {{
    background: linear-gradient(135deg, #c084fc, #f472b6);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}}

.btn {{
    background: linear-gradient(135deg, #c084fc, #f472b6);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 2rem;
    font-weight: 600;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
}}

.btn:hover {{
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(192,132,252,0.3);
}}

.hero {{
    min-height: 70vh;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    position: relative;
    border-radius: 1rem;
    margin: 1rem;
    overflow: hidden;
}}

.hero-bg {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0.35;
}}

.hero-content {{
    position: relative;
    z-index: 10;
    padding: 3rem;
}}

.hero-content h1 {{
    font-size: 3.5rem;
    margin-bottom: 1rem;
}}

.hero-content p {{
    font-size: 1.2rem;
    color: #9ca3af;
    margin-bottom: 2rem;
}}

.grid {{
    display: grid;
    gap: 1.5rem;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}}

/* Footer */
footer {{
    background: linear-gradient(180deg, rgba(15,15,18,0.8) 0%, #1a1a2e 100%);
    border-top: 1px solid rgba(255,255,255,0.05);
    margin-top: 4rem;
    padding: 3rem 0 2rem;
}}

.footer-container {{
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 1.5rem;
    display: grid;
    gap: 2rem;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}}

.footer-section h4 {{
    color: #c084fc;
    margin-bottom: 1rem;
}}

.footer-section a {{
    color: #9ca3af;
    text-decoration: none;
    display: block;
    margin-bottom: 0.5rem;
    transition: color 0.2s;
}}

.footer-section a:hover {{ color: #c084fc; }}

.copyright {{
    text-align: center;
    padding-top: 2rem;
    margin-top: 2rem;
    border-top: 1px solid rgba(255,255,255,0.05);
    color: #6b7280;
    font-size: 0.875rem;
}}

/* Mobile Menu */
.hamburger {{
    display: none;
    flex-direction: column;
    gap: 4px;
    background: transparent;
    border: none;
    cursor: pointer;
}}

.hamburger span {{
    width: 25px;
    height: 3px;
    background: #9ca3af;
    border-radius: 2px;
}}

.mobile-menu {{
    position: fixed;
    top: 0;
    right: -100%;
    width: 280px;
    height: 100vh;
    background: #1a1a1e;
    z-index: 200;
    transition: right 0.3s;
    padding: 80px 24px;
}}

.mobile-menu.active {{ right: 0; }}

.mobile-overlay {{
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.5);
    z-index: 199;
    display: none;
}}

.mobile-overlay.active {{ display: block; }}

.mobile-nav-link {{
    display: block;
    padding: 12px 16px;
    color: #9ca3af;
    text-decoration: none;
    border-radius: 0.5rem;
    margin-bottom: 8px;
}}

@media (max-width: 768px) {{
    .nav-links {{ display: none; }}
    .hamburger {{ display: flex; }}
    .hero-content h1 {{ font-size: 2rem; }}
    .footer-container {{ grid-template-columns: 1fr; text-align: center; }}
}}

@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.page {{ animation: fadeIn 0.3s ease; }}










/* Hamburger animation to X when open */
.hamburger.active span:nth-child(1) {{
    {{transform}}: rotate(45deg) translate(5px, 5px);
}}

.hamburger.active span:nth-child(2) {{
    opacity: 0;
}}

.hamburger.active span:nth-child(3) {{
    {{transform}}: rotate(-45deg) translate(5px, -5px);
}}

/* Add transition to hamburger spans */
.hamburger span {{
    width: 25px;
    height: 3px;
    background: #9ca3af;
    border-radius: 2px;
    transition: all 0.3s ease;
}}





















/* ========== FAQ ACCORDION STYLES ========== */
.faq-answer {{
    transition: all 0.3s ease;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    margin-top: 0.5rem;
    padding-top: 0.5rem;
}}

.faq-answer.hidden {{
    display: none;
}}

.faq-btn, .faq-question {{
    cursor: pointer;
    transition: all 0.2s ease;
    background: transparent;
    width: 100%;
    text-align: left;
}}

.faq-btn:hover, .faq-question:hover {{
    background: rgba(255, 255, 255, 0.05);
}}

.faq-btn i, .faq-question i {{
    transition: transform 0.2s ease;
}}








/* Increase feature icon sizes */
.feature-icon {{
    font-size: 3rem;
    width: auto;
    height: auto;
}}

/* For all icons in feature cards */
.grid.md\\:grid-cols-4 > div i {{
    font-size: 2rem;
    width: auto;
    height: auto;
    margin-bottom: 1rem;
}}





</style>








































================================================================================
JAVASCRIPT - WORKING NAVIGATION WITH BRAND CLICK HANDLER (FIXED)
================================================================================
<script>
function showPage(pageId) {{
    console.log('🔄 showPage called with:', pageId);
    
    // Hide ALL pages
    document.querySelectorAll('.page').forEach(page => {{
        page.classList.remove('active');
        page.style.display = 'none';
    }});
    
    // Show the target page
    const targetPage = document.getElementById('page_' + pageId);
    if (targetPage) {{
        targetPage.classList.add('active');
        targetPage.style.display = 'block';
        console.log('✅ Showing page:', pageId);
    }} else {{
        console.log('❌ Page not found:', 'page_' + pageId);
        // Fallback - show home
        const homePage = document.getElementById('page_home');
        if (homePage) {{
            homePage.classList.add('active');
            homePage.style.display = 'block';
        }}
    }}
    
    // Update navigation active states
    document.querySelectorAll('.nav-link, .mobile-nav-link').forEach(link => {{
        link.classList.remove('active');
        if (link.getAttribute('data-page') === pageId) {{
            link.classList.add('active');
        }}
    }});
    
    // Update URL
    if (pageId !== 'home') {{
        window.history.pushState({{}}, '', '/' + pageId);
    }} else {{
        window.history.pushState({{}}, '', '/');
    }}
    window.scrollTo(0, 0);
}}

function toggleMenu() {{
    const menu = document.getElementById('mobileMenu');
    const overlay = document.getElementById('mobileOverlay');
    const hamburger = document.querySelector('.hamburger');
    
    if (menu) menu.classList.toggle('active');
    if (overlay) overlay.classList.toggle('active');
    if (hamburger) hamburger.classList.toggle('active');
}}

// Handle brand/logo click - ALWAYS go to home page
function handleBrandClick(e) {{
    e.preventDefault();
    e.stopPropagation();
    showPage('home');
    if (window.innerWidth <= 768) toggleMenu();
}}

// Handle navigation link clicks
function handleNavClick(e) {{
    e.preventDefault();
    const pageId = this.getAttribute('data-page');
    if (pageId) {{
        showPage(pageId);
        if (window.innerWidth <= 768) toggleMenu();
    }}
}}

// ========== INITIALIZATION - CRITICAL FOR HOME PAGE ==========
if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', init);
}} else {{
    init();
}}

function init() {{
    console.log('🎯 Initializing navigation...');
    
    // Get current path or default to home
    let currentPath = window.location.pathname.slice(1);
    if (!currentPath || currentPath === '') {{
        currentPath = 'home';
    }}
    console.log('📍 Current path:', currentPath);
    
    // Ensure ALL pages are hidden first
    document.querySelectorAll('.page').forEach(page => {{
        page.classList.remove('active');
        page.style.display = 'none';
    }});
    
    // Show the home page (or current path)
    const targetPageId = currentPath === 'home' ? 'page_home' : 'page_' + currentPath;
    const targetPage = document.getElementById(targetPageId);
    
    if (targetPage) {{
        targetPage.classList.add('active');
        targetPage.style.display = 'block';
        console.log('✅ Activated page:', targetPageId);
    }} else {{
        // Fallback - show home
        const homePage = document.getElementById('page_home');
        if (homePage) {{
            homePage.classList.add('active');
            homePage.style.display = 'block';
            console.log('✅ Fallback: Activated home page');
        }}
    }}
    
    // Update navigation active states
    document.querySelectorAll('.nav-link, .mobile-nav-link').forEach(link => {{
        link.classList.remove('active');
        if (link.getAttribute('data-page') === currentPath) {{
            link.classList.add('active');
        }}
    }});
    
    // Add event listeners
    const brandLink = document.querySelector('.brand');
    if (brandLink) {{
        brandLink.addEventListener('click', handleBrandClick);
        console.log('✅ Brand click handler attached');
    }}
    
    const hamburger = document.querySelector('.hamburger');
    const overlay = document.getElementById('mobileOverlay');
    if (hamburger) hamburger.addEventListener('click', toggleMenu);
    if (overlay) overlay.addEventListener('click', toggleMenu);
    
    document.querySelectorAll('.nav-link, .mobile-nav-link').forEach(link => {{
        link.removeEventListener('click', handleNavClick);
        link.addEventListener('click', handleNavClick);
    }});
    
    console.log('✅ Navigation initialized successfully');
}}

// Handle browser back/forward
window.addEventListener('popstate', () => {{
    const path = window.location.pathname.slice(1) || 'home';
    showPage(path);
}});
</script>







================================================================================
RETURN ONLY COMPLETE HTML starting with <!DOCTYPE html>. NO explanations.
================================================================================
"""





        response_text = await model_router.generate_content(
            prompt=prompt,
            config={"temperature": 0.1, "max_output_tokens": 60000}
        )

        preview_html = clean_html_response(response_text)


        
        preview_html = enforce_body_background(preview_html)
        
        
        
        
        preview_html = inject_matching_features_faq_css(preview_html)
        
        
        preview_html = smart_style_conditional(preview_html, user_prompt)
        
        preview_html = fix_hero_navigation_overlap(preview_html)
        
        
        # ADD THIS LINE - Remove React onError handlers
        preview_html = remove_react_onerror_handlers(preview_html)
        
        preview_html = remove_duplicate_cart_systems(preview_html)
        preview_html = ensure_master_cart_only(preview_html)
        preview_html = fix_duplicate_functions(preview_html)
        
        
        
        
        
        preview_html = fix_shop_page_buttons(preview_html)
        
        
        
        
        
        
        
     
        
        
        
        
        
        
        # Remove any product cards that appear after the shop page closing tag
        preview_html = re.sub(
            r'</div>\s*</div>\s*</div>\s*<div class="glass p-6 rounded-2xl">.*?</div>\s*<div class="glass p-6 rounded-2xl">.*?</div>\s*</div>\s*</div>\s*</div>(?=<div id="page_cart")',
            '',
            preview_html,
            flags=re.DOTALL
        )
        
        # Also remove any stray glass divs that contain product cards
        preview_html = re.sub(
            r'<div class="glass p-6 rounded-2xl"><h3 class="text-xl font-bold">.*?</h3><p class="text-purple-400 text-2xl font-bold my-4">.*?</p><button class="add-to-cart-btn w-full btn".*?</button></div>',
            '',
            preview_html,
            flags=re.DOTALL
        )
        
        print(f"🧹 Removed duplicate product cards outside shop page")        
        
        
        
        
        
        
        
        
        
                # ========== REMOVE DUPLICATE CART SCRIPTS ==========
        # Method 1: Remove script that starts with // ========== CART SYSTEM ==========
        preview_html = re.sub(
            r'<script>\s*// ========== CART SYSTEM ==========.*?</script>', 
            '', 
            preview_html, 
            flags=re.DOTALL
        )
        
        # Method 2: Remove script containing cart-page-items (the wrong ID)
        preview_html = re.sub(
            r'<script[^>]*>[\s\S]*?cart-page-items[\s\S]*?</script>', 
            '', 
            preview_html, 
            flags=re.DOTALL
        )
        
        # Method 3: Remove script containing empty-cart-message (without -cart suffix)
        preview_html = re.sub(
            r'<script[^>]*>[\s\S]*?empty-cart-message[^-][\s\S]*?</script>', 
            '', 
            preview_html, 
            flags=re.DOTALL
        )
        
        # Method 4: Remove any script that has wireAddToCartButtons but not MASTER
        preview_html = re.sub(
            r'<script[^>]*>[\s\S]*?wireAddToCartButtons[\s\S]*?MutationObserver[\s\S]*?</script>', 
            '', 
            preview_html, 
            flags=re.DOTALL
        )
        
        print(f"🗑️ Removed duplicate/old cart scripts")
        # ========== END REMOVE DUPLICATE SCRIPTS ========== 
        
        
        
        
        # ========== FIX NAVIGATION CART LINK - ADD THIS HERE ==========
        # Fix the cart link that's missing the badge
        cart_link_pattern = r'<a href="#" class="nav-link" data-page="cart">\s*Cart\s*</a>'
        
        fixed_cart_link = '<a href="cart" class="nav-link relative flex items-center gap-2 group" data-page="cart">\n                <i data-lucide="shopping-cart" class="w-4 h-4 text-purple-400"></i>\n                <span class="text-gray-300 group-hover:text-purple-400">Cart</span>\n                <span data-cart-count class="cart-count-badge hidden absolute -top-2 -right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full items-center justify-center px-1 shadow-lg shadow-purple-500/25">0</span>\n            </a>'
        
        preview_html = re.sub(cart_link_pattern, fixed_cart_link, preview_html, flags=re.DOTALL)
        
        # Also handle alternative formatting
        alt_pattern = r'<a href="#" class="nav-link"[^>]*data-page="cart"[^>]*>.*?</a>'
        preview_html = re.sub(alt_pattern, fixed_cart_link, preview_html, flags=re.DOTALL)
        
        print(f"🔧 Fixed navigation cart link - added badge and icon")




                # ============================================================
        # ========== STEP 1: FIX NAVIGATION CART LINK ==========
        # ============================================================
        
        # Fix desktop cart link (shows "0" instead of "Cart")
        broken_cart_pattern = r'<a href="cart"\s+class="nav-link group"\s+data-page="cart">\s*<span[^>]*>0</span>\s*</a>'
        
        fixed_cart_link = '<a href="cart" class="nav-link relative flex items-center gap-2 group" data-page="cart">\n                <i data-lucide="shopping-cart" class="w-4 h-4 text-purple-400"></i>\n                <span class="text-gray-300 group-hover:text-purple-400">Cart</span>\n                <span data-cart-count class="cart-count-badge hidden absolute -top-2 -right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full items-center justify-center px-1 shadow-lg shadow-purple-500/25">0</span>\n            </a>'
        
        preview_html = re.sub(broken_cart_pattern, fixed_cart_link, preview_html, flags=re.DOTALL)
        
        # Alternative pattern for different formatting
        alt_pattern = r'<a href="cart"[^>]*data-page="cart"[^>]*>\s*<span[^>]*>0</span>\s*</a>'
        preview_html = re.sub(alt_pattern, fixed_cart_link, preview_html, flags=re.DOTALL)
        
        # Fix mobile cart link
        mobile_broken = r'<a href="cart"\s+class="mobile-nav-link block[^"]*"\s+data-page="cart">\s*<span[^>]*>0</span>\s*</a>'
        fixed_mobile = '<a href="cart" class="mobile-nav-link flex items-center gap-3" data-page="cart">\n                    <i data-lucide="shopping-cart" class="w-4 h-4 text-purple-400"></i>\n                    <span class="text-gray-300">Cart</span>\n                </a>'
        preview_html = re.sub(mobile_broken, fixed_mobile, preview_html, flags=re.DOTALL)
        
        print(f"🔧 Fixed navigation cart link")
        
        
        
        
        
        
        
        
        
         # ============================================================
        # ========== STEP 2: EXTRACT PRODUCTS FROM SHOP PAGE ==========
        # ============================================================
        
        # First, isolate the shop page content - use a more precise pattern
        # Find the exact shop page div
        shop_start = preview_html.find('<div id="page_shop"')
        if shop_start != -1:
            # Find the matching closing </div> for this page
            # Count nested divs to find the correct closing tag
            search_pos = shop_start
            div_count = 0
            shop_end = -1
            
            while search_pos < len(preview_html):
                # Find next div opening or closing
                next_open = preview_html.find('<div', search_pos)
                next_close = preview_html.find('</div>', search_pos)
                
                if next_close == -1:
                    break
                
                # If we find an opening div before the closing div
                if next_open != -1 and next_open < next_close:
                    div_count += 1
                    search_pos = next_open + 4
                else:
                    div_count -= 1
                    if div_count < 0:
                        shop_end = next_close + 6
                        break
                    search_pos = next_close + 6
            
            if shop_end != -1:
                shop_content = preview_html[shop_start:shop_end]
                
                # Extract product names and prices from the shop page ONLY
                product_names = re.findall(r'<h3[^>]*>([^<]+)</h3>', shop_content)
                product_prices = re.findall(r'<p[^>]*>\$?([\d.]+)</p>', shop_content)
                
                if product_names and product_prices:
                    # Build new shop page
                    new_products_html = '<div class="grid md:grid-cols-3 gap-8">'
                    for i, (name, price) in enumerate(zip(product_names, product_prices), 1):
                        clean_price = re.sub(r'[^0-9.]', '', price)
                        try:
                            price_float = float(clean_price)
                        except:
                            price_float = 0.00
                        
                        new_products_html += f'''
                    <div class="bg-white/5 p-6 rounded-2xl border border-white/10 hover:border-purple-500/50 transition-all">
                        <h3 class="text-xl font-bold mb-2">{name.strip()}</h3>
                        <p class="text-purple-400 text-2xl font-bold mb-4">${price_float:.2f}</p>
                        <button class="add-to-cart-btn w-full py-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg hover:opacity-90 transition" 
                                data-id="{i}" 
                                data-name="{name.strip()}" 
                                data-price="{price_float:.2f}">
                            Add to Cart
                        </button>
                    </div>'''
                    new_products_html += '</div>'
                    
                    # Build the new shop page
                    new_shop_page = f'''<div id="page_shop" class="page">
                <div class="pt-32 container mx-auto px-4">
                    <h1 class="text-4xl font-bold mb-12 text-center gradient-text">Our Collection</h1>
                    {new_products_html}
                </div>
            </div>'''
                    
                    # Replace ONLY the shop page div
                    preview_html = preview_html[:shop_start] + new_shop_page + preview_html[shop_end:]
                    print(f"🛒 Rebuilt shop page with {len(product_names)} products and correct data attributes")
                else:
                    print(f"⚠️ Could not extract product names and prices from shop page")
            else:
                print(f"⚠️ Could not find shop page closing tag")
        else:
            print(f"⚠️ Could not find shop page")











        # ========== FIX NAVIGATION CART LINK ==========
        # Ensure the cart link has the correct structure
        if 'data-cart-count' not in preview_html:
            cart_link_pattern = r'<a href="cart"[^>]*data-page="cart"[^>]*>.*?</a>'
            fixed_cart_link = '<a href="cart" class="nav-link relative flex items-center gap-2 group" data-page="cart">\n                <i data-lucide="shopping-cart" class="w-4 h-4 text-purple-400"></i>\n                <span class="text-gray-300 group-hover:text-purple-400">Cart</span>\n                <span data-cart-count class="cart-count-badge hidden absolute -top-2 -right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] font-bold min-w-[18px] h-[18px] rounded-full items-center justify-center px-1 shadow-lg shadow-purple-500/25">0</span>\n            </a>'
            preview_html = re.sub(cart_link_pattern, fixed_cart_link, preview_html, flags=re.DOTALL)
            print(f"🔧 Fixed navigation cart link with badge")













        # ============================================================
        # ========== CLEAN UP EXTRA CONTENT BETWEEN PAGES ==========
        # ============================================================
        # Remove any extra closing tags and stray content between shop and cart
        preview_html = re.sub(
            r'</div>\s*</div>\s*</div>\s*<!-- Right: Order Summary -->.*?(?=<div id="page_cart")',
            '',
            preview_html,
            flags=re.DOTALL
        )
        
        # Remove any empty cart-summary divs outside cart page
        preview_html = re.sub(
            r'<div class="lg:col-span-1 mt-8 lg:mt-0">\s*</div>',
            '',
            preview_html,
            flags=re.DOTALL
        )
        
        print(f"🧹 Cleaned up extra content between pages")









        # ============================================================
        # ========== STEP 3: INJECT MASTER CART TEMPLATE ==========
        # ============================================================
        
        if is_ecommerce:
            MASTER_CART_HTML = '''
<div id="page_cart" class="page">
    <div class="min-h-screen pt-24 container mx-auto px-4 py-12">
        <h1 class="text-3xl font-bold mb-8 gradient-text">Shopping Cart (<span id="cart-total-count">0</span> items)</h1>
        
        <div class="grid lg:grid-cols-3 gap-8">
            <div class="lg:col-span-2">
                <div id="cart-items-list" class="space-y-4"></div>
                <div id="empty-cart-message-cart" class="text-center py-12">
                    <i data-lucide="shopping-bag" class="w-20 h-20 text-gray-600 mx-auto mb-6"></i>
                    <h2 class="text-2xl font-bold mb-4">Your Cart is Empty</h2>
                    <button onclick="showPage('shop')" class="btn">Continue Shopping</button>
                </div>
            </div>
            <div class="lg:col-span-1 mt-8 lg:mt-0">
                <div id="cart-summary" class="bg-white/5 rounded-xl p-6 border border-white/10 h-fit hidden">
                    <h3 class="text-xl font-bold mb-4 gradient-text">Order Summary</h3>
                    <div class="space-y-2">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Subtotal</span>
                            <span id="cart-page-subtotal" class="font-semibold">$0.00</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Shipping</span>
                            <span class="text-green-400">Free</span>
                        </div>
                    </div>
                    <div class="border-t border-white/10 my-4"></div>
                    <div class="flex justify-between font-bold text-lg mb-6">
                        <span>Total</span>
                        <span id="cart-page-total" class="text-purple-400">$0.00</span>
                    </div>
                    <button onclick="openCheckoutModal()" class="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-semibold text-white hover:opacity-90 transition duration-300">
                        Proceed to Checkout →
                    </button>
                    <button onclick="clearCart()" class="w-full mt-3 py-2 text-gray-400 hover:text-white transition text-sm">
                        Clear Cart
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>'''
            
            # Remove any existing cart page and inject master template
            preview_html = re.sub(r'<div id="page_cart"[^>]*>.*?</div>\s*(?=</main>|</div>|<div id="page_|$|<footer|</body>)', '', preview_html, flags=re.DOTALL)
            
            # Find where to insert cart page (before footer or at end of main)
            if '<footer' in preview_html:
                preview_html = preview_html.replace('<footer', f'{MASTER_CART_HTML}\n\n<footer', 1)
            elif '</main>' in preview_html:
                preview_html = preview_html.replace('</main>', f'{MASTER_CART_HTML}\n    </main>', 1)
            else:
                preview_html = preview_html.replace('</body>', f'{MASTER_CART_HTML}\n</body>', 1)
            
            print(f"🛒 Injected master cart template")
        else:
            print(f"🚫 Not e-commerce - skipping cart template injection")













        # ========== CART HTML AND SCRIPT (DEFINED OUTSIDE F-STRING) ==========
        if is_ecommerce:
            cart_html = """
<!-- Cart Sidebar -->
<div id="cart-sidebar" class="fixed right-0 top-0 h-full w-full max-w-md bg-gradient-to-br from-slate-900 to-slate-800 shadow-2xl z-50 transform translate-x-full transition-transform duration-300 flex flex-col">
    <div class="flex justify-between items-center p-4 border-b border-white/10">
        <h2 class="text-xl font-bold text-white flex items-center gap-2">
            <i class="fas fa-shopping-bag text-purple-400"></i> Your Cart
        </h2>
        <button onclick="closeCartSidebar()" class="p-2 rounded-lg hover:bg-white/10 transition-colors">
            <i class="fas fa-times text-gray-400"></i>
        </button>
    </div>
    <div id="cart-items" class="flex-1 overflow-y-auto p-4 space-y-4">
        <div class="text-center py-12 text-gray-400">Your cart is empty</div>
    </div>
    <div class="border-t border-white/10 p-4">
        <div class="flex justify-between mb-4">
            <span class="text-gray-400">Total:</span>
            <span id="cart-total" class="text-xl font-bold text-purple-400">$0.00</span>
        </div>
        <button onclick="openCheckoutModal()" class="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-semibold text-white hover:opacity-90 transition">
            Checkout
        </button>
        <button onclick="closeCartSidebar()" class="w-full mt-2 py-2 text-gray-400 hover:text-white transition text-sm">
            Continue Shopping
        </button>
    </div>
</div>

<!-- Cart Toast -->
<div id="cart-toast" class="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-2 rounded-lg shadow-lg text-sm font-medium z-50 opacity-0 transition-opacity duration-300 pointer-events-none"></div>

<!-- Checkout Modal -->
<div id="checkout-modal" class="fixed inset-0 z-50 flex items-center justify-center px-4" style="display: none;">
    <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" onclick="closeCheckoutModal()"></div>
    
    <div class="relative bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl border border-white/10 shadow-2xl max-w-sm w-full p-5">
        <div class="flex items-center gap-4 mb-4">
            <div class="w-10 h-10 shrink-0 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                <i class="fas fa-credit-card text-white text-lg"></i>
            </div>
            <div>
                <h2 class="text-xl font-bold text-white leading-tight">Checkout</h2>
                <p class="text-gray-400 text-xs">Enter payment details</p>
            </div>
        </div>

        <form id="checkout-form" onsubmit="processPayment(event)">
            <div class="space-y-3">
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-[11px] font-medium text-gray-400 uppercase mb-1">Full Name</label>
                        <input type="text" id="full-name" required placeholder="John Doe" class="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-purple-500 text-white text-sm">
                    </div>
                    <div>
                        <label class="block text-[11px] font-medium text-gray-400 uppercase mb-1">Email</label>
                        <input type="email" id="email" required placeholder="email@example.com" class="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-purple-500 text-white text-sm">
                    </div>
                </div>

                <div>
                    <label class="block text-[11px] font-medium text-gray-400 uppercase mb-1">Card Number</label>
                    <input type="text" id="card-number" required placeholder="4242 4242 4242 4242" class="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-purple-500 text-white text-sm">
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-[11px] font-medium text-gray-400 uppercase mb-1">Expiry</label>
                        <input type="text" id="expiry" required placeholder="MM/YY" maxlength="5" class="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-purple-500 text-white text-sm">
                    </div>
                    <div>
                        <label class="block text-[11px] font-medium text-gray-400 uppercase mb-1">CVV</label>
                        <input type="password" id="cvv" required placeholder="123" maxlength="4" class="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-purple-500 text-white text-sm">
                    </div>
                </div>
            </div>

            <div class="mt-5 pt-4 border-t border-white/10 flex items-center justify-between gap-4">
                <div>
                    <p class="text-[10px] text-gray-400 uppercase">Total</p>
                    <span id="checkout-total" class="font-bold text-purple-400 text-lg">$0.00</span>
                </div>
                <div class="flex-1">
                    <button type="submit" class="w-full py-2.5 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg font-semibold text-white hover:opacity-90 transition text-sm">
                        Pay Now
                    </button>
                </div>
            </div>
            
            <button type="button" onclick="closeCheckoutModal()" class="w-full mt-2 text-gray-500 hover:text-white transition text-[11px] uppercase tracking-wider">
                Cancel
            </button>
        </form>
    </div>
</div>

<!-- Success Modal -->
<div id="success-modal" class="fixed inset-0 z-50 flex items-center justify-center px-4" style="display: none;">
    <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" onclick="closeSuccessModal()"></div>
    
    <div class="relative bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl border border-white/10 shadow-2xl max-w-sm w-full p-5 text-center">
        <div class="w-12 h-12 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center mx-auto mb-3">
            <i class="fas fa-check text-white text-xl"></i>
        </div>
        
        <h2 class="text-xl font-bold text-white leading-tight">Payment Successful! 🎉</h2>
        <p class="text-gray-400 text-sm mb-4">Thanks for your order!</p>
        
        <div class="bg-white/5 rounded-lg p-3 mb-5 border border-white/5">
            <div class="flex justify-between items-center mb-1">
                <span class="text-[11px] text-gray-500 uppercase tracking-wider">Sent to:</span>
                <span id="success-email" class="text-purple-400 text-xs font-medium">email@example.com</span>
            </div>
            <div class="flex justify-between items-center pt-2 border-t border-white/5">
                <span class="text-[11px] text-gray-500 uppercase tracking-wider">Total Paid:</span>
                <span id="success-total" class="text-lg font-bold text-white">$0.00</span>
            </div>
        </div>
        
        <button onclick="closeSuccessModalAndReset()" class="w-full py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg font-semibold text-white hover:opacity-90 transition text-sm">
            Continue Shopping
        </button>
    </div>
</div>

<style>
#cart-sidebar.active { transform: translateX(0); }
#cart-sidebar { transition: transform 0.3s ease; }
#cart-toast.show { opacity: 1; }
.cart-count-badge { animation: bounceIn 0.3s ease-out; }
@keyframes bounceIn {
    0% { transform: scale(0); opacity: 0; }
    50% { transform: scale(1.2); }
    100% { transform: scale(1); opacity: 1; }
}
</style>
"""
            
            # Inject cart HTML and sidebar
            if '</body>' in preview_html:
                preview_html = preview_html.replace('</body>', f'{cart_html}\n</body>')
            
            print(f"🛒 Injected cart UI components")
        else:
            print(f"🚫 Not e-commerce - skipping cart UI injection")
        
        
        
        
        
        
        
        
      
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
             # ========== CLEAN UP STRAY CART SUMMARY IN SHOP PAGE ==========
        # Find and remove any cart-summary div that appears BEFORE the cart page
        # Pattern matches cart-summary that has a div with class lg:col-span-1
        stray_summary_pattern = r'<div class="lg:col-span-1">\s*<div id="cart-summary"[^>]*>.*?</div>\s*</div>\s*</div>\s*</div>\s*</div>(?=<div id="page_cart")'
        
        # Only apply if pattern exists
        if re.search(stray_summary_pattern, preview_html, re.DOTALL):
            preview_html = re.sub(stray_summary_pattern, '', preview_html, flags=re.DOTALL)
            print(f"🧹 Removed stray cart summary before cart page")
        
        # Also remove any duplicate cart-summary that has alert('Checkout!') in it
        preview_html = re.sub(
            r'<div[^>]*id="cart-summary"[^>]*>.*?alert\(\'Checkout!\'\).*?</div>\s*</div>\s*</div>\s*</div>',
            '',
            preview_html,
            flags=re.DOTALL
        )
        
        # Remove any cart-summary that's NOT inside page_cart (simpler approach)
        # Split by page_cart to isolate
        if '<div id="page_cart"' in preview_html:
            parts = preview_html.split('<div id="page_cart"')
            before_cart = parts[0]
            after_cart = '<div id="page_cart"' + parts[1]
            
            # Remove any cart-summary from the before_cart section
            before_cart = re.sub(
                r'<div[^>]*id="cart-summary"[^>]*>.*?</div>\s*</div>\s*</div>\s*</div>',
                '',
                before_cart,
                flags=re.DOTALL
            )
            
            # Reassemble
            preview_html = before_cart + after_cart
            print(f"🧹 Cleaned up stray cart summary from shop page")
        
        
        
        
        
        
        

        # ========== CLEAN ONERROR HANDLERS ==========
        preview_html = clean_onError_handlers(preview_html)  # ← ADD THIS LINE
        # ============================================
        
        
        
        # Fix ShieldCheck icon to use correct Font Awesome class
        preview_html = preview_html.replace('fa-shield-check', 'fa-shield-alt')       
        
        
        
        
        # ========== ADD THIS LINE - INJECT CART ICON ==========
        preview_html = inject_cart_icon_into_html(preview_html, user_prompt)
        print("🔧 Checked cart icon injection (skipped for non-ecommerce)")
        # ===================================================
        
        

        # Ensure doctype
        if not preview_html.lower().startswith("<!doctype"):
            preview_html = "<!DOCTYPE html>\n" + preview_html
            
            
            
            
            
            
            
            
            
            
            

        # Inject base64 images - Use Cloudinary URLs instead of huge base64 strings
        image_urls_cache = {}
        
        for file_key, content in files.items():
            if file_key.startswith("public/images/") and isinstance(content, str) and content.startswith("__binary_base64__"):
                public_path = "/" + file_key[len("public/"):]
                
                # Upload to Cloudinary and get URL (cached)
                cloudinary_url = await get_cloudinary_url_for_preview(file_key, content)
                
                if cloudinary_url:
                    image_urls_cache[public_path] = cloudinary_url
                    preview_html = preview_html.replace(f'src="{public_path}"', f'src="{cloudinary_url}"')
                    preview_html = preview_html.replace(f"src='{public_path}'", f'src="{cloudinary_url}"')
                    print(f"  ✅ Replaced {public_path} with Cloudinary URL")
                else:
                    # Fallback to base64 if Cloudinary fails
                    raw_b64 = content[len("__binary_base64__"):]
                    data_uri = f"data:image/jpeg;base64,{raw_b64}"
                    preview_html = preview_html.replace(f'src="{public_path}"', f'src="{data_uri}"')
                    preview_html = preview_html.replace(f"src='{public_path}'", f'src="{data_uri}"')
                    print(f"  ⚠️ Cloudinary failed, using base64 for {public_path}")
        
        # If no images were processed, use gradient background
        if not image_urls_cache:
            print("⚠️ No images available, using gradient background for hero")























        # ============================================================
        # ========== STEP 4: INJECT MASTER CART SCRIPT ==========
        # ============================================================
        
        # ========== ONLY INJECT FOR E-COMMERCE ==========
        if is_ecommerce:
            # Remove any existing cart scripts
            preview_html = re.sub(r'<script>\s*// ========== CART SYSTEM ==========.*?</script>', '', preview_html, flags=re.DOTALL)
            preview_html = re.sub(r'<script>\s*// ========== MASTER CART SYSTEM ==========.*?</script>', '', preview_html, flags=re.DOTALL)
            
            # Remove scripts that start with // ========== CART SYSTEM ==========
            preview_html = re.sub(
                r'<script>\s*// ========== CART SYSTEM ==========.*?</script>',
                '',
                preview_html,
                flags=re.DOTALL
            )
            
            # Remove scripts containing cart-page-items (THE WRONG ID)
            preview_html = re.sub(
                r'<script[^>]*>[\s\S]*?cart-page-items[\s\S]*?</script>',
                '',
                preview_html,
                flags=re.DOTALL
            )
            
            # Remove scripts containing empty-cart-message (without -cart)
            preview_html = re.sub(
                r'<script[^>]*>[\s\S]*?empty-cart-message[^-][\s\S]*?</script>',
                '',
                preview_html,
                flags=re.DOTALL
            )
            
            # Remove scripts that have wireAddToCartButtons but NOT "MASTER"
            preview_html = re.sub(
                r'<script[^>]*>(?:(?!MASTER CART SYSTEM)[\s\S])*?wireAddToCartButtons[\s\S]*?</script>',
                '',
                preview_html,
                flags=re.DOTALL
            )
            
            print(f"🗑️ Force removed all old cart scripts")
            
            
            
            
            
            
            
            
            
            
            MASTER_CART_SCRIPT = '''
<script>
// ========== MASTER CART SYSTEM ==========
let cart = [];

try {
    const saved = localStorage.getItem('eaglecode_cart');
    if (saved) cart = JSON.parse(saved);
} catch(e) { console.error('Failed to load cart:', e); }

function saveCart() {
    localStorage.setItem('eaglecode_cart', JSON.stringify(cart));
    updateCartUI();
    updateCartBadge();
    updateCartPage();
}

function updateCartBadge() {
    const totalItems = cart.reduce((sum, i) => sum + (i.quantity || 1), 0);
    document.querySelectorAll('[data-cart-count]').forEach(badge => {
        if (totalItems > 0) {
            badge.textContent = totalItems > 99 ? '99+' : totalItems;
            badge.classList.remove('hidden');
            badge.classList.add('flex');
        } else {
            badge.classList.add('hidden');
            badge.classList.remove('flex');
        }
    });
}

function updateCartUI() {
    const container = document.getElementById('cart-items');
    const totalEl = document.getElementById('cart-total');
    if (!container) return;
    if (cart.length === 0) {
        container.innerHTML = '<div class="text-center py-12 text-gray-400">Your cart is empty</div>';
        if (totalEl) totalEl.textContent = '$0.00';
        return;
    }
    const total = cart.reduce((sum, i) => sum + (i.price * (i.quantity || 1)), 0);
    container.innerHTML = cart.map(item => {
        const safeName = (item.name || '').replace(/[&<>]/g, function(m) {
            return m === '&' ? '&amp;' : (m === '<' ? '&lt;' : '&gt;');
        });
        const qty = item.quantity || 1;
        return `
            <div class="flex gap-4 p-3 bg-white/5 rounded-xl border border-white/10">
                <div class="flex-1">
                    <h4 class="font-semibold text-white text-sm">${safeName}</h4>
                    <p class="text-purple-400 text-sm">$${(item.price || 0).toFixed(2)}</p>
                    <div class="flex items-center gap-2 mt-2">
                        <button onclick="updateQuantity('${item.id}', -1)" class="w-6 h-6 rounded-full bg-white/10 hover:bg-white/20">-</button>
                        <span class="text-white text-sm w-6 text-center">${qty}</span>
                        <button onclick="updateQuantity('${item.id}', 1)" class="w-6 h-6 rounded-full bg-white/10 hover:bg-white/20">+</button>
                        <button onclick="removeFromCart('${item.id}')" class="ml-auto text-red-400 hover:text-red-300 text-sm">Remove</button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    if (totalEl) totalEl.textContent = `$${total.toFixed(2)}`;
}

function updateCartPage() {
    const container = document.getElementById('cart-items-list');
    const summary = document.getElementById('cart-summary');
    const emptyMsg = document.getElementById('empty-cart-message-cart');
    const totalCountSpan = document.getElementById('cart-total-count');
    if (!container) return;
    if (cart.length === 0) {
        if (summary) summary.classList.add('hidden');
        if (emptyMsg) emptyMsg.classList.remove('hidden');
        if (container) container.classList.add('hidden');
        if (totalCountSpan) totalCountSpan.textContent = '0';
        container.innerHTML = '';
        return;
    }
    if (summary) summary.classList.remove('hidden');
    if (emptyMsg) emptyMsg.classList.add('hidden');
    if (container) container.classList.remove('hidden');
    const total = cart.reduce((sum, i) => sum + (i.price * (i.quantity || 1)), 0);
    const totalItems = cart.reduce((sum, i) => sum + (i.quantity || 1), 0);
    if (totalCountSpan) totalCountSpan.textContent = totalItems;
    container.innerHTML = cart.map(item => {
        const qty = item.quantity || 1;
        return `
            <div class="flex gap-4 p-4 bg-white/5 rounded-xl border border-white/10">
                <div class="flex-1">
                    <h3 class="font-semibold text-white">${(item.name || '').replace(/[&<>]/g, function(m) {
                        return m === '&' ? '&amp;' : (m === '<' ? '&lt;' : '&gt;');
                    })}</h3>
                    <p class="text-purple-400">$${(item.price || 0).toFixed(2)}</p>
                    <div class="flex items-center gap-3 mt-2">
                        <button onclick="updateQuantity('${item.id}', -1)" class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20">-</button>
                        <span>${qty}</span>
                        <button onclick="updateQuantity('${item.id}', 1)" class="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20">+</button>
                        <button onclick="removeFromCart('${item.id}')" class="ml-auto text-red-400 hover:text-red-300">Remove</button>
                    </div>
                </div>
                <p class="font-bold text-lg">$${(item.price * qty).toFixed(2)}</p>
            </div>
        `;
    }).join('');
    const subtotalEl = document.getElementById('cart-page-subtotal');
    const totalEl = document.getElementById('cart-page-total');
    if (subtotalEl) subtotalEl.textContent = '$' + total.toFixed(2);
    if (totalEl) totalEl.textContent = '$' + total.toFixed(2);
}

window.addToCart = function(id, name, price) {
    const existing = cart.find(i => i.id === id);
    if (existing) {
        existing.quantity = (existing.quantity || 1) + 1;
    } else {
        cart.push({ id: String(id), name: name, price: Number(price), quantity: 1 });
    }
    saveCart();
    const toast = document.getElementById('cart-toast');
    if (toast) {
        toast.textContent = name + ' added to cart!';
        toast.classList.add('show');
        setTimeout(function() { toast.classList.remove('show'); }, 2000);
    }
    if (window.innerWidth <= 768 && typeof openCartSidebar === 'function') openCartSidebar();
};

window.updateQuantity = function(id, delta) {
    const item = cart.find(i => i.id === id);
    if (item) {
        const newQty = (item.quantity || 1) + delta;
        if (newQty <= 0) {
            cart = cart.filter(i => i.id !== id);
        } else {
            item.quantity = newQty;
        }
        saveCart();
    }
};

window.removeFromCart = function(id) {
    cart = cart.filter(i => i.id !== id);
    saveCart();
    const toast = document.getElementById('cart-toast');
    if (toast) {
        toast.textContent = 'Item removed from cart';
        toast.classList.add('show');
        setTimeout(function() { toast.classList.remove('show'); }, 2000);
    }
};

window.clearCart = function() {
    if (confirm('Are you sure you want to clear your entire cart?')) {
        cart = [];
        saveCart();
        const toast = document.getElementById('cart-toast');
        if (toast) {
            toast.textContent = 'Cart cleared';
            toast.classList.add('show');
            setTimeout(function() { toast.classList.remove('show'); }, 2000);
        }
    }
};

function openCartSidebar() {
    const sidebar = document.getElementById('cart-sidebar');
    if (sidebar) sidebar.classList.add('active');
}

window.closeCartSidebar = function() {
    const sidebar = document.getElementById('cart-sidebar');
    if (sidebar) sidebar.classList.remove('active');
};

// ========== CHECKOUT FUNCTIONS ==========
function openCheckoutModal() {
    if (cart.length === 0) {
        const toast = document.getElementById('cart-toast');
        if (toast) {
            toast.textContent = 'Your cart is empty';
            toast.classList.add('show');
            setTimeout(function() { toast.classList.remove('show'); }, 2000);
        }
        return;
    }
    const total = cart.reduce(function(s, i) { return s + (i.price * (i.quantity || 1)); }, 0);
    const checkoutTotal = document.getElementById('checkout-total');
    if (checkoutTotal) checkoutTotal.textContent = '$' + total.toFixed(2);
    const modal = document.getElementById('checkout-modal');
    if (modal) modal.style.display = 'flex';
}

function closeCheckoutModal() {
    const modal = document.getElementById('checkout-modal');
    if (modal) modal.style.display = 'none';
    const form = document.getElementById('checkout-form');
    if (form) form.reset();
}

function closeSuccessModal() {
    const modal = document.getElementById('success-modal');
    if (modal) modal.style.display = 'none';
}

function closeSuccessModalAndReset() {
    closeSuccessModal();
    cart = [];
    saveCart();
    if (typeof showPage === 'function') showPage('shop');
}

function processPayment(event) {
    event.preventDefault();
    const fullName = document.getElementById('full-name');
    const email = document.getElementById('email');
    
    if (!fullName.value || !email.value) {
        const toast = document.getElementById('cart-toast');
        if (toast) {
            toast.textContent = 'Please fill in all fields';
            toast.classList.add('show');
            setTimeout(function() { toast.classList.remove('show'); }, 2000);
        }
        return;
    }
    if (!email.value.includes('@')) {
        const toast = document.getElementById('cart-toast');
        if (toast) {
            toast.textContent = 'Please enter a valid email';
            toast.classList.add('show');
            setTimeout(function() { toast.classList.remove('show'); }, 2000);
        }
        return;
    }
    
    const total = cart.reduce(function(s, i) { return s + (i.price * (i.quantity || 1)); }, 0);
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    submitBtn.disabled = true;
    
    setTimeout(function() {
        closeCheckoutModal();
        const successEmail = document.getElementById('success-email');
        const successTotal = document.getElementById('success-total');
        if (successEmail) successEmail.textContent = email.value;
        if (successTotal) successTotal.textContent = '$' + total.toFixed(2);
        const successModal = document.getElementById('success-modal');
        if (successModal) successModal.style.display = 'flex';
        cart = [];
        saveCart();
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
        const toast = document.getElementById('cart-toast');
        if (toast) {
            toast.textContent = 'Payment successful! Thank you!';
            toast.classList.add('show');
            setTimeout(function() { toast.classList.remove('show'); }, 2000);
        }
    }, 1500);
}

// ========== INITIALIZE CART ON PAGE LOAD ==========
function wireAddToCartButtons() {
    document.querySelectorAll('.add-to-cart-btn').forEach(function(btn) {
        if (!btn.hasAttribute('data-wired')) {
            btn.setAttribute('data-wired', 'true');
            const id = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name');
            const price = parseFloat(btn.getAttribute('data-price'));
            btn.onclick = function(e) {
                e.preventDefault();
                if (id && name && !isNaN(price)) {
                    addToCart(id, name, price);
                } else {
                    console.error('Missing data attributes:', {id, name, price});
                }
            };
        }
    });
}

// Initialize when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        updateCartUI();
        updateCartBadge();
        updateCartPage();
        wireAddToCartButtons();
        console.log('🛒 Cart initialized with', document.querySelectorAll('.add-to-cart-btn').length, 'buttons');
    });
} else {
    updateCartUI();
    updateCartBadge();
    updateCartPage();
    wireAddToCartButtons();
    console.log('🛒 Cart initialized with', document.querySelectorAll('.add-to-cart-btn').length, 'buttons');
}

// Also watch for dynamically added buttons
if (window.MutationObserver) {
    const observer = new MutationObserver(function() {
        wireAddToCartButtons();
    });
    observer.observe(document.body, { childList: true, subtree: true });
}
</script>'''
            
            # Inject master cart script before closing body
            if '</body>' in preview_html:
                preview_html = preview_html.replace('</body>', MASTER_CART_SCRIPT + '\n</body>')
            else:
                preview_html = preview_html + MASTER_CART_SCRIPT
            
            print(f"🛒 Injected master cart JavaScript")
        else:
            print(f"🚫 Not e-commerce - skipping cart script injection")

        # ========== AUTH HANDLER SCRIPT ==========
        auth_script = f"""
<script>
const BACKEND_URL = "{BACKEND_URL}";

// Get connection string directly from localStorage
function getDbConnection() {{
    let conn = localStorage.getItem("neon_db_connection");
    if (!conn) {{
        conn = sessionStorage.getItem("neon_db_connection");
    }}
    return conn;
}}

async function handleSignup(event) {{
    event.preventDefault();
    const form = event.target;
    const name = form.querySelector('[name="name"], [name="fullName"]')?.value || '';
    const email = form.querySelector('[name="email"]')?.value;
    const password = form.querySelector('[name="password"]')?.value;
    const confirmPassword = form.querySelector('[name="confirmPassword"]')?.value;
    
    // Get connection string directly
    const dbConnection = getDbConnection();
    console.log("🔑 DB Connection found:", dbConnection ? "Yes ✅" : "No ❌");
    
    if (!dbConnection) {{
        alert('❌ Database not connected. Please add your Neon DB connection string first.\\n\\nOpen console and run:\\nlocalStorage.setItem("neon_db_connection", "your-connection-string")');
        return;
    }}
    
    if (password !== confirmPassword) {{
        alert('❌ Passwords do not match');
        return;
    }}
    if (password.length < 6) {{
        alert('❌ Password must be at least 6 characters');
        return;
    }}
    
    const submitBtn = form.querySelector('[type="submit"]');
    const originalText = submitBtn?.innerText || 'Sign Up';
    if (submitBtn) submitBtn.innerText = 'Creating account...';
    
    try {{
        const response = await fetch(`${{BACKEND_URL}}/api/auth/signup`, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ 
                name, 
                email, 
                password, 
                db_connection_string: dbConnection 
            }})
        }});
        const data = await response.json();
        console.log("📡 Signup response:", data);
        
        if (data.success) {{
            alert('✅ Account created successfully! You can now log in.');
            form.reset();
            setTimeout(() => {{
                const loginLink = document.querySelector('a[href="/login"]');
                if (loginLink && typeof showPage === 'function') {{
                    showPage('login');
                }}
            }}, 1500);
        }} else if (data.requires_db) {{
            alert('❌ Database not configured. Please add your Neon DB connection string first.');
        }} else {{
            alert('❌ ' + (data.error || 'Signup failed'));
        }}
    }} catch (error) {{
        console.error('Signup error:', error);
        alert('❌ Network error. Make sure backend is running');
    }} finally {{
        if (submitBtn) submitBtn.innerText = originalText;
    }}
}}

async function handleLogin(event) {{
    event.preventDefault();
    const form = event.target;
    const email = form.querySelector('[name="email"]')?.value;
    const password = form.querySelector('[name="password"]')?.value;
    
    // Get connection string directly
    const dbConnection = getDbConnection();
    if (!dbConnection) {{
        alert('❌ Database not connected. Please add your Neon DB connection string first.');
        return;
    }}
    
    const submitBtn = form.querySelector('[type="submit"]');
    const originalText = submitBtn?.innerText || 'Login';
    if (submitBtn) submitBtn.innerText = 'Logging in...';
    
    try {{
        const response = await fetch(`${{BACKEND_URL}}/api/auth/login`, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ 
                email, 
                password, 
                db_connection_string: dbConnection 
            }})
        }});
        const data = await response.json();
        
        if (data.success) {{
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            alert('✅ Login successful! Welcome ' + (data.user.name || data.user.email));
            setTimeout(() => {{
                if (typeof showPage === 'function') showPage('home');
            }}, 1000);
        }} else if (data.requires_db) {{
            alert('❌ Database not configured. Please add your Neon DB connection string first.');
        }} else {{
            alert('❌ ' + (data.error || 'Login failed'));
        }}
    }} catch (error) {{
        console.error('Login error:', error);
        alert('❌ Network error. Make sure backend is running');
    }} finally {{
        if (submitBtn) submitBtn.innerText = originalText;
    }}
}}

// Listen for database connection from parent window (for iframe preview)
window.addEventListener('message', function(event) {{
    if (event.data && event.data.type === 'SET_DB_CONNECTION') {{
        localStorage.setItem('neon_db_connection', event.data.db_connection);
        console.log('✅ DB Connection received from parent');
    }}
}});

document.addEventListener('DOMContentLoaded', function() {{
    // Request connection string from parent if not present
    if (!getDbConnection() && window.parent !== window) {{
        window.parent.postMessage({{ type: 'GET_DB_CONNECTION' }}, '*');
    }}
    
    document.querySelectorAll('form').forEach(form => {{
        const hasPassword = form.querySelector('[type="password"]');
        const hasEmail = form.querySelector('[type="email"]');
        const submitText = form.querySelector('[type="submit"]')?.innerText?.toLowerCase() || '';
        const formId = form.id?.toLowerCase() || '';
        
        const isSignupForm = formId.includes('signup') || submitText.includes('sign') || submitText.includes('up') || (form.querySelector('[name="name"]') && hasPassword && hasEmail);
        const isLoginForm = formId.includes('login') || submitText.includes('log') || submitText.includes('in') || (!form.querySelector('[name="name"]') && hasPassword && hasEmail);
        
        if ((isSignupForm || isLoginForm) && !form.onsubmit) {{
            if (isSignupForm) form.onsubmit = handleSignup;
            else if (isLoginForm) form.onsubmit = handleLogin;
        }}
    }});
}});
</script>
"""

        # ========== INJECT AUTH SCRIPT ONLY ==========
        # Inject auth script (always needed for signup/login pages)
        if '</body>' in preview_html:
            preview_html = preview_html.replace('</body>', f'{auth_script}\n</body>')
        else:
            preview_html = preview_html + auth_script
            
        # Fix ShieldCheck icon one more time to be safe
        preview_html = preview_html.replace('fa-shield-check', 'fa-shield-alt')           






        
        
        
        # ⭐⭐⭐ INJECT RESTAURANT FEATURES (ONLY FOR RESTAURANT WEBSITES) ⭐⭐⭐
        # Use STRICT detection - require explicit restaurant indicators
        should_inject_restaurant = False
        
        # Method 1: Check user prompt for explicit restaurant keywords
        explicit_restaurant_keywords = ['restaurant', 'cafe', 'bistro', 'eatery', 'steakhouse', 'food truck', 'diner', 'fine dining']
        if any(keyword in user_prompt.lower() for keyword in explicit_restaurant_keywords):
            should_inject_restaurant = True
            print("🍽️ Explicit restaurant keywords found in prompt")
        # Method 2: Check for restaurant-specific page IDs (strong indicator)
        elif is_restaurant_detected and ('page_reservations' in preview_html or 'page_menu' in preview_html):
            should_inject_restaurant = True
            print("🍽️ Restaurant pages detected in HTML")
        # Method 3: Check for reservation form elements
        elif 'reservation-form' in preview_html or 'restaurantBookingForm' in preview_html:
            should_inject_restaurant = True
            print("🍽️ Reservation form detected in HTML")
        
        if should_inject_restaurant and not is_dashboard_detected:
            preview_html = inject_restaurant_features(preview_html, brand_name, user_prompt)
            print("🍽️ Restaurant features injected")
        elif is_dashboard_detected:
            print("📊 Dashboard detected - skipping restaurant features injection")
        else:
            print("🚫 Not a restaurant website - skipping restaurant features injection")
            
            
            
            

        if not is_dashboard_detected and is_restaurant_detected:
            print("📅 Reservation features already handled by inject_restaurant_features()")




        # ========== CHECK HOME PAGE CONTENT - SKIP INJECTIONS IF ALREADY EXISTS ==========
        homepage_source = files.get("app/page.tsx", "")
        
        # Check if home page already has features and FAQ
        has_features = 'const features' in homepage_source or 'features.map' in homepage_source
        has_faq = 'const faqs' in homepage_source or 'faqs.map' in homepage_source
        
        print(f"\n📋 HOME PAGE CONTENT CHECK:")
        print(f"   Features in source: {has_features}")
        print(f"   FAQ in source: {has_faq}")
        
        # Only inject trust badges (these sometimes get lost in conversion)
        preview_html = inject_trust_indicators(preview_html, files, user_prompt)
        
        
        # Inject hero padding fix to prevent header overlap
        preview_html = inject_hero_padding_fix(preview_html)
        
        # Skip FAQ injection if already in home page
        if has_faq:
            print("  ✅ FAQ already in home page - skipping injection")
        else:
            print("  🔧 FAQ missing - would inject (if needed)")
        
        
        
        # Skip Features injection if already in home page
        if has_features:
            print("  ✅ Features already in home page - skipping injection")
        else:
            print("  🔧 Features missing - would inject (if needed)")
            
            
            
            
            
            
            
        # ==================== STRICT DASHBOARD ENFORCEMENT (CONDITIONAL) ====================
        # Use the already detected value, don't recalculate
        if is_dashboard_detected:
            preview_html = enforce_strict_dashboard_rules(preview_html)
            print("🔒 Strict dashboard rules enforced")
        else:
            print("✅ Dashboard rules skipped (not a dashboard project)")

        preview_html = enforce_body_background(preview_html)
            
            
            
            
            
            

        print(f"✅ Beautiful preview generated! Length: {len(preview_html):,} chars")
        return {"success": True, "preview_html": preview_html, "preview_type": "ai_full"}
    
    
    

    except Exception as e:
        print(f"❌ AI Preview Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}
    
    
    
    
  


