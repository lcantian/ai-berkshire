#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'D:\AI\ai-berkshire'
os.chdir(BASE)
sys.path.insert(0, os.path.join(BASE, 'tools'))
import report_audit
with open(os.path.join(BASE, '.tmp_research', 'audit_hik_results.json'), encoding='utf-8') as f:
    results = json.load(f)
report_audit.render_verdict(results, '海康威视-research-20260725.md')
