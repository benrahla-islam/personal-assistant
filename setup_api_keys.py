#!/usr/bin/env python3
"""
Setup script to help configure multi-API keys for the personal assistant.
"""

import os
from pathlib import Path

def setup_multi_api_keys():
    """Interactive setup for API keys."""
    print("🔧 Personal Assistant Multi-API Key Setup")
    print("=" * 50)
    
    env_file = Path(".env")
    
    # Read existing .env if it exists
    existing_env = {}
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    existing_env[key] = value
    
    # Check current API key status
    primary_key = existing_env.get("GOOGLE_API_KEY", "")
    secondary_key = existing_env.get("GOOGLE_API_KEY_AGENTS", "")
    
    print(f"\n📋 Current Configuration:")
    print(f"   Primary API Key: {'✅ Set' if primary_key else '❌ Not set'}")
    print(f"   Secondary API Key: {'✅ Set' if secondary_key else '❌ Not set'}")
    
    print(f"\n💡 Multi-API Key Benefits:")
    print(f"   • Double your rate limits (20 req/min instead of 10)")
    print(f"   • Better load distribution")
    print(f"   • More reliable service")
    
    # Setup primary key
    if not primary_key:
        print(f"\n🔑 Primary API Key Setup:")
        print(f"   This is your main Gemini API key.")
        primary_key = input("   Enter your primary Google API key: ").strip()
        if not primary_key:
            print("   ❌ Primary key is required!")
            return False
    
    # Setup secondary key (optional)
    print(f"\n🔑 Secondary API Key Setup (Optional but Recommended):")
    print(f"   This will double your rate limits!")
    
    if secondary_key:
        use_existing = input(f"   Keep existing secondary key? (y/n): ").lower().startswith('y')
        if not use_existing:
            secondary_key = ""
    
    if not secondary_key:
        print(f"   Options:")
        print(f"   1. Enter a different Google API key")
        print(f"   2. Skip (use single API key)")
        
        choice = input("   Choose (1/2): ").strip()
        
        if choice == "1":
            secondary_key = input("   Enter your secondary Google API key: ").strip()
            if secondary_key == primary_key:
                print("   ⚠️  Warning: Secondary key is same as primary - no benefit")
        elif choice == "2":
            print("   ℹ️  Skipping secondary key - you can add it later")
        else:
            print("   ℹ️  Invalid choice - skipping secondary key")
    
    # Write to .env file
    env_content = []
    
    # Preserve non-API key entries
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                if not line.startswith("GOOGLE_API_KEY"):
                    env_content.append(line.rstrip())
    
    # Add API keys
    env_content.append(f"GOOGLE_API_KEY={primary_key}")
    if secondary_key:
        env_content.append(f"GOOGLE_API_KEY_AGENTS={secondary_key}")
    
    # Write to file
    with open(env_file, "w") as f:
        f.write("\\n".join(env_content) + "\\n")
    
    print(f"\n✅ Configuration saved to .env file!")
    print(f"\n🎯 Setup Summary:")
    print(f"   • Primary key: Set ✅")
    if secondary_key:
        print(f"   • Secondary key: Set ✅")
        print(f"   • Load distribution: ENABLED 🚀")
        print(f"   • Rate limits: ~20 req/min (double!)")
    else:
        print(f"   • Secondary key: Not set")
        print(f"   • Load distribution: DISABLED")
        print(f"   • Rate limits: ~10 req/min")
    
    print(f"\\n🚀 Your personal assistant is ready!")
    print(f"   Run: uv run python -m telegram_bot.main")
    
    return True

if __name__ == "__main__":
    try:
        success = setup_multi_api_keys()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n\\n❌ Setup cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\\n❌ Setup failed: {e}")
        exit(1)
