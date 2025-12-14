import sys
import pkg_resources
import platform
import subprocess

def check_requirements():
    print(f"🔍 System Info:")
    print(f"   - Python: {sys.version.split()[0]} ({platform.architecture()[0]})")
    print(f"   - OS: {platform.system()} {platform.release()}")
    print("-" * 60)
    
    # Read requirements.txt
    try:
        with open('requirements.txt', 'r') as f:
            requirements = [
                line.strip() 
                for line in f 
                if line.strip() and not line.startswith('#')
            ]
    except FileNotFoundError:
        print("❌ Error: requirements.txt not found!")
        return

    print(f"📦 Checking {len(requirements)} packages from requirements.txt...\n")
    
    all_good = True
    
    for req_str in requirements:
        try:
            # Parse requirement (e.g., 'pandas==2.2.1' -> name='pandas', spec='==2.2.1')
            req = pkg_resources.Requirement.parse(req_str)
            package_name = req.key
            
            try:
                # Get installed version
                installed_dist = pkg_resources.get_distribution(package_name)
                installed_ver = installed_dist.version
                
                # Check if version matches matcher
                if installed_dist in req:
                    print(f" ✅ {package_name:<30} {installed_ver:<10} (Match)")
                else:
                    print(f" ⚠️ {package_name:<30} {installed_ver:<10} (Mismatch! Expected: {req})")
                    all_good = False
                    
            except pkg_resources.DistributionNotFound:
                print(f" ❌ {package_name:<30} NOT FOUND  (Expected: {req})")
                all_good = False
                
        except Exception as e:
            print(f" ⚠️ Could not parse: {req_str} ({str(e)})")
            all_good = False

    print("-" * 60)
    if all_good:
        print("🎉 GREAT! All dependencies are installed correctly.")
        print("   You can run the app with: streamlit run app/streamlit_app.py")
    else:
        print("🚫 ISSUES FOUND.")
        print("   Please install missing/incorrect packages:")
        print("   pip install -r requirements.txt")

if __name__ == "__main__":
    check_requirements()
