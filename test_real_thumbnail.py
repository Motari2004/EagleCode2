import asyncio
from pathlib import Path
from html2image import Html2Image
import os

async def test_real_thumbnail():
    # Read your actual preview HTML file
    preview_file = r"C:\Users\PC\Documents\ai-website-builder\backend\previews\preview_2941a902.html"
    
    if not os.path.exists(preview_file):
        print(f"❌ Preview file not found: {preview_file}")
        return
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"📄 Loaded HTML: {len(html_content)} chars")
    
    # Create directories
    Path("thumbnails").mkdir(exist_ok=True)
    Path("temp_thumbnails").mkdir(exist_ok=True)
    
    # Save HTML to temp file
    temp_html = Path("temp_thumbnails/test_real.html")
    with open(temp_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Test different sizes
    sizes = [(1280, 720), (1280, 1500), (1280, 2000), (1280, 3000)]
    
    for width, height in sizes:
        print(f"\n📸 Testing size: {width}x{height}")
        
        try:
            hti = Html2Image(
                output_path="temp_thumbnails",
                size=(width, height),
                browser='chrome',
            )
            
            output_file = f"test_{width}x{height}.png"
            hti.screenshot(html_file=str(temp_html), save_as=output_file)
            
            # Move to thumbnails folder
            import shutil
            src = Path("temp_thumbnails") / output_file
            dst = Path("thumbnails") / output_file
            
            if src.exists():
                shutil.move(str(src), str(dst))
                print(f"✅ Saved: thumbnails/{output_file}")
                
                # Get file size
                size_kb = dst.stat().st_size / 1024
                print(f"   Size: {size_kb:.1f} KB")
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    # Cleanup
    os.remove(temp_html)
    os.rmdir("temp_thumbnails")
    
    print("\n" + "="*50)
    print("✅ Test complete! Check these files:")
    for width, height in sizes:
        print(f"   http://localhost:8000/thumbnails/test_{width}x{height}.png")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(test_real_thumbnail())