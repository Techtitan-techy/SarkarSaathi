"""
Test script to verify scraper functionality
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_scraper():
    """Test basic scraper"""
    print("=" * 70)
    print("TESTING BASIC SCRAPER")
    print("=" * 70)
    print()
    
    try:
        from scrape_schemes import update_scheme_database
        
        print("Running basic scraper...")
        data = update_scheme_database()
        
        print("\n✓ Basic scraper test passed!")
        print(f"  Total schemes: {data['metadata']['totalSchemes']}")
        
        return True
        
    except Exception as e:
        print(f"\n× Basic scraper test failed: {str(e)}")
        return False


def test_imports():
    """Test if required packages are installed"""
    print("=" * 70)
    print("TESTING DEPENDENCIES")
    print("=" * 70)
    print()
    
    packages = {
        'requests': 'Web requests',
        'bs4': 'HTML parsing (BeautifulSoup)',
        'lxml': 'XML/HTML parser',
    }
    
    all_installed = True
    
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"✓ {package:15} - {description}")
        except ImportError:
            print(f"× {package:15} - NOT INSTALLED")
            all_installed = False
    
    print()
    
    # Test optional packages
    print("Optional packages:")
    optional = {
        'selenium': 'Browser automation',
        'pandas': 'Data processing',
    }
    
    for package, description in optional.items():
        try:
            __import__(package)
            print(f"✓ {package:15} - {description}")
        except ImportError:
            print(f"○ {package:15} - Not installed (optional)")
    
    print()
    
    if not all_installed:
        print("Install missing packages:")
        print("  pip install requests beautifulsoup4 lxml")
        print()
    
    return all_installed


def test_data_directory():
    """Test if data directory exists"""
    print("=" * 70)
    print("TESTING DATA DIRECTORY")
    print("=" * 70)
    print()
    
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    if os.path.exists(data_dir):
        print(f"✓ Data directory exists: {data_dir}")
        
        # Check for database file
        db_file = os.path.join(data_dir, 'schemes_database.json')
        if os.path.exists(db_file):
            print(f"✓ Database file exists: {db_file}")
            
            # Check file size
            size = os.path.getsize(db_file)
            print(f"  File size: {size:,} bytes")
        else:
            print(f"○ Database file not found (will be created)")
    else:
        print(f"○ Data directory not found (will be created)")
        os.makedirs(data_dir, exist_ok=True)
        print(f"✓ Created data directory")
    
    print()
    return True


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "SCRAPER TEST SUITE" + " " * 30 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    tests = [
        ("Dependencies", test_imports),
        ("Data Directory", test_data_directory),
        ("Basic Scraper", test_basic_scraper),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n× {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
        
        print()
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "× FAIL"
        print(f"{status:8} - {test_name}")
    
    print()
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Scraper is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
    
    print()


if __name__ == '__main__':
    main()
