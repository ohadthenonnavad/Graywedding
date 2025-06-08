import uefitool
import sys

# Path to your firmware binary
firmware_path = "FWDB/dell5310.bin"  # Replace with your actual path

# Create the parser instance
parser = uefitool.FitParser()

# Load the firmware file
if not parser.load_file(firmware_path):
    print(f"❌ Failed to load firmware file: {firmware_path}")
    sys.exit(1)
    
# Parse the FIT table
fit_result = parser.parse_fit()
# Print results
print("✅ FIT Parse Result:\n")
print(fit_result)

# Optional: print additional security info
print("\nSecurity Info:\n")
info = parser.get_security_info()
print(info)