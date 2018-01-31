import os

print(os.getcwd())
os.system("py core/pupil_lib.py --datasets C:\\Users\\Gregory\\Documents\\Honors_Thesis\\2017_03_07\\002 "
          "C:\\Users\\Gregory\\Documents\\Honors_Thesis\\2017_03_07\\002 --triggers S11 S12 S13 "
          "--trial-range -1 2 --baseline 1 --store artifacts/2017_06_24/ --logger stdout --max-workers 17")