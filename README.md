# Paper-Research-Assistant
my skills  
paper-research-assistant/  
├─ SKILL.md  
├─ agents/  
│  └─ openai.yaml  
├─ scripts/  
│  ├─ build_index.py  
│  └─ search_library.py  
├─ references/  
│  ├─ citation-policy.md  
│  ├─ reading-protocol.md  
│  └─ polishing-rules.md  
├─ assets/  
│  └─ reading-note-template.md  
└─ data/  
└─ library.sqlite3    
需运行
python scripts/build_index.py \
  --library "自己的论文库路径" \
  --index data/library.sqlite3
