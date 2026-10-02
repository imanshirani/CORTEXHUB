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
                        
                        # Identify functions for adding documents
                        if 'def ' in line and ':' in line:
                            # Checking that the next line is not a document itself
                            if i + 1 < len(lines) and '"""' not in lines[i+1]:
                                indent = line[:line.find('def')]
                                func_name = line.split('def ')[1].split('(')[0]
                                
                                # Create a simple description based on the function name
                                clean_name = func_name.replace('_', ' ').title()
                                doc = f'{indent}    """\n{indent}    Handle {clean_name} operation.\n{indent}    """\n'
                                
                                new_lines.append(doc)
                                modified = True

                    if modified:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.writelines(new_lines)
                        print(f"✅ Documented: {folder}/{file}")

if __name__ == "__main__":
    # We only scan folders that contain Python code
    folders_to_scan = ["app", "plugins"]
    print("🚀 Starting Cortex Auto-Doc...")
    add_smart_docs(folders_to_scan)
    print("\n✨ All done! Your files are now documented.")