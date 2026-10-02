import os

def add_smart_docs(root_dirs):
    """
    Traverses the Cortex Pipeline structure and adds docstrings.
    """
    for folder in root_dirs:
        if not os.path.exists(folder):
            print(f"?? Folder '{folder}' not found, skipping...")
            continue

        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    path = os.path.join(root, file)
                    
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    new_lines = []
                    modified = False

                    for i, line in enumerate(lines):
                        new_lines.append(line)
                        
                        # شناسایی توابع برای اضافه کردن داکیومنت
                        if 'def ' in line and ':' in line:
                            # چک کردن اینکه خط بعدی خودش داکیومنت نباشد
                            if i + 1 < len(lines) and '"""' not in lines[i+1]:
                                indent = line[:line.find('def')]
                                func_name = line.split('def ')[1].split('(')[0]
                                
                                # ساخت یک توضیح ساده بر اساس اسم تابع
                                clean_name = func_name.replace('_', ' ').title()
                                doc = f'{indent}    """\n{indent}    Handle {clean_name} operation.\n{indent}    """\n'
                                
                                new_lines.append(doc)
                                modified = True

                    if modified:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.writelines(new_lines)
                        print(f"✅ Documented: {folder}/{file}")

if __name__ == "__main__":
    # فقط پوشه‌هایی که کد پایتون دارند را اسکن می‌کنیم
    folders_to_scan = ["app", "plugins"]
    print("🚀 Starting Cortex Auto-Doc...")
    add_smart_docs(folders_to_scan)
    print("\n✨ All done! Your files are now documented.")