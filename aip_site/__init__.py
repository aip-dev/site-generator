import sys
import os

vendor_dir = os.path.join(os.path.dirname(__file__), 'vendor')

for item in os.listdir(vendor_dir):
    path = os.path.join(vendor_dir, item)
    if not os.path.isdir(path):
        continue
    if path not in sys.path:
        sys.path.insert(0, path)
