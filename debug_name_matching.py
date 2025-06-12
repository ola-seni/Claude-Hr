# debug_name_matching.py
"""Debug the name matching algorithm to see why it's failing"""

from baseball_savant import BaseballSavant

def debug_name_matching():
    """Debug the name matching with detailed output"""
    
    print("🔍 DEBUGGING NAME MATCHING ALGORITHM")
    print("=" * 60)
    
    savant = BaseballSavant()
    
    # Test cases with detailed debugging
    test_cases = [
        ("Aaron Judge", ["Nola, Aaron", "Judge, Aaron", "Bummer, Aaron"]),
        ("Juan Soto", ["Soto, Gregory", "Soto, Juan", "Mejia, Juan"]),
    ]
    
    for search_name, candidates in test_cases:
        print(f"\n🎯 Testing: '{search_name}'")
        print(f"   Candidates: {candidates}")
        
        # Let's trace through the algorithm step by step
        
        # Step 1: Normalize names
        search_normalized = search_name.lower().strip()
        print(f"\n   Step 1 - Normalized search: '{search_normalized}'")
        
        # Step 2: Check exact match
        print("\n   Step 2 - Checking exact matches:")
        for name in candidates:
            if name.lower() == search_normalized:
                print(f"      ✓ Exact match found: '{name}'")
            else:
                print(f"      ✗ '{name.lower()}' != '{search_normalized}'")
        
        # Step 3: Parse search name
        search_parts = search_normalized.split()
        print(f"\n   Step 3 - Search name parts: {search_parts}")
        
        if len(search_parts) >= 2:
            search_first = search_parts[0]
            search_last = search_parts[-1]
            print(f"      First: '{search_first}', Last: '{search_last}'")
            
            # Step 4: Check each candidate
            print("\n   Step 4 - Checking candidates with parsed names:")
            for name in candidates:
                name_parts = name.lower().split()
                print(f"\n      Candidate: '{name}'")
                print(f"      Parts: {name_parts}")
                
                if ',' in name:
                    # Handle "Last, First" format
                    name_clean = name.replace(',', '').strip()
                    name_parts = name_clean.lower().split()
                    if len(name_parts) >= 2:
                        cand_last = name_parts[0]
                        cand_first = name_parts[1]
                        print(f"      Parsed as: First='{cand_first}', Last='{cand_last}'")
                        
                        # Check match
                        first_match = search_first == cand_first
                        last_match = search_last == cand_last
                        print(f"      First match: {first_match} ('{search_first}' == '{cand_first}')")
                        print(f"      Last match: {last_match} ('{search_last}' == '{cand_last}')")
                        
                        if first_match and last_match:
                            print(f"      ✓ MATCH FOUND!")
                        else:
                            print(f"      ✗ No match")
                else:
                    # Handle "First Last" format
                    if len(name_parts) >= 2:
                        cand_first = name_parts[0]
                        cand_last = name_parts[-1]
                        print(f"      Parsed as: First='{cand_first}', Last='{cand_last}'")
                        
                        # Check match
                        first_match = search_first == cand_first
                        last_match = search_last == cand_last
                        print(f"      First match: {first_match}")
                        print(f"      Last match: {last_match}")
        
        # Now run the actual method
        print(f"\n   ACTUAL METHOD RESULT:")
        result = savant._advanced_name_matching(search_name, candidates)
        print(f"   Result: '{result}'")
        
        if result is None:
            print("   ❌ Method returned None - name matching failed!")
        else:
            print(f"   ✅ Method returned: '{result}'")

def test_simple_matching():
    """Test with very simple cases to isolate the issue"""
    
    print("\n\n🧪 TESTING SIMPLE CASES")
    print("=" * 60)
    
    savant = BaseballSavant()
    
    # Very simple test cases
    simple_tests = [
        ("aaron judge", ["judge, aaron"]),  # All lowercase
        ("Aaron Judge", ["Judge, Aaron"]),  # Exact casing
        ("AARON JUDGE", ["JUDGE, AARON"]),  # All uppercase
    ]
    
    for search, candidates in simple_tests:
        result = savant._advanced_name_matching(search, candidates)
        print(f"'{search}' with {candidates} → '{result}'")

def check_method_exists():
    """Verify the method exists and is callable"""
    
    print("\n\n🔧 CHECKING METHOD EXISTS")
    print("=" * 60)
    
    savant = BaseballSavant()
    
    if hasattr(savant, '_advanced_name_matching'):
        print("✅ Method '_advanced_name_matching' exists")
        
        # Check if it's callable
        if callable(getattr(savant, '_advanced_name_matching')):
            print("✅ Method is callable")
            
            # Try calling with minimal args
            try:
                result = savant._advanced_name_matching("Test", ["Test"])
                print(f"✅ Method can be called, returned: '{result}'")
            except Exception as e:
                print(f"❌ Error calling method: {e}")
        else:
            print("❌ Method is not callable")
    else:
        print("❌ Method '_advanced_name_matching' does not exist!")
        
        # List available methods
        print("\nAvailable methods in BaseballSavant:")
        methods = [m for m in dir(savant) if not m.startswith('__')]
        for method in sorted(methods):
            print(f"   • {method}")

def main():
    """Run all debugging tests"""
    
    # Check if method exists
    check_method_exists()
    
    # Debug the matching algorithm
    debug_name_matching()
    
    # Test simple cases
    test_simple_matching()
    
    print("\n" + "=" * 60)
    print("📋 DEBUGGING COMPLETE")

if __name__ == "__main__":
    main()
