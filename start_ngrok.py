#!/usr/bin/env python3
"""Start Vera bot with ngrok tunnel."""
import ngrok
import time
import os

AUTHTOKEN = "3DB5f5mYwzZXmOLsB5K2uPDGjTg_3Up2XJ2mykTb9MWrQMhzo"

listener = ngrok.forward(8080, authtoken=AUTHTOKEN)

print(f"\n{'='*60}")
print(f"Vera Bot is live at: {listener.url()}")
print(f"{'='*60}\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down...")
    ngrok.kill()
