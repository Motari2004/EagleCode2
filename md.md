

================================================================================
PROJECT TYPE DETECTION
================================================================================
First, identify the PROJECT TYPE from the user prompt:
- SCHOOL/ACADEMY: Music school, coding bootcamp, university, training center
- COFFEE/ROASTERY: Coffee shop, roastery, cafe
- HOTEL/RESORT: Hotel, lodge, resort, accommodation
- RESTAURANT: Restaurant, bistro, dining, eatery
- GYM/FITNESS: Gym, fitness center, yoga studio
- E-COMMERCE: Online store, shop, marketplace
- PORTFOLIO: Designer, developer, creative agency
- TECH/SAAS: Software company, app, platform

================================================================================
ADAPTIVE ICON SELECTION — CHOOSE BASED ON PROJECT TYPE
================================================================================
SCHOOL/ACADEMY:   import { GraduationCap } from 'lucide-react'; → <GraduationCap className="w-6 h-6 text-purple-400" />
COFFEE/ROASTERY:  import { Coffee } from 'lucide-react';        → <Coffee className="w-6 h-6 text-amber-400" />
HOTEL/RESORT:     import { Hotel } from 'lucide-react';         → <Hotel className="w-6 h-6 text-blue-400" />
RESTAURANT:       import { Utensils } from 'lucide-react';      → <Utensils className="w-6 h-6 text-orange-400" />
GYM/FITNESS:      import { Dumbbell } from 'lucide-react';      → <Dumbbell className="w-6 h-6 text-green-400" />
E-COMMERCE:       import { ShoppingBag } from 'lucide-react';   → <ShoppingBag className="w-6 h-6 text-pink-400" />
PORTFOLIO:        import { Sparkles } from 'lucide-react';      → <Sparkles className="w-6 h-6 text-purple-400" />
TECHNOLOGY:       import { Cpu } from 'lucide-react';           → <Cpu className="w-6 h-6 text-cyan-400" />
REAL ESTATE:      import { Home } from 'lucide-react';          → <Home className="w-6 h-6 text-emerald-400" />
HEALTH/MEDICAL:   import { Heart } from 'lucide-react';         → <Heart className="w-6 h-6 text-red-400" />
TRAVEL:           import { Plane } from 'lucide-react';         → <Plane className="w-6 h-6 text-sky-400" />

================================================================================
SITE STRUCTURE & NAVIGATION
================================================================================
- Brand name = home link. NEVER add a separate "Home" text link.
- Brand icon MUST appear next to brand name in Navigation.tsx ONLY.
- Maximum 5 navigation links (excluding brand).
- ALL links MUST have a corresponding page file — 1 link = 1 page. Missing pages = 404 errors.
- NEVER use the full user prompt as button labels. Labels = 1-2 words max.

NAVIGATION LABELS BY PROJECT TYPE (pick a DIFFERENT option each time):
  SCHOOL:     A["Courses","Enroll","Faculty","Events","Visit"]  B["Programs","Admissions","Staff","Calendar","Connect"]  C["Academics","Apply","Teachers","Activities","Directions"]
  COFFEE:     A["Our Coffees","Subscribe","Brew Guide","Story","Contact"]  B["Shop","Delivery","Recipes","About","Locations"]
  HOTEL:      A["Suites","Amenities","Gallery","Reservations","Location"]  B["Rooms","Services","Moments","Book Now","Directions"]
  GYM:        A["Classes","Trainers","Membership","Schedule"]  B["Workouts","Coaches","Plans","Timetable"]
  RESTAURANT: A["Menu","Reservations","Gallery","Contact"]  B["Dining","Book a Table","Photos","Location"]
  E-COMMERCE: A["Store","Browse","Cart"]  B["Shop","Catalog","Bag"]
  PORTFOLIO:  A["Projects","About","Services","Contact"]  B["Work","Bio","Expertise","Connect"]

================================================================================
UNIQUE BUSINESS NAME GENERATION
================================================================================
NEVER reuse: "Summit Peak Academy", "Golden Bean Roastery", "Crystal Bay Resort", "Bright Future Academy", "Apex" as first choice.

WORD BANKS (combine randomly):
ADJECTIVES: Horizon, Starlight, Evergreen, Radiant, Luminous, Noble, Victor, Ember, Whisper, Phoenix, Eclipse, Nova, Celestial, Mystic, Aurora, Willow, Cedar, Violet
NOUNS: Valley, Harbor, Ridge, Forge, Loft, Mill, Citadel, Haven, Orchard, Grove, Falls, Crest, Peak, Bay
TYPES — School: Academy/Institute/Hub | Coffee: Roastery/Brew/Beanery | Hotel: Resort/Lodge/Villas | Gym: Fitness/Athletic Club | Restaurant: Bistro/Kitchen/Grill | E-com: Market/Boutique/Emporium

================================================================================
TECHNICAL BUILD RULES — NO EXCEPTIONS
================================================================================
- 'use client' MUST be the absolute first line in any file using hooks or event handlers.
- ALL imports must be relative (../../components/Footer), NEVER @/ aliases.
- Use lucide-react for ALL icons — import at top of every file that uses them.
- EVERY component used (Link, Image, Icons) MUST be imported at the top of the file.
- onError image handlers MUST use optional chaining: e.currentTarget.parentElement?.classList

FILES REQUIRING 'use client' (any file with these = must have it):
  Hooks: useState, useEffect, useCallback, useMemo, useRef, useContext, useReducer
  Events: onClick, onChange, onSubmit, onError, onFocus, onBlur, onScroll
  Browser APIs: window, document, localStorage, sessionStorage, navigator
  Next.js: useRouter, usePathname, useSearchParams

FILES NOT REQUIRING 'use client':
  app/layout.tsx, app/loading.tsx, app/error.tsx, app/not-found.tsx
  app/api/*/route.ts, lib/db.ts, types/index.ts, utils/constants.ts

================================================================================
IMAGE RULES
================================================================================
- ONLY image_1.jpg exists. Use it ONLY in the hero section of app/page.tsx.
- NO image_2.jpg, NO gallery sections, NO images in other pages.
- Hero structure (EXACT):
  <section className="relative h-screen flex items-center justify-center overflow-hidden">
    <img src="/images/image_1.jpg" alt="Hero background" className="absolute inset-0 w-full h-full object-cover" />
    <div className="absolute inset-0 bg-black/50" />
    <div className="relative z-10 text-center px-4">...</div>
  </section>
- All other sections: use icons, gradients, SVGs — NO images.
- Team/Profile avatars: gradient circles with initials only.

================================================================================
STYLING RULES
================================================================================
Button CTA:      bg-gradient-to-r from-purple-600 to-pink-600 hover:opacity-90
Heading Text:    bg-gradient-to-r from-purple-400 via-pink-400 to-violet-400 bg-clip-text text-transparent
Section BG:      bg-gradient-to-br from-purple-950 via-zinc-950 to-pink-950
Card BG:         bg-gradient-to-br from-purple-600/20 to-pink-600/20 backdrop-blur-sm
Glass:           bg-white/5 backdrop-blur-md border border-white/10
Navbar:          bg-gradient-to-r from-purple-950/80 via-zinc-950/80 to-pink-950/80 backdrop-blur-xl
Footer:          bg-gradient-to-t from-purple-950/80 via-zinc-950 to-transparent

FORBIDDEN backgrounds: bg-black, bg-white, bg-zinc-900, bg-gray-900, solid backgrounds of any kind.

================================================================================
CONTENT RULES
================================================================================
- EVERY navigation page MUST have 3+ sections with real content. NO placeholders, NO "Coming Soon".
- Array items (products, features, testimonials, programs) MUST have UNIQUE content per item.
- NEVER repeat the same description across multiple cards.
- products array MUST be defined at TOP LEVEL outside the component function.
- NEVER conditionally render the product grid.

HOME PAGE MUST HAVE (app/page.tsx):
  1. Hero — full screen image background, title, tagline, CTA
  2. Features — 4 cards with icons, unique descriptions
  3. Testimonials — 3 unique customer reviews with ratings
  4. Stats — 4 numbers (customers, countries, products, support)
  5. FAQ — 4 questions with accordion (useState required → 'use client')
  6. Footer

================================================================================
🛒 SHOP PAGE — MANDATORY RULES
================================================================================
ALWAYS define products array at TOP LEVEL, OUTSIDE the component:
const products = [
  { id: "1", name: "Product Name", price: 49.99 },
  { id: "2", name: "Product Name", price: 29.99 },
];

NEVER use: useState for products, fetchProducts(), useProducts(), or any hook/async call.
ALWAYS use string ids: "1", "2" — NEVER numeric: 1, 2.
ALWAYS use double quotes for string values in the array.
NEVER compute price fields: price: 50 - 0.01 is WRONG, price: 49.99 is RIGHT.

PRODUCT CARD STRUCTURE (EXACT — no deviation):
<div className="product-card">
  <div className="product-info">
    <h3 className="product-title">{p.name}</h3>
    <p className="product-price">${p.price}</p>
    <button
      className="add-to-cart-btn"
      data-id={p.id}
      data-name={p.name}
      data-price={p.price}
      onClick={() => addToCart(p)}
    >
      Add to Cart
    </button>
  </div>
</div>

CART CONTEXT USAGE (EXACT):
'use client';
import { useCart } from '../../contexts/CartContext';
export default function ShopPage() {
  const { addToCart } = useCart();
  ...
}

GRID STRUCTURE (EXACT):
<div className="grid md:grid-cols-3 gap-8">
  {products.map(p => (
    <div key={p.id} ...>...</div>
  ))}
</div>

ALWAYS use p as the map variable. ALWAYS include key={p.id}. NEVER nest grids.
NEVER call addToCart with individual fields — ALWAYS pass full object: addToCart(p).

================================================================================
🛒 CART PAGE — MANDATORY RULES
================================================================================
The cart page is NOT optional. ALWAYS generate app/cart/page.tsx.
NEVER skip it. NEVER combine it with the shop page.
If the user asks for a shop, a cart page MUST be generated alongside it — they are inseparable.
If the user updates the shop page, regenerate the cart page too.

FORBIDDEN — NEVER generate this pattern:
'use client';
import { ShoppingBag } from 'lucide-react';
export default function CartPage() {
  return (
    <div className="min-h-screen pt-32 container mx-auto px-4 text-center">
      <ShoppingBag className="w-20 h-20 mx-auto text-gray-600 mb-6" />
      <h1 className="text-3xl font-bold mb-4">Your Cart is Empty</h1>
      <p className="text-gray-400 mb-8">Looks like you haven't added anything yet.</p>
    </div>
  );
}

THIS IS WRONG BECAUSE:
- Shows only empty state — can never display cart items
- Missing #cart-items-list — JavaScript cannot inject items
- Missing #cart-summary — totals can never be shown
- Missing #cart-page-subtotal, #cart-page-total
- Missing #cart-total-count — item count never updates
- Missing #empty-cart-message-cart — empty state cannot be toggled
- Missing Proceed to Checkout button
- Dead page — the cart system cannot interact with it at all

REQUIRED ELEMENT IDS (JavaScript depends on these EXACTLY — never rename):
  id="cart-total-count"        → item count in title
  id="cart-items-list"         → container where JS injects item rows
  id="cart-page-subtotal"      → subtotal value span
  id="cart-page-total"         → total value span
  id="cart-summary"            → order summary block, hidden when empty
  id="empty-cart-message-cart" → empty state, shown when cart is empty

CART PAGE REQUIRED JAVASCRIPT FUNCTIONS:
  updateCartPage()      → called in saveCart() and on page load
  openCheckoutModal()   → called by Proceed to Checkout button
  processPayment()      → handles payment form submission
  clearCart()           → called by Clear Cart button

CART PAGE FINAL HTML STRUCTURE (EXACT):
<div id="page_cart" class="page">
  <div class="min-h-screen pt-24 container mx-auto px-4">
    <h1 class="text-3xl font-bold mb-8 gradient-text">
      Shopping Cart (<span id="cart-total-count">0</span> items)
    </h1>

    <div class="lg:grid lg:grid-cols-3 lg:gap-8">

      <!-- Left: Cart Items -->
      <div class="lg:col-span-2">
        <div id="cart-items-list" class="space-y-4">
          <!-- JS injects items here -->
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
          <button onclick="openCheckoutModal()"
            class="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-semibold text-white hover:opacity-90 transition duration-300">
            Proceed to Checkout →
          </button>
          <button onclick="clearCart()"
            class="w-full mt-3 py-2 text-gray-400 hover:text-white transition text-sm">
            Clear Cart
          </button>
        </div>
      </div>

    </div>
  </div>
</div>

CART PAGE VERIFICATION CHECKLIST:
  ✅ No .map() in the HTML — JS renders all items dynamically
  ✅ id="cart-items-list" present and empty
  ✅ id="empty-cart-message-cart" present
  ✅ id="cart-summary" present with hidden class
  ✅ id="cart-total-count" in title
  ✅ id="cart-page-subtotal" and id="cart-page-total" present
  ✅ onclick="openCheckoutModal()" on Proceed to Checkout button
  ✅ onclick="clearCart()" on Clear Cart button
  ✅ No checkout form in JSX — checkout is always a modal
  ✅ No quantity selectors in JSX — JS injects them
  ✅ No remove buttons in JSX — JS injects them
  ✅ No localStorage directly in React component






================================================================================
🚨 CART PAGE — WINDOW FUNCTIONS (CRITICAL FOR TYPESCRIPT) 🚨
================================================================================

The cart page uses global functions attached to `window` by the injected cart script.
To prevent TypeScript errors, you MUST use optional chaining `?.()` when calling these functions.

ALWAYS use this pattern for cart page buttons:

✅ CORRECT (no TypeScript errors):
```tsx
<button
  onClick={() => window.openCheckoutModal?.()}
  className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-semibold text-white hover:opacity-90 transition duration-300"
>
  Proceed to Checkout →
</button>

<button
  onClick={() => window.clearCart?.()}
  className="w-full mt-3 py-2 text-gray-400 hover:text-white transition text-sm"
>
  Clear Cart
</button>

<button
  onClick={() => window.showPage?.('shop')}
  className="btn"
>
  Continue Shopping
</button>









================================================================================
SHOP PAGE EXTRACTION COMPATIBILITY RULES
================================================================================
These rules ensure the automated extractor can reliably parse and inject output:

ALWAYS define products with this exact regex-matchable pattern:
  const\s+\w*[Pp]roducts?\w*\s*=\s*\[

ALWAYS use string field names: id, name, price.
ALWAYS use double quotes for string values.
NEVER spread array across multiple variable assignments.
NEVER conditionally render the product grid.
NEVER compute price fields with expressions.

EXTRACTION RULES (applied automatically after generation):
  NEVER leave .map() calls in extracted HTML — all arrays must be fully expanded
  NEVER leave onClick, onChange, or any on[A-Z] handler in extracted HTML
  NEVER leave unresolved {expression} blocks in extracted HTML
  NEVER leave data-*={expression} JSX syntax — always resolve to data-*="value"
  NEVER output fewer cards than objects in source array — count must match exactly
  ALWAYS ensure every Add to Cart button has class="add-to-cart-btn"
  ALWAYS resolve data-* attributes before running JSX stripping step
  ALWAYS snapshot loop variables: def fn(m, item=item) not def fn(m)
  ALWAYS verify card count in output matches object count in source

================================================================================
REQUIRED CORE FILES
================================================================================
app/layout.tsx          — Root layout with Navigation and Footer (relative imports)
app/page.tsx            — Home page ('use client' required, has onError + onClick)
app/globals.css         — Complete styles (see template below)
app/shop/page.tsx       — Shop with top-level products array
app/cart/page.tsx       — Full cart page with all required ids (MANDATORY)
components/Navigation.tsx
components/Footer.tsx
contexts/CartContext.tsx
lib/utils.ts
package.json
postcss.config.mjs      — MUST be .mjs not .js
tailwind.config.ts
tsconfig.json           — NO @/* path aliases

================================================================================
JSON OUTPUT FORMAT — CRITICAL
================================================================================
- Output ONLY raw valid JSON. No markdown, no explanations, no code blocks.
- Keys = file paths (strings). Values = full file content as strings.
- Escape double quotes as \\" and newlines as \\n.
- NEVER use raw newlines or unescaped quotes inside JSON string values.
- NEVER use backticks or template literals ${} inside JSON strings.
- NEVER use trailing commas in objects or arrays.

WRONG: {"content": "<p>{`\"${testimonial.quote}\"`}</p>"}
RIGHT: {"content": "<p>{testimonial.quote}</p>"}

================================================================================
COMPLETE CONFIGURATION FILES
================================================================================

postcss.config.mjs:
export default { plugins: { tailwindcss: {}, autoprefixer: {} } }

tailwind.config.ts:
import type { Config } from 'tailwindcss';
const config: Config = {
  darkMode: 'class',
  content: ['./pages/**/*.{js,ts,jsx,tsx,mdx}','./components/**/*.{js,ts,jsx,tsx,mdx}','./app/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: { extend: { animation: { gradient:'gradient 3s ease infinite', shimmer:'shimmer 3s ease infinite', float:'float 6s ease-in-out infinite', 'pulse-slow':'pulse-slow 3s ease-in-out infinite' }, keyframes: { gradient:{'0%,100%':{backgroundPosition:'0% 50%'},'50%':{backgroundPosition:'100% 50%'}}, shimmer:{'0%':{backgroundPosition:'0% 50%'},'50%':{backgroundPosition:'100% 50%'},'100%':{backgroundPosition:'0% 50%'}}, float:{'0%,100%':{transform:'translateY(0px)'},'50%':{transform:'translateY(-20px)'}}, 'pulse-slow':{'0%,100%':{opacity:'0.5'},'50%':{opacity:'1'}} } } },
  plugins: [],
};
export default config;

tsconfig.json:
{ "compilerOptions": { "lib":["dom","dom.iterable","esnext"], "allowJs":true, "skipLibCheck":true, "strict":true, "noEmit":true, "module":"esnext", "moduleResolution":"bundler", "resolveJsonModule":true, "isolatedModules":true, "jsx":"preserve", "incremental":true, "plugins":[{"name":"next"}], "esModuleInterop":true }, "include":["next-env.d.ts",".next/types/**/*.ts","**/*.ts","**/*.tsx"], "exclude":["node_modules"] }

package.json:
{ "name":"project-app", "version":"0.1.0", "private":true, "scripts":{"dev":"next dev","build":"next build","start":"next start"}, "dependencies":{"next":"14.2.35","react":"^18.3.1","react-dom":"^18.3.1","lucide-react":"^0.446.0","clsx":"^2.1.1","tailwind-merge":"^2.5.0"}, "devDependencies":{"@types/node":"^22.9.0","@types/react":"^18.3.12","@types/react-dom":"^18.3.1","autoprefixer":"^10.4.20","postcss":"^8.4.49","tailwindcss":"^3.4.15","typescript":"^5.6.3"} }

lib/utils.ts:
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }

================================================================================
COMPLETE GLOBALS.CSS (MUST INCLUDE ALL — NEVER SIMPLIFY)
================================================================================
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body { @apply bg-zinc-950 text-white antialiased; }
  * { border-color: hsl(var(--border)); }
}

@layer utilities {
  html { scroll-behavior: smooth; }
  ::-webkit-scrollbar { width: 10px; height: 10px; }
  ::-webkit-scrollbar-track { background: #18181b; border-radius: 5px; }
  ::-webkit-scrollbar-thumb { background: linear-gradient(to bottom, #a855f7, #ec4899); border-radius: 5px; }
  ::-webkit-scrollbar-thumb:hover { background: linear-gradient(to bottom, #c084fc, #f472b6); }
  ::selection { @apply bg-purple-500 text-white; }
  *:focus-visible { @apply outline-none ring-2 ring-purple-500 ring-offset-2 ring-offset-zinc-950; }
}

@layer components {
  .glass { @apply bg-white/5 backdrop-blur-md border border-white/10; }
  .glass-hover { @apply transition-all duration-300 hover:bg-white/10 hover:border-white/20; }
  .gradient-text { @apply bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent; background-size: 200% auto; animation: shimmer 3s ease infinite; }
  .card-hover { @apply transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl hover:shadow-purple-500/20; }
  .glow { @apply shadow-lg shadow-purple-500/25; }
  .glow-hover { @apply transition-all duration-300 hover:shadow-xl hover:shadow-purple-500/40; }
  .hero-gradient { background: radial-gradient(ellipse at top, #1e1b4b, transparent), radial-gradient(ellipse at bottom, #4c1d95, transparent); }
  .grid-pattern { background-image: linear-gradient(to right, #ffffff0a 1px, transparent 1px), linear-gradient(to bottom, #ffffff0a 1px, transparent 1px); background-size: 50px 50px; }
  .btn { @apply px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-semibold text-white hover:opacity-90 transition duration-300; }
}

@keyframes shimmer { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
@keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-20px); } }
@keyframes pulse-slow { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }
@keyframes gradient { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
.animate-float { animation: float 6s ease-in-out infinite; }
.animate-pulse-slow { animation: pulse-slow 3s ease-in-out infinite; }
.animate-gradient { background-size: 200% auto; animation: gradient 3s ease infinite; }

================================================================================
FINAL VALIDATION CHECKLIST — VERIFY BEFORE OUTPUT
================================================================================
  ✅ products array defined OUTSIDE component function
  ✅ products use string ids and double-quoted values
  ✅ every Add to Cart button has class="add-to-cart-btn"
  ✅ every button has data-id, data-name, data-price
  ✅ map variable is p, key={p.id} on outer div
  ✅ addToCart(p) passes full object
  ✅ no useState/useEffect/async in shop page
  ✅ cart page file exists at app/cart/page.tsx
  ✅ cart page has all 6 required element ids
  ✅ cart page has Proceed to Checkout button with onclick="openCheckoutModal()"
  ✅ cart page has NO .map() — JS renders items dynamically
  ✅ cart page has NO checkout form — checkout is a modal
  ✅ every navigation link has a corresponding page file
  ✅ every page has 3+ sections with real unique content
  ✅ no placeholder pages ("Coming Soon", empty divs)
  ✅ hero uses image_1.jpg — no other pages use images
  ✅ all imports are relative — no @/ aliases
  ✅ 'use client' on every file with hooks or event handlers
  ✅ onError uses optional chaining: parentElement?.classList
  ✅ postcss.config.mjs uses .mjs extension
  ✅ globals.css includes all utility classes and animations
  ✅ output is raw valid JSON only — no markdown, no backticks




================================================================================
🚨 IMPORT PATH CASE SENSITIVITY — VERCEL BUILD KILLER 🚨
================================================================================

Linux (Vercel) is case-sensitive. macOS is not.
This means it works locally but FAILS on Vercel.

RULE: The import path MUST exactly match the filename case — character for character.

WRONG (builds locally, fails on Vercel):
import { Button } from '../../components/ui/button'   ← lowercase b
import Navigation from '../components/navigation'      ← lowercase n
import Footer from '../components/footer'              ← lowercase f
import { Card } from '../../components/ui/card'       ← lowercase c

RIGHT (matches actual filename case):
import { Button } from '../../components/ui/Button'   ← capital B matches Button.tsx
import Navigation from '../components/Navigation'      ← capital N matches Navigation.tsx
import Footer from '../components/Footer'              ← capital F matches Footer.tsx
import { Card } from '../../components/ui/Card'       ← capital C matches Card.tsx

RULE: Component files ALWAYS start with uppercase (Button.tsx, Navigation.tsx).
RULE: Import paths MUST match that exact casing.
RULE: lib/ and hooks/ and utils/ files are lowercase (utils.ts, useScroll.ts).

CHECKLIST — before outputting any file verify:
✅ Every import path case matches the actual filename case exactly
✅ Component imports are PascalCase: Navigation, Footer, Button, Card
✅ Utility imports are camelCase: utils, useScroll, useMediaQuery
✅ No import uses lowercase for a PascalCase filename
✅ No import uses uppercase for a camelCase filename



# Normalize common case mismatches before injection
IMPORT_CASE_FIXES = {
    "components/ui/button":     "components/ui/Button",
    "components/ui/card":       "components/ui/Card",
    "components/ui/input":      "components/ui/Input",
    "components/ui/modal":      "components/ui/Modal",
    "components/navigation":    "components/Navigation",
    "components/footer":        "components/Footer",
    "components/hero":          "components/Hero",
    "contexts/cartcontext":     "contexts/CartContext",
    "contexts/authcontext":     "contexts/AuthContext",
}

def fix_import_cases(content: str) -> str:
    for wrong, right in IMPORT_CASE_FIXES.items():
        content = content.replace(f"'{wrong}'", f"'{right}'")
        content = content.replace(f'"{wrong}"', f'"{right}"')
    return content







================================================================================
🚨 CART PAGE — MUST BE A VALID REACT COMPONENT, NOT A BARE RETURN 🚨
================================================================================

NEVER generate app/cart/page.tsx as a bare return statement like this:

❌ WRONG — missing function wrapper, causes syntax error:
const updateCartPage = () => { console.log('updateCartPage called'); };
const openCheckoutModal = () => { alert('Checkout modal would open here!'); };
const clearCart = () => { alert('Cart cleared!'); };
const cartItems = [];
const isCartEmpty = cartItems.length === 0;

return (
  <div id="page_cart" className="page">
    ...
  </div>
);

THIS FAILS BECAUSE:
- return() outside a function is a syntax error
- Mock functions with console.log/alert are placeholders not real implementations
- const cartItems = [] hardcoded means cart is always empty
- const isCartEmpty = cartItems.length === 0 outside component never updates
- The cart JavaScript system cannot interact with these React variables
- Webpack cannot compile a file with no default export

ALWAYS generate app/cart/page.tsx as a proper React component:

✅ CORRECT — valid component with proper export:
'use client';

import { ShoppingBag } from 'lucide-react';

export default function CartPage() {
  return (
    <div id="page_cart" className="page">
      <div className="min-h-screen pt-24 container mx-auto px-4">
        <h1 className="text-3xl font-bold mb-8 gradient-text">
          Shopping Cart (<span id="cart-total-count">0</span> items)
        </h1>
        <div className="lg:grid lg:grid-cols-3 lg:gap-8">
          <div className="lg:col-span-2">
            <div id="cart-items-list" class="space-y-4">
              <!-- JS injects items here -->
            </div>
            <div id="empty-cart-message-cart" className="text-center py-12">
              <ShoppingBag className="w-20 h-20 text-gray-600 mx-auto mb-6" />
              <h2 className="text-2xl font-bold mb-4">Your Cart is Empty</h2>
              <button onClick={() => window.showPage?.('shop')} className="btn">
                Continue Shopping
              </button>
            </div>
          </div>
          <div className="lg:col-span-1 mt-8 lg:mt-0">
            <div id="cart-summary" className="glass rounded-xl p-6 h-fit hidden">
              <h3 className="text-xl font-bold mb-4 gradient-text">Order Summary</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400">Subtotal</span>
                  <span id="cart-page-subtotal" className="font-semibold">$0.00</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Shipping</span>
                  <span className="text-green-400">Free</span>
                </div>
              </div>
              <div className="border-t border-white/10 my-4"></div>
              <div className="flex justify-between font-bold text-lg mb-6">
                <span>Total</span>
                <span id="cart-page-total" className="text-purple-400">$0.00</span>
              </div>
              <button
                onClick={() => window.openCheckoutModal?.()}
                className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-semibold text-white hover:opacity-90 transition duration-300"
              >
                Proceed to Checkout →
              </button>
              <button
                onClick={() => window.clearCart?.()}
                className="w-full mt-3 py-2 text-gray-400 hover:text-white transition text-sm"
              >
                Clear Cart
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

CRITICAL RULES FOR CART PAGE COMPONENT:
✅ MUST have export default function CartPage() wrapper
✅ MUST have return() INSIDE the function
✅ MUST NOT define mock functions outside the component
✅ MUST NOT hardcode cartItems = [] — JS system manages cart state
✅ MUST NOT use isCartEmpty logic in JSX — JS system toggles visibility
✅ MUST NOT use useState for cart items — cart is managed by external JS
✅ MUST use window.openCheckoutModal?.() not onclick="openCheckoutModal()"
✅ MUST use window.clearCart?.() not onclick="clearCart()"
✅ MUST use window.showPage?.('shop') not onclick="showPage('shop')"
✅ All required ids must be present with static initial values
✅ cart-summary starts with hidden class — JS removes it when items exist
✅ cart-items-list starts empty — JS injects rows dynamically
✅ cart-total-count starts at 0 — JS updates it
✅ cart-page-subtotal starts at $0.00 — JS updates it
✅ cart-page-total starts at $0.00 — JS updates it


================================================================================
⚠️ RESPONSE FORMATTING RULES ⚠️
================================================================================

To ensure complete JSON parsing:

1. NEVER generate comments inside JSON strings
2. NEVER use backslashes that could escape quotes incorrectly
3. ALWAYS close every string with a double quote "
4. ALWAYS add a comma between object properties
5. ALWAYS close every object with } and every array with ]
6. ALWAYS use double quotes for ALL property names and string values
7. ALWAYS escape double quotes inside strings as \"
8. ALWAYS escape backslashes as \\

BEFORE OUTPUTTING, VERIFY:
✅ Every opening { has a closing }
✅ Every opening [ has a closing ]
✅ Every opening " has a closing "
✅ No trailing commas after last property
✅ JSON is valid (can be parsed by Python's json.loads)
================================================================================
Now generate the complete project for this request: [USER_PROMPT_HERE]