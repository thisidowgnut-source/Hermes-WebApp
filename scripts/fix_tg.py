import re

def main():
    path = "static/index.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Fix raw tg.BackButton and tg.MainButton in openModule
    content = re.sub(
        r'(\s+)tg\.BackButton\.show\(\);\s*tg\.BackButton\.onClick\(closeAllModules\);',
        r'\1try { tg.BackButton.show(); tg.BackButton.onClick(closeAllModules); } catch(e) {}',
        content
    )

    content = re.sub(
        r'(\s+)tg\.MainButton\.setText\("⚡ CLEANUP ZOMBIES"\);\s*tg\.MainButton\.setParams\(\{ color: \'#ff3333\', text_color: \'#ffffff\' \}\);\s*tg\.MainButton\.show\(\);\s*tg\.MainButton\.onClick\(\(\) => triggerMacro\(\'cleanup_zombies\'\)\);',
        r'\1try { tg.MainButton.setText("⚡ CLEANUP ZOMBIES"); tg.MainButton.setParams({ color: "#ff3333", text_color: "#ffffff" }); tg.MainButton.show(); tg.MainButton.onClick(() => triggerMacro("cleanup_zombies")); } catch(e) {}',
        content
    )

    content = re.sub(
        r'(\s+)tg\.MainButton\.hide\(\);',
        r'\1try { tg.MainButton.hide(); } catch(e) {}',
        content
    )

    # 2. Fix raw tg.showAlert
    content = re.sub(
        r'tg\.showAlert\((.*?)\);',
        r'try { tg.showAlert(\1); } catch(e) { alert(\1); }',
        content
    )
    
    # Also fix the already wrapped ones to have alert fallback
    content = re.sub(
        r'try \{ tg\.showAlert\((.*?)\); \} catch\(e\) \{\}',
        r'try { tg.showAlert(\1); } catch(e) { alert(\1); }',
        content
    )
    
    # 3. Clean up double try/catch
    content = re.sub(
        r'try \{ try \{ tg\.showAlert\((.*?)\); \} catch\(e\) \{ alert\((.*?)\); \} \} catch\(e\) \{\}',
        r'try { tg.showAlert(\1); } catch(e) { alert(\2); }',
        content
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("Fixed tg API calls in static/index.html")

if __name__ == "__main__":
    main()
