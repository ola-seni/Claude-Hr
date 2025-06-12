# clear_cache.py
"""Clear all cached data to force fresh retrieval"""

import os
import shutil
import glob

def clear_all_caches():
    """Clear all cache directories and files"""
    
    print("🧹 CLEARING ALL CACHED DATA")
    print("=" * 40)
    
    # Cache directories to clear
    cache_dirs = [
        'savant_cache',
        'savant_test',
        'backtest_cache',
        '__pycache__'
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ Removed directory: {cache_dir}")
            except Exception as e:
                print(f"❌ Error removing {cache_dir}: {e}")
    
    # Cache file patterns to clear
    cache_patterns = [
        '*.pkl',
        '*.cache',
        '*_cache.json',
        'savant_data_*.json'
    ]
    
    for pattern in cache_patterns:
        files = glob.glob(pattern)
        for file in files:
            try:
                os.remove(file)
                print(f"✅ Removed file: {file}")
            except Exception as e:
                print(f"❌ Error removing {file}: {e}")
    
    print("\n✅ Cache clearing complete!")
    print("📋 Next: Run test_name_matching_fix.py to verify everything works")

if __name__ == "__main__":
    clear_all_caches()
