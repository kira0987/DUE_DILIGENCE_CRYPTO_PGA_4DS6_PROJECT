import git
from git import Repo
import os
from tqdm import tqdm
import time

# Folder to save the repo
output_dir = "whitepaper_cryp"
os.makedirs(output_dir, exist_ok=True)

# GitHub repository URL
repo_url = "https://github.com/Cryptorating/whitepapers.git"

# Custom progress class for GitPython
class CloneProgress(git.RemoteProgress):
    def __init__(self):
        super().__init__()
        self.pbar = tqdm(total=100, desc="Cloning Progress", unit="%")
        self.total_size_mb = None  # We'll estimate this
        self.downloaded_mb = 0

    def update(self, op_code, cur_count, max_count=None, message=''):
        # Estimate total size (GitPython doesn't provide this directly, so we approximate)
        if max_count and not self.total_size_mb:
            # Rough estimate: assume 50 MB total (adjust based on repo size if known)
            self.total_size_mb = 50.0  # Update this after checking repo size manually if needed
        
        # Calculate progress percentage
        if max_count:
            progress = (cur_count / max_count) * 100
            self.pbar.n = progress
            self.pbar.refresh()

            # Estimate downloaded MBs
            if self.total_size_mb:
                self.downloaded_mb = (cur_count / max_count) * self.total_size_mb
                remaining_mb = self.total_size_mb - self.downloaded_mb
                self.pbar.set_postfix({"Remaining MB": f"{remaining_mb:.2f}"})
        
        if message:
            self.pbar.set_description(f"Cloning: {message}")

    def __del__(self):
        self.pbar.close()

def clone_repo_with_progress():
    print(f"Starting clone of {repo_url} into {output_dir}")
    try:
        # Clone the repo with progress tracking
        progress = CloneProgress()
        Repo.clone_from(repo_url, output_dir, progress=progress)
        
        # After cloning, calculate actual size
        total_size_mb = sum(os.path.getsize(os.path.join(dirpath, filename)) 
                           for dirpath, _, filenames in os.walk(output_dir) 
                           for filename in filenames) / (1024 * 1024)
        print(f"\nClone completed! Total size: {total_size_mb:.2f} MB")
        
        # List downloaded folders
        folders = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
        print(f"Downloaded {len(folders)} folders: {folders}")
        
    except Exception as e:
        print(f"Error during cloning: {e}")

if __name__ == "__main__":
    # Install required packages if not already present: pip install gitpython tqdm
    clone_repo_with_progress()