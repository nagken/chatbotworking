#!/usr/bin/env python3
"""
Debug the clear chat popup issue
"""

print("🔍 Debug Clear Chat Popup Issue")
print("=" * 40)

print("The issue might be:")
print("1. JavaScript error in try/catch block")
print("2. Response not being JSON parsed correctly")
print("3. UI method calls failing")
print("")
print("To debug in browser:")
print("1. Open Developer Tools (F12)")
print("2. Go to Console tab")
print("3. Click 'Clear All Chats' button")
print("4. Watch for any red error messages")
print("")
print("Expected console output:")
print("   🔑 Session token retrieved successfully")
print("   🗑️ Sending request to clear all conversations...")
print("   ✅ Clear all conversations response: {success: true, ...}")
print("   ✅ All conversations cleared successfully")
print("")
print("If you see errors, they will help identify the issue!")
print("")
print("Quick test - run this in browser console:")
print("   window.conversationManager.getSessionToken()")
print("   // Should return a token, not null")