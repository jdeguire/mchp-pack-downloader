#! /usr/bin/env python3
#
# Copyright (c) 2025, Jesse DeGuire
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# #####
#
# mchp-pack-downloader.py
#
# This is a script to automate downloading device packs from Microchip's packs repository at
# https://packs.download.microchip.com/. For now, this script will download only packs for 32-bit ARM
# devices because this is meant to be used with the 'buildMchpClang.py' script. This will also look
# for and download only the latest versions of packs. If you are building a toolchain, then you
# should make an archive of your sources and packs so you can build those at any time in the future.
#
# You can modify what packs this script will look for by editing the 'keep_this_pack()' method in
# the DevicePack class below.
#

from html.parser import HTMLParser
from pathlib import Path
import os
import urllib.request

PACKS_REPO_URL = 'https://packs.download.microchip.com/'
PACKS_EXTENSION = '.atpack'

THIS_FILE_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
DOWNLOAD_DIR = THIS_FILE_DIR / 'dl'
PACKS_DIR = THIS_FILE_DIR / 'packs'


class DevicePack:
    '''Represents a single device pack that you would download from Microchip's pack repository.

    This is here mainly to help parse the names of the packs to extract the devices they apply to
    and to get their version. Pack names from Microchip have the following form:

        Manufacturer.DeviceFamily.X.Y.Z.atpack
    
    For example: "Microchip.SAML10_DFP.3.5.87.atpack"

    Notice that the DeviceFamily portion ends in "_DFP". Tool packs for things like debuggers will
    instead end in "_TP". ARM's CMSIS is also distributed in packs, so the manufacturer might be
    "ARM" instead of "Microchip".
    '''

    def __init__(self, path:str):
        '''Make a new DevicePack object with the given path.

        Use the filename that was retrieved from the packs repository URL, including the extension
        and any path compoents.
        '''
        self.path: str = path

        # Split the file name from the rest of the path at the last '/' if one was present. The
        # pack filename will be the last element of this array.
        name = path.rsplit('/', 1)[-1]

        # Now parse the name further to get other info.
        parts: list[str] = name.split('.')

        if len(parts) != 6:
            raise ValueError(f'Unexpected pack name format for pack {self.path}')
        
        self.manufacturer: str = parts[0]
        self.family: str = parts[1]
        self.version_str: str = f'{parts[2]}.{parts[3]}.{parts[4]}'

        # For now, let each version part have up to five digits.
        try:
            self.version: int = (10_000_000_000 * int(parts[2])  +
                                 100_000 * int(parts[3])  +
                                 int(parts[4]))
        except ValueError:
            raise ValueError(f'Unable to parse version from pack {self.path}')

        self.extension = parts[5]


    def keep_this_pack(self) -> bool:
        '''Return True if the name of this pack appears to be for a device series we want to support.

        This works as a whitelist in that it looks for packs that we know are for devices we can
        support. Update these checks if you want to add other devices, like the 8-bit AVR chips.
        '''
        # Check for Microchip parts.
        if self.get_manufacturer() != 'Microchip':
            return False


        family: str = self.get_family().lower()

        # Tool packs for things like debuggers and programmers. We do not want these.
        if family.endswith('_tp'):
            return False

        # Look for the most common ARM devices first.
        if family.startswith('sam')  or  family.startswith('pic32c'):
            return True

        # Some PIC32W wireless parts have ARM CPUs.
        if family.startswith('pic32w'):
            return True

        # These seem to be embedded controllers for things like keyboards. At least some of these
        # have ARM CPUs in them.
        if family.startswith('cec')  or  family.startswith('dec')  or  family.startswith('mec'):
            return True

        # LoRa modules with ARM CPUs.
        if family.startswith('wrl'):
            return True

        # Else assume it is a pack we do not want. Update the above checks if you want to add a new
        # device series.
        return False


    def get_path(self) -> str:
        '''Return the path that was passed to the constructor of this object.
        '''
        return self.path


    def get_manufacturer(self) -> str:
        '''Return the manufacturer provided in the pack name.
        '''
        return self.manufacturer


    def get_family(self) -> str:
        '''Return the device family provided in the pack name.
        '''
        return self.family


    def get_version(self) -> int:
        '''Return the pack version as parsed from the pack name.

        If the version in the pack name is "x.y.z", then this will return

            (x * 10_000_000_000) + (y * 100_000) + z.
        '''
        return self.version
    

    def get_version_string(self) -> str:
        '''Return the pack version as a string in X.Y.Z format.
        '''
        return self.version_str


    def get_extension(self) -> str:
        '''Return the extension of the pack filename.
        '''
        return self.extension


class PacksHtmlParser(HTMLParser):
    '''A super simple subclass of HTMLParser to look for download links for packs and put those into
    a list for later.

    This is based on the examples and docs for the 'html.parser' library found at
    https://docs.python.org/3/library/html.parser.html#module-html.parser. Have a look there to get
    a better idea of what this is doing. See the main code below to see how to use this class.
    '''

    def __init__(self):
        super().__init__()

        self.links: list[DevicePack] = []


    def get_pack_links(self):
        '''Return a list of links to file packs.

        The links are relative to the URL from which they were read. You need to feed the HTML data
        from the URL to this parser using the 'feed()' method first before this will return anything
        useful.
        '''
        return self.links


    def handle_starttag(self, tag, attrs):
        '''This is called by the HTMLParser superclass whenever a start tag is found.

        In our case, we want to look for download links for pack files, which end in '.atpack'.
        This will put links into a list that can be retrieved later from this instance.
        '''
        # The tags we're looking for look like this:
        #    <a href="Microchip.ATautomotive_DFP.3.1.73.atpack" download="">
        #
        # Look for the 'a' tag with the 'href' and 'download' attributes.
        #
        if 'a' == tag:
            href: str = ''
            download: bool = False

            for attr in attrs:
                if 'download' == attr[0]:
                    download = True
                elif 'href' == attr[0]  and  attr[1]  and  attr[1].endswith(PACKS_EXTENSION):
                    href = attr[1]

            if download:
                # We found a valid pack download link, so hold onto it if it's a pack we care about.
                pack = DevicePack(href)

                if pack.keep_this_pack():
                    self.links.append(pack)


if '__main__' == __name__:
    pack_links: list[DevicePack] = []

    with urllib.request.urlopen(PACKS_REPO_URL, data=None, timeout=10.0) as req:
        # Grab the HTML from the packs URL.
        html_data: str = req.read().decode('utf-8')

        # Create our custom HTML parser and pass the HTML to that.
        parser = PacksHtmlParser()
        parser.feed(html_data)
        parser.close()

        # Now that the parser has parsed the HTML, we can see what links to packs it has found.
        pack_links = parser.get_pack_links()
    

    # Now that we have our links, search for and keep only the latest versions of packs.
    latest_packs: dict[str, DevicePack] = {}
    for pack in pack_links:
        family = pack.get_family()

        if family in latest_packs:
            if pack.get_version() > latest_packs[family].get_version():
                latest_packs[family] = pack
        else:
            latest_packs[family] = pack
    
    for family, pack in latest_packs.items():
        print(f'Latest version of pack {family} is {pack.get_version_string()}')
