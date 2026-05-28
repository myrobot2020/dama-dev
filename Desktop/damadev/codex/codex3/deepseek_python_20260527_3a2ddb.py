# Fix common transcription errors
text = re.sub(r'(?i)\bvagina\b', 'jhana', text)
text = re.sub(r'(?i)\bvangina\b', 'jhana', text)
text = re.sub(r'(?i)\bjanus\b', 'jhanas', text)
text = re.sub(r'(?i)\bjana\b', 'jhana', text)
text = re.sub(r'(?i)\bgenres\b', 'jhanas', text)
text = re.sub(r'(?i)\bganas\b', 'jhanas', text)