#!/usr/bin/env python3
"""
Estonian Football Time Machine - Launch Script
Cleaned and refactored project launcher
"""

import tkinter as tk
from estonian_football_time_machine_final import EstonianFootballTimeMachineComplete

def main():
    """Launch the Estonian Football Time Machine application"""
    print("🚀 Launching Estonian Football Time Machine...")
    print("📊 Processing actual 2025 match results for realistic predictions...")
    
    root = tk.Tk()
    app = EstonianFootballTimeMachineComplete(root)
    
    print("✅ Application loaded successfully!")
    print("🎯 Ready for Estonian football predictions with real match data")
    
    root.mainloop()

if __name__ == "__main__":
    main()
