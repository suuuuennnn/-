"""
验证修复的测试脚本
"""

print("=" * 60)
print("Verify fixes")
print("=" * 60)

# 测试1: 验证txt文件导入功能
print("\n[Test 1] Verify txt file import")
print("-" * 60)

try:
    from word_manager import WordManager
    from database import DatabaseManager
    
    db = DatabaseManager()
    wm = WordManager()
    
    # Clear grade 3 words
    db.execute("DELETE FROM words WHERE grade_level = '三年级上'")
    
    # Import txt file
    print("Importing wordlists/三年级上.txt...")
    count = wm.import_wordlist("wordlists/三年级上.txt", "三年级上")
    
    # Verify import
    grade3_words = db.get_words_by_grade("三年级上")
    print(f"Import successful: {count} words")
    print(f"Database has {len(grade3_words)} grade 3 words")
    
    if grade3_words:
        print(f"Sample word: {grade3_words[0]}")
    
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()

# Test space-separated format
print("\n[Test 1b] Test space-separated format")
print("-" * 60)

try:
    # Create a test file with space-separated format
    test_content = "apple 苹果\nbook 书;书本\ncat 猫\n"
    with open("test_space.txt", "w", encoding="utf-8") as f:
        f.write(test_content)
    
    # Import it
    count = wm.import_custom_wordlist("test_space.txt")
    print(f"Space-separated import: {count} words")
    
    # Verify
    custom_words = db.get_custom_words()
    print(f"Custom words in DB: {len(custom_words)}")
    
    # Clean up
    os.remove("test_space.txt")
    
except Exception as e:
    print(f"Space-separated test failed: {e}")
    import traceback
    traceback.print_exc()

# 测试2: 验证图片加载功能
print("\n[Test 2] Verify image loading")
print("-" * 60)

try:
    from image_utils import ImageUtils
    
    img_utils = ImageUtils()
    img_utils.load_all_images()
    
    mouse_img = img_utils.get_image("mouse")
    hammer_img = img_utils.get_image("hammer")
    injured_img = img_utils.get_image("injured")
    runaway_img = img_utils.get_image("runaway")
    bg_img = img_utils.get_image("background")
    
    if mouse_img:
        print("Mouse image loaded successfully")
    else:
        print("Mouse image loading failed")
    
    if hammer_img:
        print("Hammer image loaded successfully")
    else:
        print("Hammer image loading failed")
    
    if injured_img:
        print("Injured image loaded successfully")
    else:
        print("Injured image loading failed")
    
    if runaway_img:
        print("Runaway image loaded successfully")
    else:
        print("Runaway image loading failed")
        
    if bg_img:
        print("Background image loaded successfully")
    else:
        print("Background image loading failed")
    
except Exception as e:
    print(f"Image loading failed: {e}")
    import traceback
    traceback.print_exc()

# 测试3: 验证游戏界面创建
print("\n[Test 3] Verify game UI creation")
print("-" * 60)

try:
    import tkinter as tk
    from game import GameEngine
    from sound import SoundManager
    
    # Create hidden root window
    root = tk.Tk()
    root.withdraw()
    
    # Initialize managers
    db = DatabaseManager()
    sound = SoundManager()
    images = ImageUtils()
    images.load_all_images()
    
    # Get test words
    test_words = db.get_words_by_grade("三年级上")
    if not test_words:
        print("No grade 3 words, skipping test")
    else:
        print(f"Using {len(test_words)} words for test")
        
        # Create game engine
        print("Creating game engine...")
        game = GameEngine(root, db, sound, images)
        
        # Try to start game
        print("Starting game...")
        result = game.start_game(test_words[:3], "eng2chn", 3)
        
        if result:
            print("Game started successfully")
            print("Game UI created successfully")
            
            # Close after 1 second
            root.after(1000, root.destroy)
            root.mainloop()
        else:
            print("Game start failed")
    
except Exception as e:
    print(f"Game UI creation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Verification complete")
print("=" * 60)

print("\n[Summary]")
print("1. txt import fixes:")
print("   - Supports comma, tab, and space separators")
print("   - Uses split(None,1) for space separation")
print("   - Shows detailed error messages")
print("")
print("2. Image fixes:")
print("   - Custom mouse image (mouse.png)")
print("   - Custom injured mouse image (injured.png)")
print("   - Custom hammer image (hammer.png)")
print("   - Custom background image (background.png)")
print("   - All images loaded from external files")