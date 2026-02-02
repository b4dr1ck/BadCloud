#!/bin/bash

destination_dir="$1"
repo_dir="$2"

export PATH="/home/badrick/bin:$PATH"

rtcCheck() {
  rtc=$1
  if [ $rtc -ne 0 ]; then
    echo "Error: Command failed with return code $rtc"
    exit $rtc
  fi
}

# write log file
LOGFILE="install_$(date "+%Y%M%d_%H%M%S").log"
exec > >(tee -a "$LOGFILE") 2>&1


if [ -z "$destination_dir" ] || [ -z "$repo_dir" ]; then
  echo "Usage: $0 <destination_dir> <repo_dir>"
  exit 1
fi

if [ ! -d "$destination_dir" ]; then
  echo "Error: Destination directory '$destination_dir' does not exist."
  exit 2
fi

if [ ! -d "$repo_dir" ]; then
  echo "Error: Repository directory '$repo_dir' does not exist."
  exit 4
fi

echo "* Pull Repository"

cd $repo_dir || {
  echo "Error: Could not change directory to '$repo_dir'."
  exit 3
}

git pull origin main
rtcCheck $?

echo "* Install dependencies and build project"
npm install
rtcCheck $?
npm run build
rtcCheck $?
echo ""

echo "* Deploying build to '$destination_dir'..."
cd dist || {
  echo "Error: 'dist' directory does not exist after build."
  exit 5
}

rm -rv "${destination_dir}/assets/"
rtcCheck $?

cp -rv ./* "$destination_dir/"

cp ../src/fileRequest.py "${destination_dir}/fileRequest.py"
rtcCheck $?

