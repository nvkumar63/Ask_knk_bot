python3 -c "
content = open('run_telegram.py').read()
old = '        import_text_file(\"mydata.txt\")'
new = '        import_text_file(\"mydata.txt\")\n        from load_restricted import load_restricted\n        load_restricted()'
content = content.replace(old, new)
open('run_telegram.py', 'w').write(content)
print('Done!')
"