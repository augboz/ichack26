"""
Download SSD MobileNet V2 model files for object detection
"""
import urllib.request
import os

# Model file URLs
CONFIG_URL = "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/ssd_mobilenet_v2_coco_2018_03_29.pbtxt"
WEIGHTS_URL = "http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz"

# File paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "ssd_mobilenet_v2_coco_2018_03_29.pbtxt")
WEIGHTS_ARCHIVE = os.path.join(SCRIPT_DIR, "ssd_mobilenet_v2_coco_2018_03_29.tar.gz")
WEIGHTS_PATH = os.path.join(SCRIPT_DIR, "ssd_mobilenet_v2_coco_2018_03_29", "frozen_inference_graph.pb")
WEIGHTS_DEST = os.path.join(SCRIPT_DIR, "ssd_mobilenet_v2_coco_2018_03_29.pb")


def download_file(url, destination):
    """Download a file with progress indication"""
    print(f"Downloading {os.path.basename(destination)}...")

    def progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(downloaded * 100 / total_size, 100)
        print(f"\r  Progress: {percent:.1f}%", end='', flush=True)

    urllib.request.urlretrieve(url, destination, progress)
    print()  # New line after progress


def main():
    print("=" * 60)
    print("SSD MobileNet V2 Model Downloader")
    print("=" * 60)

    # 1. Download config file
    if os.path.exists(CONFIG_PATH):
        print(f"✓ Config file already exists: {CONFIG_PATH}")
    else:
        download_file(CONFIG_URL, CONFIG_PATH)
        print(f"✓ Downloaded config file to: {CONFIG_PATH}")

    # 2. Download and extract weights
    if os.path.exists(WEIGHTS_DEST):
        print(f"✓ Weights file already exists: {WEIGHTS_DEST}")
    else:
        # Download archive
        download_file(WEIGHTS_URL, WEIGHTS_ARCHIVE)
        print(f"✓ Downloaded weights archive")

        # Extract archive
        print("Extracting weights...")
        import tarfile
        with tarfile.open(WEIGHTS_ARCHIVE, 'r:gz') as tar:
            tar.extractall(SCRIPT_DIR)
        print("✓ Extracted weights")

        # Move frozen_inference_graph.pb to the correct name
        if os.path.exists(WEIGHTS_PATH):
            os.rename(WEIGHTS_PATH, WEIGHTS_DEST)
            print(f"✓ Renamed weights to: {WEIGHTS_DEST}")

        # Clean up
        os.remove(WEIGHTS_ARCHIVE)
        print("✓ Cleaned up archive file")

    print("\n" + "=" * 60)
    print("✓ Model files ready!")
    print("=" * 60)
    print(f"\nConfig:  {CONFIG_PATH}")
    print(f"Weights: {WEIGHTS_DEST}")
    print("\nYou can now run: python backend.py")


if __name__ == "__main__":
    main()
