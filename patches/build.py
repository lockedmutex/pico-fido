import os
import shutil
import subprocess
import sys
import multiprocessing

# --- Configuration ---
BUILD_DIR = "build"

PATCHES = [
    {
        "file": "pico-keys-sdk/src/usb/usb_descriptors.c",
        "name": "Manufacturer Name",
        "old": '"Pol Henarejos"',
        "new": '"Suyog Tandel"'
    },
    {
        "file": "pico-keys-sdk/src/main.c",
        "name": "Enable Button Check (Force 60s timeout)",
        "old": "uint32_t button_timeout = 0;",
        "new": "uint32_t button_timeout = 60000;"
    }
]

# --- Build Environment ---
BUILD_ENV = os.environ.copy()
BUILD_ENV.update({
    "PICO_SDK_PATH": "/home/suyog/.pico-sdk/sdk/2.2.0",
    "PICO_TOOLCHAIN_PATH": "/home/suyog/.pico-sdk/toolchain/14_2_Rel1/bin"
})

# --- CMake Command ---
CMAKE_CMD = [
    "cmake", "..",
    "-DPICO_BOARD=pico2",
    "-DVIDPID=Nitro3",       
    "-DENABLE_EDDSA=ON",
    "-DCMAKE_BUILD_TYPE=Release"
]

def patch_source():
    print("\n🔧 Applying Patches...")
    
    for p in PATCHES:
        target_file = p["file"]
        if not os.path.exists(target_file):
            print(f"   ❌ Error: File not found: {target_file}")
            sys.exit(1)

        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        if p["new"] in content:
            print(f"   ✅ {p['name']}: Already patched.")
        elif p["old"] in content:
            new_content = content.replace(p["old"], p["new"])
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"   ✅ {p['name']}: Applied.")
        else:
            print(f"   ⚠️  Warning: Could not patch '{p['name']}'. Original string not found.")

def undo_patches():
    print("\n🧹 Reverting Patches (Cleaning up)...")
    
    for p in PATCHES:
        target_file = p["file"]
        
        if not os.path.exists(target_file):
            continue

        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        if p["new"] in content:
            restored_content = content.replace(p["new"], p["old"])
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(restored_content)
            print(f"   ⏪ {p['name']}: Reverted to original.")
        elif p["old"] in content:
            print(f"   ℹ️  {p['name']}: Already clean.")
        else:
            print(f"   ⚠️  Warning: Could not revert '{p['name']}'. New string not found.")

def run_build():
    print("\n🚀 Starting Build Process...")

    if os.path.exists(BUILD_DIR):
        print(f"   Cleaning {BUILD_DIR}...")
        shutil.rmtree(BUILD_DIR)
    
    os.makedirs(BUILD_DIR)
    
    print(f"   Running CMake configuration...")
    try:
        subprocess.run(
            CMAKE_CMD,
            cwd=BUILD_DIR,
            env=BUILD_ENV,
            check=True
        )
        print("\n✅ Configuration successful.")
        
        cpu_count = multiprocessing.cpu_count()
        print(f"   Compiling with {cpu_count} jobs...")
        
        subprocess.run(
            ["make", f"-j{cpu_count}"], 
            cwd=BUILD_DIR, 
            check=True
        )
        print("\n✅ Build Completed Successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with error code {e.returncode}")
        # We re-raise the error so the finally block catches it but we still exit with error
        sys.exit(e.returncode)

if __name__ == "__main__":
    try:
        patch_source()
        run_build()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user.")
    except SystemExit:
        pass 
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        undo_patches()