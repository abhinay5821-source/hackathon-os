# Fresh-clone reproduction report

Run date: 2026-10-08 UTC  
Tested published head: `b2e0afb339da2e9ffe8decacdffb43fabb148033`  
Environment: Linux 6.18.44 x86_64, Python 3.12.14  
Declared core dependency: `numpy==2.3.5`

Procedure:

```bash
git clone --branch repairlab/ctc-foundation --single-branch \
  https://github.com/abhinay5821-source/hackathon-os.git repairlab-fresh
python -m venv repairlab-venv
repairlab-venv/bin/pip install -r repairlab-fresh/repairlab-requirements.txt
cd repairlab-fresh
../repairlab-venv/bin/python -m unittest discover -s tests -v
```

Result: **60 tests run; 60 passed; 0 failures; 0 errors** in 2.856 seconds after dependency installation.

This result covers the lightweight core requirements and automated suite. It does not reproduce optional acoustic-model downloads, approved reference data, human annotations, browser usability, real detector accuracy or a public deployment. Those remain separate gates.
