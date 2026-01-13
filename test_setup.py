"""Test script to verify the application setup"""

import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    try:
        print("Testing imports...")

        from app.models import Account, Dossier, ProcessingJob
        print("✓ Models imported successfully")

        from app.services.csv_parser import CSVParser
        print("✓ CSV Parser imported successfully")

        from app.services.disqualifier import Disqualifier
        print("✓ Disqualifier imported successfully")

        from app.services.scorer import PriorityScorer
        print("✓ Scorer imported successfully")

        from app.services.enricher import EnrichmentService
        print("✓ Enricher imported successfully")

        from app.services.dossier import DossierGenerator
        print("✓ Dossier Generator imported successfully")

        from app import create_app
        print("✓ Flask app imported successfully")

        from config import Config
        print("✓ Config imported successfully")

        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_directories():
    """Test that required directories exist"""
    print("\nTesting directories...")

    required_dirs = [
        'data/uploads',
        'data/outputs',
        'app/templates',
        'app/static',
        'app/services',
    ]

    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ {dir_path} exists")
        else:
            print(f"✗ {dir_path} missing")
            all_exist = False

    return all_exist

def test_config():
    """Test configuration"""
    print("\nTesting configuration...")

    try:
        from config import Config

        assert hasattr(Config, 'WEIGHTS'), "WEIGHTS not in config"
        print("✓ Scoring weights configured")

        assert hasattr(Config, 'INDUSTRY_PROPENSITY'), "INDUSTRY_PROPENSITY not in config"
        print("✓ Industry propensity configured")

        assert hasattr(Config, 'UPLOAD_FOLDER'), "UPLOAD_FOLDER not in config"
        print("✓ Upload folder configured")

        return True
    except Exception as e:
        print(f"✗ Config error: {e}")
        return False

def test_sample_csv():
    """Test parsing the sample CSV"""
    print("\nTesting sample CSV parsing...")

    try:
        from app.services.csv_parser import CSVParser

        sample_path = Path('sample_data.csv')
        if not sample_path.exists():
            print("✗ sample_data.csv not found")
            return False

        parser = CSVParser()
        is_valid, errors = parser.validate_csv(sample_path)

        if is_valid:
            print("✓ Sample CSV is valid")

            accounts = parser.parse_csv(sample_path)
            print(f"✓ Parsed {len(accounts)} accounts from sample CSV")

            return True
        else:
            print(f"✗ Sample CSV validation failed: {errors}")
            return False

    except Exception as e:
        print(f"✗ Error parsing sample CSV: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Account Prioritization Tool - Setup Test")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Directories", test_directories),
        ("Configuration", test_config),
        ("Sample CSV", test_sample_csv),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")

    all_passed = all(result for _, result in results)

    print("=" * 60)
    if all_passed:
        print("✓ All tests passed! The application is ready to run.")
        print("\nTo start the application, run:")
        print("  python run.py")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == '__main__':
    main()