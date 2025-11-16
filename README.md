# mchp-pack-downloader
This is a simple Python script to download certain device packs from Microchip Technology's packs
repository at https://packs.download.microchip.com/. This script will currently download only device
packs for Microchip's 32-bit ARM devices. If you want this to download other Microchip packs, edit the
`keep_this_pack()` method in the `DevicePack` class to add the packs you want. This script also looks
for and download only the latest versions of packs. You therefore probably want to archive whatever
packs you download if you think you might need them again in the future.

This app is covered by the standard 3-clause BSD license, so you can modify this to download packs
for other Microchip devices or even devices from other vendors. See the LICENSE file in this directory
for the full license text.

## What are Device Packs?
Device packs are files that contain information about a vendor's microcontroller and microprocessor
devices. They also contain things like header files and linker scripts that can be used with that
vendor's development tools. From what I can tell, the idea of device packs came from ARM and their
CMSIS framework. Packs are particularly useful for vendors that use Arm's compiler suite instead of
distributing their own. A vendor needs only to update packs to fix bugs or add new devices instead of
needing to bundle up a whole new distribution of a toolchain.

Microchip uses device packs even though they distribute their own custom build of GCC under the "XC"
branding. This is probably because Atmel was already doing this when Microchip acquired them in 2016.

## Requirements
All you should need is Python 3.10 or newer to be installed.

## A Quick Word of Caution
This script accesses the external URL https://packs.download.microchip.com/ to download Microchip's
device packs. Doing so should be safe because that site belongs to Microchip Technology and because
this script does not execute anything. However, there is always a risk when accessing an external
resource, so keep that in mind. You can try going to that URL in your web browser to see if it still
works if you want to exercise a bit of extra caution.

## How to Run
Chances are you do not need to run this script by itself unless you are modifying it for your own
use. This script is really meant to be run by another script used to build a toolchain, such as
the `buildMchpClang.py` script you can find at https://github.com/jdeguire/buildMchpClang.

Simply run the script as `python3 ./mchp-pack-downloader.py`. If you are on Linux, you can use
`chmod +x ./mchp-pack-downloader.py` to make the script executable and then run it like a normal
program with `./mchp-pack-downloader.py`.

The script will automatically download pack files to a `dl/` directory that is created alongside the
script. Those packs are then extracted to a `packs/` directory that is also created alongside the
script.

## Trademarks
This project and the similarly-named ones make references to "PIC32", "SAM", "XC32", and "MPLAB"
products from Microchip Technology. Those names are trademarks or registered trademarks of Microchip
Technology.

These project also refer to "Arm", "ARM", "Cortex", and "CMSIS", which are all trademarks of Arm
Limited.

These projects are all independent efforts not affiliated with, endorsed, sponsored, or otherwise
approved by Microchip Technology, Arm Limited, or the LLVM Foundation.
